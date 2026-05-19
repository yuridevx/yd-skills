---
name: solo-runtestplan
description: Claude-only executor for e2e test plan trees authored by `solo-testplan` / `duo-testplan` (or any tree following the `linked-testplan` page shape). Aggregates one or more test plan trees, generates a no-external-ports docker-compose stack, brings it up, and runs every HAPPY/NEGATIVE scenario via CLI tools (curl, kcat, redis-cli, psql, mc, grpcurl, …) inside a single runner container on an internal network. Four phases — `plan-aggregate`, `compose-build`, `flow-execute`, `result`. Per-flow subagents translate scenarios to runner-exec'd commands, observe via the same runner, and append immutable entries to `Bugs.md` (failures with full repro) and `Log.md` (chronological event ledger). No INCONCLUSIVE state — observation gaps trigger autonomous recovery (subagent self-installs tools / restarts deps; main re-dispatches compose-build for structural fixes) until every scenario reaches PASS / FAIL / SKIPPED or the per-flow `recovery-budget` (default 5) is exhausted (which itself files an `observation-exhausted` bug). Strict sequential flow execution; scrub-between-attempts derived from external-dep tags. TRIGGERS ONLY on explicit "solo" keyword — `solo runtestplan X`, `solo-runtestplan X`, `/solo-runtestplan X`, `solo run testplan X`, `solo execute testplan X`. Does NOT auto-activate on plain `run tests`, `execute tests`, `e2e run`, or `test the system`.
---

# Solo Run-Test-Plan

Autonomous executor for e2e test plan trees. Given one or more inputs (slugs that resolve under `Solo/TestPlan-<slug>/` or `Duo/TestPlan-<slug>/`, or arbitrary paths to directories of `linked-testplan` pages), generate a no-external-ports docker-compose stack, bring it up, and run every scenario via CLI tools inside a single runner container. Maintain append-only `Bugs.md` and `Log.md` ledgers in-stream; write a thin `Result.md` at the end.

There is no INCONCLUSIVE outcome. Observation gaps drive autonomous recovery loops until each scenario reaches PASS / FAIL / SKIPPED, or until the per-flow recovery budget is exhausted (which itself produces a FAIL bug entry with `kind: observation-exhausted`).

The companion `linked-testplan` rulebook is consumed AS IS. It owns the page shape the executor parses. Do not modify it from this skill.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

### Trigger

Trigger only on explicit `solo` phrasing:

- `solo runtestplan X`
- `solo-runtestplan X`
- `/solo-runtestplan X`
- `solo run testplan X`
- `solo execute testplan X`

Do NOT activate on plain `run tests`, `execute tests`, `test the system`, `e2e run`, or any prose without the literal `solo` token.

### Mode

Detect autonomous mode when prose contains a clear execution phrase: `autonomously`, `no questions`, `hands-free`, `auto`, or `unattended`. In autonomous mode, never call `AskUserQuestion`; missing inputs land in `Bugs.md` / `Log.md` / `Result.md → Unresolved`.

Default mode allows at most one clarifying question if the mission cannot start (e.g., empty or unresolvable input set). Ask inline as plain text — never via `AskUserQuestion`.

### Modifiers

| Modifier | Effect |
|---|---|
| `keep-stack` | Default. Leave the docker stack up at mission end for inspection. |
| `teardown` | Run `docker compose -f <mission>/compose.yaml down -v` at end of `result`. |
| `recovery-budget=N` | Maximum recovery cycles per flow and per compose-build re-dispatch. Default 5. |

Web access (WebFetch / WebSearch) is always enabled for subagents — no modifier needed.

### Filter and Slug

The prose can name one or more inputs:

- A slug (`Petclinic`) — resolved under `Solo/TestPlan-<slug>/` first, then `Duo/TestPlan-<slug>/`.
- A path (`./somewhere/test-plan/`) — treated as a directory of `linked-testplan` pages.
- Mixed list separated by commas or "and" (`solo runtestplan Petclinic, OrdersFlow, ./external/another-plan`).

