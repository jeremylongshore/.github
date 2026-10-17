"""Exercise the reusable workflow's actual shell steps with disposable SSH keys."""

import os
from pathlib import Path
import pwd
import shlex
import shutil
import socket
import subprocess
import tempfile
import textwrap
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/vps-deploy.yml"
REVISION = "a" * 40


def step_script(name):
    lines = WORKFLOW.read_text().splitlines()
    start = lines.index("      - name: " + name)
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("      - ")), len(lines))
    start = lines.index("        run: |", start, end) + 1
    return textwrap.dedent("\n".join(lines[start:end])) + "\n"


class DeploySSHTests(unittest.TestCase):
    def setUp(self):
        # sshd StrictModes rejects authorized_keys under world-writable /tmp.
        self.tmp = tempfile.TemporaryDirectory(prefix=".deploy-ssh-test-", dir=Path.home())
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("server", "client", "wrong"):
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "",
                            "-f", str(self.root / name)], check=True)
        self.host = "deploy-test.invalid"
        self.pin = self.host + " " + (self.root / "server.pub").read_text()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for command in ("ssh-keyscan", "getent"):
            script = self.bin / command
            script.write_text("#!/bin/sh\necho DNS-dependent-command-called >&2\nexit 91\n")
            script.chmod(0o700)
        self.env = dict(os.environ, RUNNER_TEMP=str(self.root),
                        GITHUB_OUTPUT=str(self.root / "outputs"),
                        VPS_HOST=self.host, VPS_TAILNET_IP="127.0.0.1",
                        VPS_DEPLOY_KEY=(self.root / "client").read_text(),
                        VPS_USER=pwd.getpwuid(os.getuid()).pw_name,
                        DEPLOY_REVISION=REVISION,
                        PATH=str(self.bin) + os.pathsep + os.environ["PATH"])

    def configure(self, pin=None):
        self.env["VPS_HOST_KEY"] = self.pin if pin is None else pin
        script = step_script("Configure SSH")
        # Secrets must enter through env, never interpolation into shell code.
        self.assertNotIn("${{", script)
        self.assertNotIn("~/.ssh", script)
        result = subprocess.run(["bash", "-euo", "pipefail", "-c", script],
                                env=self.env, text=True, capture_output=True)
        outputs = self.root / "outputs"
        if result.returncode == 0:
            self.outputs = dict(line.split("=", 1) for line in outputs.read_text().splitlines())
        return result

    def test_hostname_pin_without_dns_or_keyscan(self):
        result = self.configure()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.outputs["host-key-alias"], self.host)
        known = Path(self.outputs["known-hosts-file"])
        self.assertEqual(known.read_text().strip(), self.pin.strip())
        self.assertEqual(known.stat().st_mode & 0o777, 0o600)
        self.assertEqual(Path(self.outputs["identity-file"]).stat().st_mode & 0o777, 0o600)
        self.assertNotIn("PRIVATE KEY", result.stdout + result.stderr)

    def test_hashed_hostname_pin(self):
        known = self.root / "hashed-hosts"
        known.write_text(self.pin)
        subprocess.run(["ssh-keygen", "-q", "-H", "-f", str(known)],
                       check=True, capture_output=True)
        result = self.configure(known.read_text())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.outputs["host-key-alias"], self.host)

    def test_ip_only_pin(self):
        result = self.configure(self.pin.replace(self.host, "127.0.0.1"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.outputs["host-key-alias"], "127.0.0.1")

    def test_missing_or_unrelated_pin_fails_before_identity_is_written(self):
        for pin in ("", self.pin.replace(self.host, "unrelated.invalid")):
            with self.subTest(pin=bool(pin)):
                result = self.configure(pin)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "vps-deploy-ssh/id_ed25519").exists())
                self.assertNotIn("PRIVATE KEY", result.stdout + result.stderr)

    def start_server(self, force_command="/bin/echo integration-reached"):
        server = shutil.which("sshd") or "/usr/sbin/sshd"
        self.assertTrue(Path(server).exists(), "openssh-server is required for transport tests")
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        config = self.root / "sshd_config"
        config.write_text(textwrap.dedent(f"""\
            ListenAddress 127.0.0.1
            Port {port}
            HostKey {self.root / 'server'}
            PidFile {self.root / 'sshd.pid'}
            AuthorizedKeysFile {self.root / 'client.pub'}
            PasswordAuthentication no
            KbdInteractiveAuthentication no
            UsePAM no
            StrictModes yes
            ForceCommand {force_command}
            LogLevel VERBOSE
        """))
        log = (self.root / "sshd.log").open("w")
        self.addCleanup(log.close)
        proc = subprocess.Popen([server, "-D", "-e", "-f", str(config)],
                                stdout=log, stderr=log)
        def stop():
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=5)
        self.addCleanup(stop)
        for _ in range(100):
            self.assertIsNone(proc.poll(), (self.root / "sshd.log").read_text())
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=.1):
                    break
            except OSError:
                time.sleep(.02)
        else:
            self.fail("disposable sshd did not start")
        # Add only the disposable port and disable machine-specific client config.
        # All trust, destination and identity options remain from the workflow.
        wrapper = self.bin / "ssh"
        wrapper.write_text("#!/bin/sh\nexec /usr/bin/ssh -F /dev/null -p "
                           + shlex.quote(str(port)) + ' "$@"\n')
        wrapper.chmod(0o700)

    def deploy(self, send_revision="true"):
        self.env.update(SEND_REVISION=send_revision,
                        SSH_IDENTITY_FILE=self.outputs["identity-file"],
                        SSH_KNOWN_HOSTS_FILE=self.outputs["known-hosts-file"],
                        SSH_HOST_KEY_ALIAS=self.outputs["host-key-alias"])
        script = step_script("Trigger VPS deploy (command-restricted SSH over tailnet)")
        self.assertNotIn("${{", script)
        return subprocess.run(["bash", "-euo", "pipefail", "-c", script],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def test_real_ssh_uses_ip_when_hostname_cannot_resolve(self):
        self.start_server()
        result = self.configure()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.deploy()
        self.assertEqual(result.returncode, 0,
                         result.stderr + (self.root / "sshd.log").read_text())
        self.assertEqual(result.stdout.strip(), "integration-reached")

    def report_original_command(self):
        script = self.root / "report-command"
        script.write_text('#!/bin/sh\necho "cmd=[$SSH_ORIGINAL_COMMAND]"\n')
        script.chmod(0o755)
        self.start_server(force_command=str(script))
        result = self.configure()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_revision_reaches_the_forced_command_by_default(self):
        self.report_original_command()
        result = self.deploy()
        self.assertEqual(result.returncode, 0,
                         result.stderr + (self.root / "sshd.log").read_text())
        self.assertEqual(result.stdout.strip(), f"cmd=[{REVISION}]")

    def test_send_revision_false_sends_an_empty_command(self):
        # braves-booth's forced command refuses anything but an empty command (exit 64).
        self.report_original_command()
        result = self.deploy(send_revision="false")
        self.assertEqual(result.returncode, 0,
                         result.stderr + (self.root / "sshd.log").read_text())
        self.assertEqual(result.stdout.strip(), "cmd=[]")

    def test_real_ssh_rejects_wrong_pinned_key(self):
        self.start_server()
        result = self.configure(self.host + " " + (self.root / "wrong.pub").read_text())
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("integration-reached", result.stdout)
        self.assertIn("Host key verification failed", result.stderr)


def step_lines(name):
    lines = WORKFLOW.read_text().splitlines()
    start = lines.index("      - name: " + name)
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("      - ")), len(lines))
    return lines[start:end]


