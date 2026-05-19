---
name: solo-runtestplan
description: Claude-only executor for e2e test plan trees authored by `solo-testplan` / `duo-testplan` (or any tree following the `linked-testplan` page shape). Aggregates one or more test plan trees, generates a no-external-ports docker-compose stack, brings it up, and runs every HAPPY/NEGATIVE scenario via CLI tools (curl, kcat, redis-cli, psql, mc, grpcurl, …) inside a single runner container on an internal network. Four phases — `plan-aggregate`, `compose-build`, `flow-execute`, `result`. Per-flow subagents translate scenarios to runner-exec'd commands, observe via the same runner, and append immutable entries to `Bugs.md` (failures with full repro) and `Log.md` (chronological event ledger). No INCONCLUSIVE state — observation gaps trigger autonomous recovery (subagent self-installs tools / restarts deps; main re-dispatches compose-build for structural fixes) until every scenario reaches PASS / FAIL / SKIPPED or the per-flow `recovery-budget` (default 5) is exhausted (which itself files an `observation-exhausted` bug). Strict sequential flow execution; scrub-between-attempts derived from external-dep tags. TRIGGERS ONLY on explicit "solo" keyword — `solo runtestplan X`, `solo-runtestplan X`, `/solo-runtestplan X`, `solo run testplan X`, `solo execute testplan X`. Does NOT auto-activate on plain `run tests`, `execute tests`, `e2e run`, or `test the system`.
---

# Solo Run-Test-Plan

Autonomous executor for e2e test plan trees. Given one or more inputs (slugs that resolve under `Solo/TestPlan-<slug>/` or `Duo/TestPlan-<slug>/`, or arbitrary paths to directories of `linked-testplan` pages), generate a no-external-ports docker-compose stack, bring it up, and run every scenario via CLI tools inside a single runner container. Maintain append-only `Bugs.md` and `Log.md` ledgers in-stream; write a thin `Result.md` at the end.

There is no INCONCLUSIVE outcome. Observation gaps drive autonomous recovery loops until each scenario reaches PASS / FAIL / SKIPPED, or until the per-flow recovery budget is exhausted (which itself produces a FAIL bug entry with `kind: observation-exhausted`).

The companion `linked-testplan` rulebook is consumed AS IS. It owns the page shape the executor parses. Do not modify it from this skill.
