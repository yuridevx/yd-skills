# yd-skills

Duo skills for symmetric Claude+Codex convergence. Installed as a plugin into Claude Code and Codex CLI from the same git repo.

Plugin name: `yd`. Marketplace name: `yd`.

## Skills shipped

Duo skills (all trigger only on explicit `duo` keyword):

- `duo-design` - architecture / system design convergence; output `Duo/Design-<slug>/Result.md`.
- `duo-discuss` - open-ended convergence (decisions, tradeoffs, planning, post-mortems); output `Duo/Discussion-<slug>/Result.md`.
- `duo-forge` - meta-skill; uses the duo protocol to design a new `duo-<name>` skill, writes `~/.claude/skills/duo-<name>/SKILL.md` on CREATE.
- `duo-prod-ready` - production-readiness refactoring; WRITES CODE; modifies tree, runs build+test, commits per cycle.
- `duo-research` - research deliverable convergence with central web access; output `Duo/Research-<slug>/Result.md`.
- `duo-review` - branch / PR / diff code-review convergence; read-only; output `Duo/Review-<slug>/Result.md`.
- `duo-testplan-build` - symmetric Claude+Codex authoring of an e2e test plan tree for multi-repo workspaces; 8-phase pipeline with per-service / per-flow streaming, union-merge convergence + N-parallel-pass refinement; outputs `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow>.md` and `test-plan/cross-app/flows/<flow>.md`.
- `duo-testplan-converge` - symmetric Claude+Codex authoring of an e2e test plan tree for multi-repo workspaces; 6-phase pipeline with per-unit duo author + step-by-step structured diff convergence (first-AGREED-pair per field); each unit owned by a per-unit Claude subagent that resumes a single codex session across rounds; consumes the linked-testplan rulebook AS IS; same output tree as duo-testplan-build but ~3-5x lower dispatch ceiling.

Rulebook skill (passive; loaded by orchestrator or by explicit reference, NOT triggered on `duo`):

- `linked-testplan` - rulebook for the e2e test plan page shape, coverage vocabulary, scenario policy, mocks policy, and 21-rule refinement checklist. Loaded by `duo-testplan-build` and `duo-testplan-converge` orchestrator-dispatched agents. Standalone activation only on explicit `apply linked-testplan rules to X` prose.

## Runtime requirements

- `codex` on PATH (the OpenAI Codex CLI binary) for every duo skill - it dispatches a second codex agent in the background.
- Codex is pinned to model `gpt-5.5`, reasoning level `xhigh`, yolo / `--dangerously-bypass-approvals-and-sandbox`. Web search is `live` for most skills; `duo-testplan-build` and `duo-testplan-converge` default web search OFF (source code is the only ground truth) — flip to `live` with the `web-allowed` prose modifier when external contract specs are needed.
- Git working tree at the repo where the convergence runs (skills write to `Duo/` under the current repo).

## Repo layout

```
yd-skills/
  .claude-plugin/
    plugin.json          # Claude Code plugin manifest
    marketplace.json     # Claude Code marketplace
  .codex-plugin/
    plugin.json          # Codex plugin manifest
  .agents/
    plugins/
      marketplace.json   # Codex marketplace (canonical path)
  skills/
    duo-design/SKILL.md
    duo-discuss/SKILL.md
    duo-forge/SKILL.md
    duo-prod-ready/SKILL.md
    duo-prod-ready/references/categories.md
    duo-research/SKILL.md
    duo-review/SKILL.md
    duo-testplan-build/SKILL.md
    duo-testplan-converge/SKILL.md
    linked-testplan/SKILL.md
    linked-testplan/references/page-shape.md
    linked-testplan/references/checklist-21.md
    linked-testplan/references/coverage-vocab.md
  scripts/
    check-refs.py        # used by duo-testplan-build refinement pipeline and duo-testplan-converge P5
  AGENTS.md              # this file (Codex repo context)
  CLAUDE.md              # Claude Code repo context
  LICENSE
  README.md
```
