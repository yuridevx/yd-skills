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
- `duo-testplan` - symmetric Claude+Codex authoring of an e2e test plan tree for multi-repo workspaces; 6-phase pipeline (P1a scope file discovery, P1b per-service scope, P2 local flow refinement, P3 cross-app discovery, P4 cross-app flow refinement, P5 result + check-refs.py) with per-unit duo author + step-by-step structured diff convergence (first-AGREED-pair per field); each unit owned by a per-unit Claude subagent that resumes a single codex session across rounds; consumes the linked-testplan rulebook AS IS; outputs `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow>.md` and `test-plan/cross-app/flows/<flow>.md`.

Solo skill (Claude-only counterpart to `duo-testplan`; triggers only on explicit `solo` keyword, not `duo`):

- `solo-testplan` - Claude-only authoring of the same e2e test plan tree as `duo-testplan`; no codex peer. Five named phases (service-scope, local-flows, cross-app-survey, cross-app-flows, result). Each unit lives in its own subfolder under `.solo/<phase>/<unit-key>/` and runs as a chain of independent fresh-context subagent dispatches - one Author round followed by Refinement rounds. Each refinement reads every prior `Author-r*.md` and `Refine-r*.md` and emits substance-only field diffs; editorial edits (reword, polish, reorder, hedge, layout) are forbidden. Refinement terminates at first `substantial_diff_count: 0` round (CLEAN) or at round cap (CAPPED with `[unresolved:]` tags). Default round cap R0 + 1; `extended-refinement` removes the cap. Mechanical work - repo/service enumeration and cross-app producer/consumer reconciliation - lives in the main session. Streaming handoff: `local-flows` for a service spawn the moment its `service-scope` commits; `cross-app-flows` for a cflow spawn the moment both `local-flows` sides commit. Only one hard barrier (all flow units terminal -> result). The unit's converged artifact is the max-N `Author-r<N>.md` in its subfolder; main copies that file directly into the final `test-plan/` tree. No prompt files and no `Committed.md` indirection are written - main and subagents share the same Claude harness, so prompts go via the Agent tool parameter and convergence is identified by the highest-numbered Author file. Outputs `Solo/TestPlan-<slug>/Result.md` plus the same `test-plan/<repo>/<svc>/flows/<flow>.md` and `test-plan/cross-app/flows/<flow>.md` tree as duo. Consumes the linked-testplan rulebook AS IS. Triggers only on `solo testplan X`, `solo-testplan X`, `/solo-testplan X`, or `solo build a test plan for X`.

Rulebook skill (passive; loaded by orchestrator or by explicit reference, NOT triggered on `duo` or `solo`):

- `linked-testplan` - rulebook for the e2e test plan page shape, coverage vocabulary, scenario policy, mocks policy, and 21-rule refinement checklist. Loaded by `duo-testplan` orchestrator-dispatched agents. Standalone activation only on explicit `apply linked-testplan rules to X` prose.

## Runtime requirements

- `codex` on PATH (the OpenAI Codex CLI binary) for every duo skill - it dispatches a second codex agent in the background. `solo-testplan` does NOT require `codex` — it is Claude-only.
- Codex is pinned to model `gpt-5.5`, reasoning level `xhigh`, yolo / `--dangerously-bypass-approvals-and-sandbox`. Web search is `live` for most skills; `duo-testplan` and `solo-testplan` default web search OFF (source code is the only ground truth) — flip to `live` with the `web-allowed` prose modifier when external contract specs are needed.
- Git working tree at the repo where the convergence runs (duo skills write to `Duo/` under the current repo; `solo-testplan` writes to `Solo/`).

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
    duo-testplan/SKILL.md
    solo-testplan/SKILL.md
    linked-testplan/SKILL.md
    linked-testplan/references/page-shape.md
    linked-testplan/references/checklist-21.md
    linked-testplan/references/coverage-vocab.md
  scripts/
    check-refs.py        # used by duo-testplan at P5
  AGENTS.md              # this file (Codex repo context)
  CLAUDE.md              # Claude Code repo context
  LICENSE
  README.md
```
