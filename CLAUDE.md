# yd-skills

Dual-target plugin repo. Same content installed as a Claude Code plugin and a Codex plugin. See [AGENTS.md](AGENTS.md) for the full skill catalog, runtime requirements, and layout - this file mirrors that document for harnesses that look for `CLAUDE.md`.

Plugin name: `yd`. Marketplace name: `yd`.

## Skills shipped

Duo skills (all trigger only on explicit `duo` keyword; each dispatches a second `codex` agent in the background and converges on `Duo/<MissionKind>-<slug>/Result.md`):

- `duo-design`, `duo-discuss`, `duo-forge`, `duo-prod-ready`, `duo-research`, `duo-review`, `duo-testplan`.

`duo-testplan` is the per-unit duo author + step-by-step structured diff convergence skill for e2e test plan trees (6 phases; first-AGREED-pair per-field convergence; per-unit Claude subagent owns the convergence cycle and resumes a single codex session within the unit).

Solo skills (Claude-only; trigger only on explicit `solo` keyword; write under `Solo/`):

- `solo-testplan` - Claude-only counterpart to `duo-testplan`, same artifact shape, no codex. Five named phases (service-scope, local-flows, cross-app-survey, cross-app-flows, result). Each unit decomposes into a chain of independent fresh-context subagent dispatches: one Author round plus N Refinement rounds, each reading every prior `Author-r*.md` and `Refine-r*.md` in the unit subfolder. Refinement is substance-only — editorial edits forbidden. Default round cap R0 + 1; `extended-refinement` removes the cap. Streaming handoffs replace barriers everywhere except `result`. Outputs `Solo/TestPlan-<slug>/`.

- `solo-runtestplan` - Claude-only executor for e2e test plan trees (the artifact shape produced by `solo-testplan` / `duo-testplan`). Aggregates one or more test plan trees, generates a no-external-ports docker-compose stack + runner Dockerfile, brings the stack up, and runs every HAPPY/NEGATIVE scenario via CLI tools inside a single runner container on an internal network. Four phases (plan-aggregate, compose-build, flow-execute, result). Append-only `Bugs.md` (failures with full repro) and `Log.md` (chronological event ledger) maintained in-stream by per-flow subagents and main; thin `Result.md` at end. No INCONCLUSIVE state — observation gaps drive autonomous recovery (subagent self-installs tools / restarts deps; main re-dispatches compose-build for structural fixes) until every scenario reaches PASS / FAIL / SKIPPED or `recovery-budget` (default 5) is exhausted (which itself files an `observation-exhausted` bug). Strict sequential per-flow execution; scrub-between-every-attempt derived from external-dep tags. Outputs `Solo/RunTestPlan-<slug>/`.

Rulebook skill (passive; loaded by orchestrator or by explicit reference, NOT triggered on `duo` or `solo`):

- `linked-testplan` - rulebook for the e2e test plan page shape, coverage vocabulary, and 21-rule refinement checklist used by `duo-testplan`, `solo-testplan`, and `solo-runtestplan` (the executor reads the same page shape to translate scenarios into CLI commands).

## Runtime requirements

- `codex` binary on PATH (every duo skill dispatches a second codex agent). `solo-testplan` and `solo-runtestplan` do NOT need `codex` — both are Claude-only.
- `solo-runtestplan` additionally requires `docker` and `docker compose` v2 on PATH; the test stack runs inside docker on an internal network with no external ports.
- Git working tree at the convergence target repo.

## Installation

See [README.md](README.md) for `claude plugin marketplace add` and `codex plugin marketplace add` invocations.
