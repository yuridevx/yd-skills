# yd-skills

Dual-target plugin repo. Same content installed as a Claude Code plugin and a Codex plugin. See [AGENTS.md](AGENTS.md) for the full skill catalog, runtime requirements, and layout - this file mirrors that document for harnesses that look for `CLAUDE.md`.

Plugin name: `yd`. Marketplace name: `yd`.

## Skills shipped

Duo skills (all trigger only on explicit `duo` keyword; each dispatches a second `codex` agent in the background and converges on `Duo/<MissionKind>-<slug>/Result.md`):

- `duo-design`, `duo-discuss`, `duo-forge`, `duo-prod-ready`, `duo-research`, `duo-review`, `duo-testplan-build`, `duo-testplan-converge`.

`duo-testplan-converge` is the per-unit duo author + step-by-step diff convergence variant of `duo-testplan-build` (6 phases vs 8; first-AGREED-pair per-field convergence vs union-merge + N-pass refinement; ~3-5x lower dispatch ceiling). Both ship in this plugin and coexist; users pick by workload character.

Rulebook skill (passive; loaded by orchestrator or by explicit reference, NOT triggered on `duo`):

- `linked-testplan` - rulebook for the e2e test plan page shape, coverage vocabulary, and 21-rule refinement checklist used by `duo-testplan-build` and `duo-testplan-converge`.

## Runtime requirements

- `codex` binary on PATH.
- Git working tree at the convergence target repo.

## Installation

See [README.md](README.md) for `claude plugin marketplace add` and `codex plugin marketplace add` invocations.
