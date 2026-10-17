# VPS SSH transport tests

Run `python3 -m unittest discover -s tests -v` with Python 3 and OpenSSH client
and server installed. CI also runs these tests before actionlint.

The tests extract and execute the SSH steps from the reusable workflow. They
generate disposable keys, reject DNS/keyscan calls, and run an SSH server bound
only to loopback on a temporary port. Correct pins permit the test command;
wrong pins reject it. No VPS, deployment key, or network beyond loopback is used.
Temporary files live under the current user's home so the test server can keep
OpenSSH's `StrictModes` checks enabled; cleanup stops the server and removes them.

The runner-mode tests cover `join-tailnet: false`: the reachability step passes
against a loopback listener, fails after its bounded attempts on a closed port,
and the Tailscale steps are gated on `join-tailnet`.
