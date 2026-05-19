# yd-skills

Dual-target plugin repo. Same content installed as a Claude Code plugin and a Codex plugin. See [AGENTS.md](AGENTS.md) for the full skill catalog, runtime requirements, and layout - this file mirrors that document for harnesses that look for `CLAUDE.md`.

Plugin name: `yd`. Marketplace name: `yd`.

## Skills shipped

Duo skills (all trigger only on explicit `duo` keyword; each dispatches a second `codex` agent in the background and converges on `Duo/<MissionKind>-<slug>/Result.md`):

- `duo-design`, `duo-discuss`, `duo-forge`, `duo-prod-ready`, `duo-research`, `duo-review`, `duo-testplan`.

`duo-testplan` is the per-unit duo author + step-by-step structured diff convergence skill for e2e test plan trees (6 phases; first-AGREED-pair per-field convergence; per-unit Claude subagent owns the convergence cycle and resumes a single codex session within the unit).

Solo skill (Claude-only; triggers only on explicit `solo` keyword; writes `Solo/TestPlan-<slug>/`):

- `solo-testplan` - Claude-only counterpart to `duo-testplan`, same artifact shape, no codex. Five named phases (service-scope, local-flows, cross-app-survey, cross-app-flows, result). Each unit decomposes into a chain of independent fresh-context subagent dispatches: one Author round plus N Refinement rounds, each reading every prior `Author-r*.md` and `Refine-r*.md` in the unit subfolder. Refinement is substance-only — editorial edits forbidden. Default round cap R0 + 1; `deep-refinement` → R0 + 3; `extended-refinement` removes the cap. Streaming handoffs replace barriers everywhere except `result`.

Rulebook skill (passive; loaded by orchestrator or by explicit reference, NOT triggered on `duo` or `solo`):

- `linked-testplan` - rulebook for the e2e test plan page shape, coverage vocabulary, and 21-rule refinement checklist used by `duo-testplan` and `solo-testplan`.

## Runtime requirements

- `codex` binary on PATH (every duo skill dispatches a second codex agent). `solo-testplan` does NOT need `codex` — it is Claude-only.
- Git working tree at the convergence target repo.

## Installation

See [README.md](README.md) for `claude plugin marketplace add` and `codex plugin marketplace add` invocations.
