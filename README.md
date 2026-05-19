# yd-skills

Dual-target plugin: ships the same skill set to Claude Code and Codex CLI from one repository.

## What you get

Seven duo skills for symmetric Claude+Codex convergence (each dispatches a parallel `codex` agent and writes a converged artifact under `Duo/<MissionKind>-<slug>/Result.md`), one Claude-only solo skill that produces the same artifact shape as `duo-testplan` without a codex peer, and one passive rulebook skill.

| Skill | Kind | Output | Writes code? |
|---|---|---|---|
| `duo-design` | duo | `Duo/Design-<slug>/Result.md` | no |
| `duo-discuss` | duo | `Duo/Discussion-<slug>/Result.md` | no |
| `duo-forge` | duo | `Duo/Forge-<slug>/Result.md` + `~/.claude/skills/duo-<name>/SKILL.md` | no (writes the new skill file) |
| `duo-prod-ready` | duo | per-cycle commits on the working branch | YES |
| `duo-research` | duo | `Duo/Research-<slug>/Result.md` | no |
| `duo-review` | duo | `Duo/Review-<slug>/Result.md` | no |
| `duo-testplan` | duo | `Duo/TestPlan-<slug>/Result.md` + `test-plan/<repo>/<svc>/flows/<flow>.md` tree (6-phase per-unit duo author + step-by-step structured diff convergence) | no (writes test plan markdown only) |
| `solo-testplan` | solo (Claude-only) | `Solo/TestPlan-<slug>/Result.md` + same `test-plan/` tree as duo-testplan. 5 named phases (service-scope, local-flows, cross-app-survey, cross-app-flows, result); each unit is a chain of independent fresh-context subagent dispatches — Author + N Refinement rounds, substance-only diffs, editorial edits forbidden. | no |
| `linked-testplan` | rulebook | (loaded by `duo-testplan` / `solo-testplan` or by explicit reference; no output of its own) | no |

All duo skills trigger only on the explicit `duo` keyword (e.g. `duo design X`, `duo-review X`, `/duo-prod-ready <scope>`). `solo-testplan` triggers only on the explicit `solo` keyword (`solo testplan X`, `/solo-testplan X`). None auto-activate on plain `design X` / `review X` / `test plan X` phrasing. The `linked-testplan` rulebook is passive — loaded by orchestrator-dispatched agents or activated only on explicit `apply linked-testplan rules to X` prose.

## Requirements

- `codex` CLI on PATH for every duo skill. `solo-testplan` does NOT need `codex` — it is Claude-only.
- Duo skills pin codex model `gpt-5.5`, reasoning `xhigh`, yolo / `--dangerously-bypass-approvals-and-sandbox`. Web search is `live` for most skills. `duo-testplan` and `solo-testplan` are the exceptions: web search defaults OFF (source code is the only ground truth); flip to `live` with the `web-allowed` prose modifier.
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