class RunnerModeTests(unittest.TestCase):
    """join-tailnet: false runs on a host already on the tailnet and mints nothing."""

    REACH = "Check the VPS is reachable from this runner"

    def reach(self, port, attempts="2"):
        script = step_script(self.REACH)
        self.assertNotIn("${{", script)
        env = dict(os.environ, VPS_TAILNET_IP="127.0.0.1",
                   VPS_SSH_PORT=str(port), REACH_ATTEMPTS=attempts)
        return subprocess.run(["bash", "-euo", "pipefail", "-c", script],
                              env=env, capture_output=True, text=True, timeout=30)

    def test_reachable_port_passes_on_first_attempt(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            result = self.reach(listener.getsockname()[1])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reachable after 1 attempt(s)", result.stdout)

    def test_closed_port_fails_after_bounded_attempts(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        result = self.reach(port, attempts="3")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("not reachable"), 4)  # 3 attempts + the error
        self.assertIn("already on the tailnet", result.stdout)

    def test_tailscale_steps_run_only_when_joining(self):
        for name in ("Connect Tailscale (OIDC / Workload Identity Federation)",
                     "Wait for tailnet peer to be routable"):
            with self.subTest(step=name):
                self.assertIn("        if: ${{ inputs.join-tailnet }}", step_lines(name))
        self.assertIn("        if: ${{ !inputs.join-tailnet }}", step_lines(self.REACH))

    def test_runner_and_secrets_follow_the_mode(self):
        text = WORKFLOW.read_text()
        self.assertIn("    runs-on: ${{ fromJSON(inputs.runs-on) }}", text)
        self.assertIn("        default: '\"ubuntu-latest\"'", text)
        secrets = text.split("    secrets:", 1)[1].split("\njobs:", 1)[0]
        for name in ("TS_OIDC_CLIENT_ID", "TS_AUDIENCE"):
            block = secrets.split(name + ":", 1)[1].split("\n      ", 3)
            self.assertIn("required: false", "\n".join(block[:3]), name)
        for name in ("VPS_DEPLOY_KEY", "VPS_HOST_KEY"):
            block = secrets.split(name + ":", 1)[1].split("\n      ", 3)
            self.assertIn("required: true", "\n".join(block[:3]), name)


if __name__ == "__main__":
    unittest.main()
