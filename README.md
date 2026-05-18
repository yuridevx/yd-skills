# yd-skills

Dual-target plugin: ships the same `duo-*` skill set to Claude Code and Codex CLI from one repository.

## What you get

Six skills for symmetric Claude+Codex convergence. Each one dispatches a parallel `codex` agent and writes a converged artifact under `Duo/<MissionKind>-<slug>/Result.md` in the working repo.

| Skill | Output | Writes code? |
|---|---|---|
| `duo-design` | `Duo/Design-<slug>/Result.md` | no |
| `duo-discuss` | `Duo/Discussion-<slug>/Result.md` | no |
| `duo-forge` | `Duo/Forge-<slug>/Result.md` + `~/.claude/skills/duo-<name>/SKILL.md` | no (writes the new skill file) |
| `duo-prod-ready` | per-cycle commits on the working branch | YES |
| `duo-research` | `Duo/Research-<slug>/Result.md` | no |
| `duo-review` | `Duo/Review-<slug>/Result.md` | no |

All trigger only on the explicit `duo` keyword (e.g. `duo design X`, `duo-review X`, `/duo-prod-ready <scope>`). None auto-activate on plain `design X` / `review X` phrasing.

## Requirements

- `codex` CLI on PATH. Skills pin model `gpt-5.5`, reasoning `xhigh`, live web search, and yolo / `--dangerously-bypass-approvals-and-sandbox`.
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
