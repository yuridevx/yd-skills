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

## Pipeline

Four descriptive phases, all hard-gated.

| Phase | Role | Owner | Cardinality |
|---|---|---|---|
| `plan-aggregate` | Resolve input slugs/paths. Parse every test plan page. Build `run-manifest.json` cataloging flows, scenarios, external-dep tags across all queued trees. | Main session, mechanical | sequential, single execution |
| `compose-build` | One subagent generates `compose.yaml` + `compose.runner.Dockerfile`. Main runs `docker compose build` + `up -d` + healthcheck-wait. Re-dispatch on validation / bring-up failure, bounded by `recovery-budget`. | Subagent for authoring; main for execution | sequential |
| `flow-execute` | Per-flow subagents dispatched **strictly sequentially**. Each translates scenarios → CLI commands, runs inside the runner, observes, classifies, appends to `Bugs.md` / `Log.md`. Main scrubs stack state between attempts and drives main-side recovery on `bailed` returns. | Per-flow subagents + main scrub/recovery | strict sequential |
| `result` | Main writes thin `Result.md` summary (counts, coverage matrix, recovery-exhausted flows, caveats). | Main only | sequential |

### Gates

Three hard barriers:

1. `plan-aggregate` complete → `compose-build` may start.
2. `compose-build` subagent terminal **and** main confirms stack health → `flow-execute` may start.
3. All `flow-execute` units terminal → `result` may start.

No streaming handoffs (unlike `solo-testplan`): strict sequential flow execution means there is no upstream/downstream overlap opportunity.

## plan-aggregate Phase

Main-only, sequential, one execution.

1. Resolve each input source. Slug → `Solo/TestPlan-<slug>/` then `Duo/TestPlan-<slug>/`. Path → use as-is. Halt with clean error if any source is unresolvable.
2. For each resolved tree, glob `test-plan/**/*.md`. Parse the linked-testplan page shape:
   - `Trigger:`, `Entry:`, `Brief:` header.
   - `## Scenarios` with HAPPY / NEGATIVE tagged blocks containing Preconditions, Steps, Expected, Mocks, Code refs.
3. Detect SKIPPED-eligible scenarios up front:
   - Any scenario whose page carries an `[unresolved:]` tag covering its assertions.
   - Any scenario whose `Mocks:` line names an external the runner cannot stand up (e.g., a specific third-party SaaS not modeled by a generally-available image).

   These are flagged in `run-manifest.json` with `skip_reason`. The per-flow subagent will append `scenario-skipped` to Log.md without executing them.
4. Aggregate external-dep tags across trees. Multiple trees declaring `kafka:produce:owner-updated` collapse to one tag. Used by `compose-build` to size the stack.
5. Commit `.solo-run/run-manifest.json` and `.solo-run/input-sources.json`. Append `phase_complete`.

`run-manifest.json` shape:

```json
{
  "trees": [
    { "tree_tag": "Petclinic", "source_kind": "slug", "root": "/abs/path" }
  ],
  "flows": [
    {
      "unit_key": "flow-execute/Petclinic__post-owners",
      "tree_tag": "Petclinic",
      "flow_id": "post-owners",
      "page_path": "/abs/path/test-plan/petclinic/customer/flows/post-owners.md",
      "entry": { "file": "...", "line": 42 },
      "external_deps": ["http:server:POST /api/owners", "sql:write:owners"],
      "scenarios": [
        { "name": "...", "tag": "HAPPY", "skip_reason": null },
        { "name": "...", "tag": "NEGATIVE", "skip_reason": "[unresolved:] tag on Expected" }
      ]
    }
  ],
  "aggregated_external_deps": [
    "kafka:produce:owner-updated", "redis:write:owner:cache:"
  ]
}
```

## compose-build Phase

One subagent under `.solo-run/compose-build/` owns authoring of `compose.yaml` + `compose.runner.Dockerfile`. Main owns `docker compose build` + `up -d` + healthcheck-wait + re-dispatch on failure.

### Subagent inputs

Passed in the prompt:

- `.solo-run/run-manifest.json` (aggregated services + external-dep tags).
- Per-flow source root paths (resolved during `plan-aggregate`).
- Workspace-walk seed — known build-config filenames to look for near each `Entry:`: `Dockerfile`, `docker-compose.yml` (read for reference only, not consumed wholesale), `package.json`, `pom.xml`, `build.gradle`, `go.mod`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `*.csproj`.
- Web access (always allowed) for image-tag and CLI-invocation lookups.
- Hard generation rules (below).

### Subagent outputs

At the mission root:

- `compose.yaml` — every service + the runner + a single internal bridge network.
- `compose.runner.Dockerfile` — runner image build context.

Under `.solo-run/compose-build/`:

