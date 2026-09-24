# Contributing

Thanks for working on an Intent Solutions repository. This guide is the **default way we work every
repo** — it applies org-wide unless a specific repo overrides it with its own `CONTRIBUTING.md`.
It's short on purpose, and every rule comes with its *why*, because the goal is that you internalize
the reasoning and apply it well in situations this guide never anticipated.

> **The one principle:** you are always building the **record**, not just the change. A commit and a
> pull request are read months later by a human — or an AI agent — with zero memory of the work.
> Here the record is part of the product, so it's held to the same bar as the code.

## Quick start

1. **Read the repo's own `README.md` and `CLAUDE.md`/`AGENTS.md` first** (if present). Each repo has
   its own build/test commands and conventions — never assume one repo's patterns apply to another.
2. **Branch from `main`** (`git fetch` first; `main` often moves under you). **Never commit to `main`
   directly.**
3. Make your change; run the repo's **tests, type-check, and lint** locally *before* you commit.
4. **Push — that opens your pull request.** CI and the review bot pick it up from there.
5. Address review + CI, then a **maintainer merges** (see *Reviews & merging*).

## Branches

`<type>/<short-kebab-topic>` — e.g. `feat/streaming-parser`, `fix/null-token-crash`,
`docs/contributing-guide`.

- Types: `feat` · `fix` · `refactor` · `perf` · `docs` · `test` · `chore` · `build` · `ci`.
- **Why a branch every time:** `main` stays always-green and deployable, and every change stays
  isolated, reviewable, atomic, and revertible. It prevents a half-done change landing on the trunk
  everyone else branches from.

## Commits

```text
type(scope): imperative subject, ≤ ~72 chars, no trailing period

WHAT changed — the mechanism, in plain terms.
WHY — the problem it solves. When a real alternative existed, add one line:
"chose X over Y because Z" (the part a diff can't show you).
HOW verified — the tests/evidence: counts, commands, what you observed.

Refs/Closes the issue.
```

- No bare `fix` / `update` subjects — say *what* specifically (`fix: reject expired tokens at auth`,
  not `fix: bug`).
- **Why the full body:** the commit is the durable record. *"Chose X over Y because Z"* preserves the
  fork in the road so the next person doesn't re-litigate a settled decision or lose the intent.

## Pull requests

A PR is a **decision packet**, not a diff dump. Use the repo's PR template. Two lanes:

- **Full lane** (any code / config / CI / schema / dependency / runtime change): *What · Why &
  decision rationale · How it works · Verification & evidence (link the proof — a CI run, test
  output, a screenshot) · Risk assessment · Operational impact · Follow-up & deferred · Refs/Closes.*
- **Lightweight lane** (docs/typo/formatting only): *What · Why (one line) · Refs.*

### The Outsider Test (the pre-merge bar)

Before a PR merges, someone must be able to answer these seven questions using **only the PR
description** — not the diff, not memory of the work:

1. What changed? 2. Why was it necessary? 3. Which component changed? 4. How was it verified?
5. How do I roll it back? 6. What are the risks? 7. What remains unfinished?

**If a stranger can't answer all seven from the PR alone, it isn't ready** — the code might be, but
the record isn't. "Verified" is a claim; *link the artifact that proves it.*

## Reviews & merging

- **CI is the deterministic gate — that's what we merge on.** Lint, type-check, tests, and any
  security/quality checks must be green. A coverage drop is fixed by adding tests, never by lowering
  the threshold. Don't bypass a required check; if a check is wrong, fix the check.
- **The AI reviewer is advisory.** Read whichever review bot comments on your PR and address or
  resolve it — it adds judgment, but it can be wrong or absent, so it never blocks on its own.
- **Maintainers merge.** Contributors push branches and open PRs; a maintainer with merge authority
  lands them after review. This lets everyone move fast while one accountable owner holds quality and
  lets CI and the reviewer actually run. If your PR sits, that's the gate working — ping politely.
- Be patient and specific: each follow-up push should answer a **specific** review comment or CI
  failure, never a speculative "made more changes."

## Working with AI agents

Much of our work is done with AI coding agents, and this guide is written for them too.

- **Point your agent at this file** (and the repo's `CLAUDE.md`/`AGENTS.md`) at the start of a
  session, so it works the same way you do.
- Keep `CLAUDE.md` and `AGENTS.md` **in lockstep** — if you change one, change the other in the same
  PR, so agents from different tools follow identical instructions.
- The same standards apply to agent-authored changes: feature branch, strong commit + PR, tests
  green, the Outsider Test. An agent that can't meet the bar isn't done.

## Tests

Every change ships with the evidence that it works. Add or update tests alongside the code; run the
repo's suite before you push; link the result in your PR. If you're adding a capability, add the test
that proves it; if you're fixing a bug, add the test that reproduces it.

## Docs

If your change affects behavior, update the docs in the same PR — a change and its documentation
drift apart the moment they land in separate commits. Keep dated records (plans, audits, decisions)
in the repo's docs directory with its filing convention where one exists.

## Learn how we build

- **How we build with AI** — a chaptered walk-through of our workflow:
  <https://demos.intentsolutions.io/how-we-build/>
- **Intent Solutions** — <https://intentsolutions.io>

## Conduct & license

Be respectful and constructive; assume good faith. By contributing, you agree your contributions are
licensed under the repository's `LICENSE`. See `CODE_OF_CONDUCT.md` and `SECURITY.md` where present.