Empty input set halts with a clean error. No implicit "run everything in the workspace".

Mint a 2-5 PascalCase slug from prose ending in `Run`, for example `PetclinicRun` or `OrdersFlowRun`. If the user names an existing `Solo/RunTestPlan-<slug>/`, resume from `.solo-run/journal.jsonl`.

For path inputs, derive a `<tree-tag>` from the PascalCased basename of the parent of `test-plan/`, deduplicated against existing tags by `Foo` / `Foo2` / `Foo3`. For slug inputs, `<tree-tag>` equals the slug.

## Plugin Layout and Path Resolution

This skill ships in the `yd` plugin alongside the `linked-testplan` rulebook. The mission CWD is the user's target workspace, not the plugin install directory, so plugin-relative paths must be resolved to absolute paths before they are passed to dispatched subagents.

At activation, resolve once and reuse for the mission:

- `PLUGIN_ROOT`: two directories above this skill directory.
- `RULEBOOK_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`.
- `RULEBOOK_REFS_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/references/`.

Pass these absolute paths in every dispatched prompt. Before the first subagent writes any artifact, verify `RULEBOOK_ABS` and `RULEBOOK_REFS_ABS` exist and are readable. Halt on broken install.

This skill does NOT use `scripts/check-refs.py` (used by `solo-testplan` / `duo-testplan` for ref validation against authored plans). Do not resolve it.

### Runtime Requirements

- `docker` and `docker compose` v2 on PATH. Probe both at activation; halt with a clean error if absent.
- Git working tree at the user's target workspace.
- `codex` is NOT required (Claude-only skill).
- Web access available to subagents.

## Mission Folder Layout

```
Solo/RunTestPlan-<slug>/
  Result.md                       thin end-of-mission summary
  Bugs.md                         append-only bug ledger
  Log.md                          append-only event ledger
  compose.yaml                    generated stack manifest
  compose.runner.Dockerfile       runner image build context
  .solo-run/
    journal.jsonl                 main-only coordinator journal
    run-manifest.json             aggregated plan input + flow catalog
    input-sources.json            resolved input trees (slugs/paths + roots)
    compose-build/
      Author-r00.md
      Refine-r01.md               optional, on re-dispatch
      Author-r01.md
    flow-execute/
      <tree-tag>__<flow-id>/
        attempts/
          attempt-r00.md
          attempt-r01.md
        recovery/
          repair-r01.md
        terminal.md
    result/
      coverage-matrix.json
```

**Root contains only visible deliverables.** Five files at root: `Result.md`, `Bugs.md`, `Log.md`, `compose.yaml`, `compose.runner.Dockerfile`. Everything else under `.solo-run/`.

**Tree-tag** namespaces flows across queued trees. Two trees that both contain a flow named `post-owners` get distinct unit keys: `Petclinic__post-owners` and `Vetclinic__post-owners`.

**Slash characters in repo names** become `__` to keep `flow-execute/` flat.

**Attempts are immutable, numbered.** Each re-dispatch after a recovery cycle writes a fresh `attempt-rNN.md`. Prior attempts are never overwritten. `repair-rNN.md` precedes `attempt-rNN.md` (cycle number matches the attempt that follows).

**Unit key formats** (used in journal events and ledger entries):

| Phase | Unit key |
|---|---|
| `plan-aggregate` | `plan-aggregate` |
| `compose-build` | `compose-build` |
| `flow-execute` (local flow) | `flow-execute/<tree-tag>__<flow-id>` |
| `flow-execute` (cross-app flow) | `flow-execute/<tree-tag>__crossapp__<cflow-id>` |
| `result` | `result` |

Cross-app flows live in the same `flow-execute/` directory; only their CLI commands differ (multiple services as actors).