- `Author-rNN.md` — generation rationale per service (why this image, why this healthcheck, why this runner toolset).

### Hard generation rules

1. **No `ports:` mapping on any service.** Validated by main parsing the compose YAML.
2. **One internal network** named `runtestplan-net`. Every service + the runner joins it.
3. **Every service has a `healthcheck`** runnable inside its own container (no external curl). Generic patterns:
   - HTTP server: `wget --spider http://localhost:<port>/health` or `curl -f` or `nc -z localhost <port>` as last-resort.
   - Kafka broker: `kafka-broker-api-versions --bootstrap-server localhost:9092` or `nc -z`.
   - Redis: `redis-cli ping`.
   - Postgres: `pg_isready -U <user>`.
   - MinIO / S3-compatible: `curl -f http://localhost:9000/minio/health/live`.
   - Other kinds: documented in Author-rNN.md.
4. **Image selection — generally-available only, no baked catalog.** Subagent picks at generation time:
   - Docker Hub Official Images first: `postgres`, `redis`, `mongo`, `mysql`, `nginx`, `alpine`, `debian`.
   - Kafka: `apache/kafka` (KRaft mode) preferred; `confluentinc/cp-kafka` acceptable.
   - S3: `minio/minio`.
   - Workspace services: build from their Dockerfile if one exists near the Entry path. If absent, emit as `compose-gap` blocker in Author-rNN.md → main re-dispatches with escalation (no fallback synthesis of Dockerfiles for workspace services).
   - Pin to a specific tag (no `:latest`). Subagent web-checks tag existence before emitting.
5. **External-dep tag → service mapping is one-to-many-acceptable.** Multiple kafka topics collapse to one broker; multiple redis prefixes collapse to one redis; multiple sql tables collapse to one postgres unless plans declare distinct databases by name.
6. **Init / seed wiring.** Declarative seed via standard image conventions (`/docker-entrypoint-initdb.d/` for postgres, sidecar init for kafka, etc.) when possible. Non-declarative seeds deferred to runtime per-flow setup.

### Runner image

`compose.runner.Dockerfile`:

- Base: alpine (default) or debian-slim if a tool requires it. Subagent picks based on toolset.
- Tools at image-build time — union of CLI tools implied by aggregated external-dep tags + baseline (`curl`, `jq`, `wget`, `coreutils`). Mappings: kafka → `kcat`; redis → `redis`; sql → `postgresql-client`; s3 → `mc` or `awscli`; grpc → `grpcurl`.
- Long-running command: `tail -f /dev/null`. Main `docker compose exec`s into it.
- No host volume mounts.

### Main's bring-up loop

1. Dispatch subagent. Wait for completion notification (no polling).
2. Validate on return:
   - `compose.yaml` exists and `docker compose -f compose.yaml config` exits 0.
   - No service declares `ports`.
   - Every service has a `healthcheck`.
   - `compose.runner.Dockerfile` exists and parses.
3. On validation failure: append `compose-validation-failed` to `Log.md`; re-dispatch the subagent with the errors attached as a `Refine-rNN.md` analogue. Bounded by `recovery-budget` (default 5).
4. On validation pass: `docker compose build` → `docker compose up -d` → poll healthchecks until all healthy (bounded wait, default 5 minutes). Append `stack-up` then `stack-healthy` events.
5. Health-wait failure → re-dispatch with `docker compose logs <svc>` attached. Same budget.
6. Compose-build budget exhausted → `mission_halted { reason: compose-build-exhausted }`. The only mission-halt path during normal operation.

Compose-build terminal states:

- `CLEAN` — stack healthy on first attempt.
- `REPAIRED` — stack healthy after N re-dispatches (logged in Log.md).
- `BLOCKED` — budget exhausted; mission halts.

## flow-execute Phase

Strict sequential per-flow execution. Per-flow subagents dispatched one at a time in the order defined by `run-manifest.json`: local flows first grouped by `(tree-tag, repo, svc)` in document order, then cross-app flows last.

### Per-Flow Subagent Prompt

Composed in-memory by main, passed as the Agent tool's `prompt` parameter:

- Mission folder absolute path, CWD absolute path.
- Absolute paths: `RULEBOOK_ABS` (linked-testplan/SKILL.md), `BUGS_ABS`, `LOG_ABS`, `MANIFEST_ABS`.
- The flow page absolute path + every `Entry:` / `Code refs:` file path.
- External-dep tags scoped to this flow.
- Service-to-container mapping for the running stack.
- Runner exec template:

```
docker compose -f <mission>/compose.yaml exec -T runner sh -c '<cmd>'
```

