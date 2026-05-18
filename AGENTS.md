# yd-skills

Duo skills for symmetric Claude+Codex convergence. Installed as a plugin into Claude Code and Codex CLI from the same git repo.

Plugin name: `yd`. Marketplace name: `yd`.

## Skills shipped

- `duo-design` - architecture / system design convergence; output `Duo/Design-<slug>/Result.md`.
- `duo-discuss` - open-ended convergence (decisions, tradeoffs, planning, post-mortems); output `Duo/Discussion-<slug>/Result.md`.
- `duo-forge` - meta-skill; uses the duo protocol to design a new `duo-<name>` skill, writes `~/.claude/skills/duo-<name>/SKILL.md` on CREATE.
- `duo-prod-ready` - production-readiness refactoring; WRITES CODE; modifies tree, runs build+test, commits per cycle.
- `duo-research` - research deliverable convergence with central web access; output `Duo/Research-<slug>/Result.md`.
- `duo-review` - branch / PR / diff code-review convergence; read-only; output `Duo/Review-<slug>/Result.md`.

All trigger only on the explicit `duo` keyword.

## Runtime requirements

- `codex` on PATH (the OpenAI Codex CLI binary) for every duo skill - it dispatches a second codex agent in the background.
- Codex is pinned to model `gpt-5.5`, reasoning level `xhigh`, live web search on, yolo / `--dangerously-bypass-approvals-and-sandbox`.
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
  AGENTS.md              # this file (Codex repo context)
  CLAUDE.md              # Claude Code repo context
  LICENSE
  README.md
```
