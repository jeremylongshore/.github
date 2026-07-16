# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## What this repo is

`jeremylongshore/.github` — the org-level shared GitHub repo. Two responsibilities:

1. **Org profile README** at `profile/README.md` — shown on GitHub at `https://github.com/jeremylongshore`.
2. **Reusable workflows** at `.github/workflows/*.yml` — canonical templates that other jeremylongshore/* repos call via `uses:`.

## Reusable workflows

| Workflow | Purpose | Callers |
|---|---|---|
| [`vps-deploy.yml`](.github/workflows/vps-deploy.yml) | Canonical Tailscale-OIDC + SSH-over-tailnet deploy to the Contabo VPS at `intentsolutions` (167.86.106.29). Includes hard-fail smoke check. | `braves-booth` (current); rolling out to all P7 GCP-exodus repos. |

### Calling convention

Caller workflows MUST:
1. Declare `permissions: id-token: write` at the workflow or job level (Tailscale OIDC needs the GitHub-issued JWT).
2. Run a `test` job before the deploy job, with `needs: test` on the deploy job. The reusable workflow does not enforce this — it's a contract the caller honors.
3. **Pin the reusable workflow by 40-char SHA**, never `@v1` or `@main`. Current deployment authority is [`intent-os/ops/deploy`](https://github.com/intent-solutions-io/intent-os/tree/main/ops/deploy).
4. Use `secrets: inherit` (or list each TS_*/VPS_* secret explicitly) so the reusable workflow can read repo secrets.

Full calling pattern is documented in the workflow file's header comment.

## Cross-references

- Deployment authority: `~/000-projects/intent-os/ops/deploy/`
- Pilot caller (braves-booth): `https://github.com/jeremylongshore/braves-booth/blob/main/.github/workflows/deploy.yml`
- Bead: `OPS-g6a` (P5 reusable workflow + braves refactor)
- Tailscale OIDC trust and secret references: `~/000-projects/intent-os/ops/host/` (values never enter docs)

## Bead workflow

This repo doesn't have its own beads — it's tracked at the home-level cross-cutting `~/.beads/` under `OPS` prefix. Currently `OPS-g6a` covers all changes here.

## Doc filing

Numbered docs go in `000-docs/` per `~/002-command-bible/DOCUMENT-FILING-STANDARD-v3.0.md`.
