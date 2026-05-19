# yd-skills

Dual-target plugin: ships the same skill set to Claude Code and Codex CLI from one repository.

## What you get

Eight duo skills for symmetric Claude+Codex convergence (each dispatches a parallel `codex` agent and writes a converged artifact under `Duo/<MissionKind>-<slug>/Result.md`) plus one passive rulebook skill.

| Skill | Kind | Output | Writes code? |
|---|---|---|---|
| `duo-design` | duo | `Duo/Design-<slug>/Result.md` | no |
| `duo-discuss` | duo | `Duo/Discussion-<slug>/Result.md` | no |
| `duo-forge` | duo | `Duo/Forge-<slug>/Result.md` + `~/.claude/skills/duo-<name>/SKILL.md` | no (writes the new skill file) |
| `duo-prod-ready` | duo | per-cycle commits on the working branch | YES |
| `duo-research` | duo | `Duo/Research-<slug>/Result.md` | no |
| `duo-review` | duo | `Duo/Review-<slug>/Result.md` | no |
| `duo-testplan-build` | duo | `Duo/TestPlan-<slug>/Result.md` + `test-plan/<repo>/<svc>/flows/<flow>.md` tree (8-phase union-merge + N-pass refinement) | no (writes test plan markdown only) |
| `duo-testplan-converge` | duo | `Duo/TestPlan-<slug>/Result.md` + `test-plan/<repo>/<svc>/flows/<flow>.md` tree (6-phase per-unit duo author + step-by-step diff convergence, ~3-5x lower dispatch ceiling) | no (writes test plan markdown only) |
| `linked-testplan` | rulebook | (loaded by `duo-testplan-build` / `duo-testplan-converge` or by explicit reference; no output of its own) | no |

All duo skills trigger only on the explicit `duo` keyword (e.g. `duo design X`, `duo-review X`, `/duo-prod-ready <scope>`). None auto-activate on plain `design X` / `review X` phrasing. The `linked-testplan` rulebook is passive — loaded by orchestrator-dispatched agents or activated only on explicit `apply linked-testplan rules to X` prose.

## Requirements

- `codex` CLI on PATH. Skills pin model `gpt-5.5`, reasoning `xhigh`, yolo / `--dangerously-bypass-approvals-and-sandbox`. Web search is `live` for most skills. `duo-testplan-build` and `duo-testplan-converge` are exceptions: web search defaults OFF (source code is the only ground truth); flip to `live` with the `web-allowed` prose modifier.
- Git working tree at the convergence target.

## Install

### Claude Code

```
claude plugin marketplace add yuridevx/yd-skills
claude plugin install yd@yd
```

Or from inside a Claude Code session:

```
/plugin marketplace add yuridevx/yd-skills
/plugin install yd@yd
```

### Codex CLI

```
codex plugin marketplace add yuridevx/yd-skills
```

Codex auto-enables shipped plugins on marketplace add. Disable per-plugin in `~/.codex/config.toml`:

```toml
[plugins."yd@yd"]
enabled = false
```

## Layout

See [AGENTS.md](AGENTS.md).

## License

MIT - see [LICENSE](LICENSE).