- Append paths and append-only contract.
- Write paths: `attempts/attempt-rNN.md` + `terminal.md`. Forbidden to write anywhere else except via append to Bugs/Log.
- Read paths: all prior `attempts/attempt-r*.md` and `recovery/repair-r*.md` in this unit subfolder.
- Attempt number + recovery budget remaining.
- Boundaries:
  - No sub-subagents.
  - No edits to test plan, compose.yaml, or runner Dockerfile.
  - Self-recovery allowed only inside the stack (in-place subagent fixes); no compose authoring.

### Self-Recovery Boundary

**Subagent-fixable** (in-dispatch self-heal):

- Install tools in the runner: `docker compose exec runner apk add <pkg>` / `apt-get install` / similar.
- Restart a single service: `docker compose restart <svc>`.
- Wait-then-retry on healthcheck (bounded, e.g. 5 × 3s).
- Reset kafka topic (delete + recreate via broker CLI).
- Flush redis keys for a prefix.
- Drop + recreate postgres schema / truncate tables.
- Seed init state via SQL or HTTP POST against in-stack services.

**Main-fixable only** (subagent escalates with bail):

- Edit `compose.yaml` (add service, change image tag, change env var, change network, change healthcheck definition).
- Edit `compose.runner.Dockerfile` (change base image; runtime tool installs stay subagent-fixable).
- Full stack rebuild / `down -v && up -d`.
- Cross-flow state corruption that the upcoming flow can't reach to scrub.
- Structural compose gap (test plan declares a topic / table / service the manifest didn't generate).

### Per-Attempt Control Flow Inside the Subagent

1. **Read context.** Flow page + prior `attempt-r*.md` + prior `repair-r*.md` + run-manifest scope.
2. **Pre-flight requirements check.** Scan all scenarios; infer the toolset and in-stack deps required. For each requirement:
   - Satisfied → continue.
   - Not satisfied → attempt self-recovery from the subagent-fixable set. Append `recovery-action` to `Log.md` with `actor: subagent` per action.
   - Self-recovery fails after local retry budget → **accumulate** into `bail_errors`. Do NOT return yet; continue checking other requirements.
3. **Scenario loop.** For each scenario in document order:
   - Set up preconditions (idempotent). Failure here triggers self-recovery; persistent failure accumulates to `bail_errors`; affected scenario is skipped within this attempt and logged as `scenario-skipped-by-bail`.
   - Execute `Steps:` via runner exec. Capture exit code, stdout, stderr per command.
   - Observe `Expected:` via runner exec. Untranslatable observations trigger the same self-recovery path.
   - Classify PASS / FAIL. Append `scenario-pass` or `scenario-fail` to `Log.md`. On FAIL, append a `kind: assertion-contradicted` block to `Bugs.md`. Continue regardless.
   - SKIPPED scenarios (pre-flagged in manifest) skip execution; append `scenario-skipped` with `skip_reason` from manifest.
4. **Terminal.** Write `terminal.md` summarizing per-scenario outcomes for this attempt.
5. **Return** structured payload (see below).

The subagent **accumulates** bail errors and continues checking other requirements / scenarios — it does NOT return on first failure. Main receives the full error list in one batch and addresses all of them in one repair cycle.

### Subagent Return Shape

```yaml
attempt: <N>
unit_key: flow-execute/<tree-tag>__<flow-id>
state: PASS-all | mixed | FAIL-all | bailed
self_recovery_actions: [<action list>]
bail_errors:
  - kind: tool-unfixable | infra-unfixable | observation-unfixable | compose-gap
    detail: { tool?, container?, observation?, evidence: [...] }
    self_recovery_tried: [<list>]
    rationale: <terse why-it's-main's-job>
scenarios:
  - { name, tag, outcome: PASS|FAIL|SKIPPED|SKIPPED-BY-BAIL, bug_id?: <n> }
```

`PASS-all` / `mixed` / `FAIL-all` are terminal — main moves to scrub + next flow. `bailed` triggers main's recovery cycle.

### Soft Self-Recovery Budgets Inside the Subagent

Defaults, overridable in the prompt by main:

- Tool install: 2 attempts per tool.
- Service restart + wait-health: 3 cycles of `restart → 5×3s healthcheck poll`.
- Topic / schema / key reset: 2 attempts.

If a single requirement hits its local budget, the subagent accumulates the bail and moves on — it does not retry that requirement again within the same attempt.

### Re-Dispatch Contract

Fresh-context subagent each attempt. New attempt reads every prior `attempt-r*.md` + `repair-r*.md`. Main runs a **scrub before every attempt** (first dispatch and every re-dispatch). Every scenario re-runs from scratch.

### Cross-App Flow Execution

Same per-flow subagent shape. Differences:

- The prompt names multiple services as actors.
- The scenario `Steps:` are prefixed `<service> → <service>:`.
- The subagent typically issues `curl` between services, or back-to-back kafka producer/consumer pairs via runner exec.

No special phase or unit kind.
