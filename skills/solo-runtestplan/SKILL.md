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

## Recovery Cycle (Main-Side)

Triggered when a per-flow subagent returns `state: bailed` with a non-empty `bail_errors` list. Main is the only actor in this cycle — subagents are off-stage between attempts.

**Main does NOT edit `compose.yaml` or `compose.runner.Dockerfile` directly.** Structural fixes go through a compose-build subagent re-dispatch with a refinement-style prompt.

### Cycle Steps

1. **Read & classify.** Parse `bail_errors`; each has a `kind ∈ {tool-unfixable, infra-unfixable, observation-unfixable, compose-gap}` plus `self_recovery_tried`.
2. **Plan repair actions.** Each `bail_error` maps to one or more main-fixable actions:

   | Bail kind | Likely main action |
   |---|---|
   | `tool-unfixable` | Bake the tool into `compose.runner.Dockerfile` via compose-build re-dispatch → rebuild runner. |
   | `infra-unfixable` | Restart → recycle service → escalate to compose-build for definition change. |
   | `observation-unfixable` | Typically compose-build issue (missing service, wrong image, wrong env). Dispatch compose-build with bail evidence. |
   | `compose-gap` | Dispatch compose-build with gap brief. |

3. **Execute targeted runtime fixes first** (no subagent dispatch):
   - `docker compose restart <svc>` (with health wait).
   - `docker compose build <svc> && docker compose up -d <svc>` (Dockerfile-only change for the service).
   - `docker compose build runner && docker compose up -d runner` (after compose-build refinement that touched only the runner image).
   - Full stack recycle: `docker compose down -v && docker compose up -d` (last resort; logged as `stack-recycle`).
4. **Dispatch compose-build subagent for structural fixes** — when `compose.yaml` or runner Dockerfile content must change. Compose-build receives a refinement-style prompt: current files, prior Author-rNN.md, bail evidence, "emit minimum diff to fix listed errors". Output is `Author-rNN+1.md` + fresh `compose.yaml` + fresh `compose.runner.Dockerfile`. Main re-applies + health-waits per the bring-up loop above.
5. **Write `repair-rNN.md`** under the flow's `recovery/` subfolder. One block per action: kind, command or diff, outcome, time. Cycle number `NN` matches the next attempt number.
6. **Append `recovery-*` events to `Log.md`** as actions happen (`actor: main`).
7. **Re-dispatch per-flow subagent** for attempt `N+1`. New fresh-context dispatch reads every prior `attempt-r*.md` + `repair-r*.md` and runs a clean scrub before its scenarios.

### Budget Accounting

`recovery-budget=N` (default 5) caps the number of recovery cycles per flow (i.e., maximum `repair-rNN.md` count). The cycle counts as one regardless of how many bail errors it addresses or how many repair actions it invokes. Main batches all repairs for one bail into a single cycle.

### Budget Exhaustion Semantics

When attempt `N` returns `bailed` and `N == recovery-budget`:

- Flow terminal state: `budget-exhausted`.
- For each unresolved `bail_error`, main appends a bug block to `Bugs.md` with `kind: observation-exhausted`. The block includes the full attempt log, every repair action tried, and every error returned.
- Main appends `flow-terminal` to `Log.md` with reason `budget-exhausted`.
- Main proceeds to scrub + next flow. **Mission does not halt** — one budget-exhausted flow does not block others.

Exception: if the compose-build subagent's own budget exhausts mid-recovery, main halts the entire mission with `mission_halted { reason: compose-build-exhausted }`. This is the only mission-halt path during `flow-execute`.

### Stack-Recycle Caveat

A full stack recycle (`down -v && up -d`) wipes all state including prior-flow state. Bug entries are immutable and remain in `Bugs.md`, but the deterministic-reproduction guarantee weakens for prior bugs: "scrub + run this flow" only holds if stack composition hasn't changed since the bug was filed. Main records this in `Result.md → Caveats` whenever a `stack-recycle` event occurs.

## Scrub Between Flow Attempts

Scrub = the cleanup pass that resets shared deps to a clean baseline. Runs **before every flow attempt** (first dispatch and every re-dispatch).

Without scrub, prior-flow state contaminates the next flow's preconditions. Example: flow A inserts an `owner` row; flow B's HAPPY scenario asserts "GET /owners returns an empty list" — fails because of A's leftover, not a real bug. Scrub eliminates that interference.

### Per-Tag Scrub Actions

Derived from the upcoming flow's external-dep tag set plus any tags touched by prior flows since the last full reset:

| Tag kind | Scrub action |
|---|---|
| `kafka:produce:<topic>` / `kafka:consume:<topic>` | Reset consumer-group offsets on the topic; optionally delete + recreate if marked destructive by the plan. |
| `redis:write:<prefix>` / `redis:read:<prefix>` | `redis-cli --scan --pattern <prefix>* \| xargs redis-cli del`. |
| `sql:write:<table>` / `sql:read:<table>` | `TRUNCATE TABLE <table> CASCADE`; if init has not run, re-run it. |
| `s3:write:<bucket>[/<prefix>]` | `mc rm --recursive --force <alias>/<bucket>/<prefix>`. |
| `sqs:produce:<queue>` / `sqs:consume:<queue>` | Purge queue (e.g., `aws sqs purge-queue` against localstack). |
| `http:server:<…>` / `http:client:<…>` | No-op (no persistent state). |
| `grpc:server:<…>` / `grpc:client:<…>` | No-op. |
| `cron:<…>` | No-op (cron entrypoint invoked directly inside the test). |

### Scrub Execution

Runs inside the runner via `docker compose exec -T runner sh -c '<scrub-script>'`. Main composes the script from the flow's tag set; appends `scrub-started` and `scrub-completed` events to `Log.md`.

### Scrub Failure

If scrub fails (psql can't reach postgres, redis-cli times out, etc.) → main treats it as a stack-level infra problem and enters the recovery cycle on behalf of the upcoming flow's first attempt. Scrub does not have its own budget; it consumes the flow's `recovery-budget`.

## Ledger and Report Formats

Three visible files at mission root: `Bugs.md`, `Log.md`, `Result.md`. `Bugs.md` and `Log.md` are append-only ledgers maintained in-stream by per-flow subagents and main. `Result.md` is single-write at the end of `result`.

### Bugs.md

Append-only bug ledger. Entries added by per-flow subagents (`kind: assertion-contradicted`) and by main (`kind: observation-exhausted` on budget-exhausted flows). Bug numbers assigned in append order; an entry's number does not imply priority.

Header (written once during `plan-aggregate`):

```markdown
# Bugs — <slug>

This is an append-only ledger. Each entry below is a self-contained, immutable
bug block. Entries are added by per-flow subagents as `assertion-contradicted`
bugs and by main as `observation-exhausted` bugs (budget-exhausted flows). Bug
numbers are assigned in append order; an entry's number does not imply
priority.

---
```

Per-entry block (template, verbatim shape):

````markdown
## Bug <NNN> — <flow-id> · <scenario-name> · <kind>

- **Tree:** <tree-tag>
- **Flow:** <flow-id>  (Entry: <file>:<line>)
- **Scenario:** <name> (HAPPY|NEGATIVE)
- **Kind:** assertion-contradicted | observation-exhausted
- **Attempt:** <N>
- **Reporting unit:** <unit_key>
- **Timestamp:** <ISO 8601 UTC>

**Expected**
> <verbatim quote from the flow page's Expected: block>

**Observed**
> <verbatim or summarized CLI evidence>

**Repro**
```sh
# Scrub commands run before this attempt
<scrub line 1>
# Scenario commands
<cmd 1>
```

**Evidence**
```text
<stdout, stderr, exit codes, container log tails — fenced verbatim>
```

**Source ref**
- <file>:<line>  (Entry)
- <file>:<line>  (Code refs from the flow page)

**Recovery attempts** (only for `observation-exhausted` kind)
- <repair-r01 summary>
- ...

---
````

Bug numbers are 3-digit zero-padded (`Bug 001`, `Bug 002`, …). Assigned by counting existing `## Bug ` headings before append. Duplicate FAILs across re-dispatches each append a new entry — the duplication itself is information (the bug reproduced); `Result.md`'s coverage matrix deduplicates for summary counts.

### Log.md

Append-only event ledger. Every entry has a timestamp, unit key, event kind, and an actor, plus a one-line summary and an optional fenced details block. Reading top-to-bottom is the chronological trace of the mission.

Header (written once):

```markdown
# Log — <slug>

Append-only event ledger. Every entry has a timestamp, unit key, event kind,
and an actor, plus a one-line summary and an optional fenced details block.
Reading top-to-bottom is the chronological trace of the mission.

---
```

Per-event block:

````markdown
### <ISO 8601 UTC> · <unit_key> · <event-kind> · <actor>
<one-line summary>

```<lang-or-empty>
<optional structured details: command run, stdout excerpt, error trace>
```
````

Event kind vocabulary (closed set):

| Event | Actor | When |
|---|---|---|
| `phase-start` / `phase-complete` | main | Per phase entry/exit |
| `stack-up` / `stack-healthy` / `stack-recycle` | main | Stack lifecycle |
| `flow-dispatched` / `flow-redispatched` / `flow-terminal` | main | Per-flow lifecycle |
| `scrub-started` / `scrub-completed` | main | Around per-attempt scrub |
| `scenario-pass` / `scenario-fail` / `scenario-skipped` / `scenario-skipped-by-bail` | subagent | Per scenario |
| `recovery-started` / `recovery-action` / `recovery-completed` | main \| subagent | Recovery cycle |
| `compose-validation-failed` / `compose-build-redispatched` | main | Compose-build re-dispatch path |
| `mission-halted` | main | Hard failure |

### Result.md

Single-write end-of-mission summary, ~200-400 lines max. Written once by main at the end of `result`.

```markdown
# Run Result — <slug>

## Summary
- Trees queued: <N> (<list>)
- Flows planned: <total>
- Flows executed: <total>  (PASS-all <n>, mixed <n>, FAIL-all <n>, budget-exhausted <n>)
- Scenarios: total <T>, PASS <P>, FAIL <F>, SKIPPED <S>, SKIPPED-BY-BAIL <SB>
- Bugs filed: <N>  (assertion-contradicted <n>, observation-exhausted <n>)
- Mission state: complete | halted-at-<phase>

## Pointers
- [Bugs.md](Bugs.md) — <N> entries
- [Log.md](Log.md) — chronological trace
- [compose.yaml](compose.yaml)
- [compose.runner.Dockerfile](compose.runner.Dockerfile)

## Coverage Matrix
| Tree | Flow | Scenario | Outcome | Bug# | Attempts | Recovery cycles |
|---|---|---|---|---|---|---|
| ... one row per (tree, flow, scenario) ... |

## Recovery-Exhausted Flows
- <flow-id> — <unit_key> — <N> repair cycles — final bail kinds: <list> — bug entries: <list of #s>

## Caveats
- <e.g., "Stack was recycled once during mission; bugs filed before <timestamp> may not reproduce against the post-recycle stack composition.">
- <e.g., "Compose-build re-dispatched 2 times before stack became healthy.">

## Unresolved
- Cross-cutting issues not tied to a single flow.
```

### Append Safety

Strict sequential per-flow execution means at most one subagent appends at any time. Main appends between dispatches. Each appender writes a full block via a single atomic file append (one OS write, terminated with `\n---\n` separator). No file locking required at v1.

## Journal Events (.solo-run/journal.jsonl)

Main-only writes. Mirrors `solo-testplan`'s shape.

| Event | Fields | When |
|---|---|---|
| `phase_start` | `phase`, `ts` | Before each phase |
| `subagent_spawn` | `phase`, `unit_key`, `role` (`author` \| `attempt`), `attempt`, `expected_output_path` | Before each subagent dispatch |
| `artifact_accepted` | `path`, `status` | After validating output |
| `artifact_rejected` | `path`, `reason` | After rejecting malformed output |
| `attempt_complete` | `unit_key`, `attempt`, `state`, `bail_error_count` | After per-flow attempt |
| `recovery_cycle` | `unit_key`, `cycle`, `actions[]` | After each main-side recovery cycle |
| `flow_terminal` | `unit_key`, `final_state`, `attempts_used`, `cycles_used` | At flow terminal |
| `stack_up` / `stack_healthy` / `stack_recycle` | `ts` | Stack lifecycle |
| `compose_build_redispatch` | `attempt`, `reason` | When main re-dispatches compose-build |
| `phase_complete` | `phase`, `counts` | At phase exit |
| `mission_halted` | `reason` | On fatal failure |

### Resumability

On harness restart with the same slug, main reads `journal.jsonl` tail:

- Last event `phase_start` without `phase_complete` → resume that phase.
- Last event `subagent_spawn` without `attempt_complete` → re-spawn the same attempt (output paths deterministic; subagents are fresh-context).
- Last event `recovery_cycle` without subsequent `subagent_spawn` → re-dispatch the next attempt.

## result Phase

Sequential final phase. Only hard barrier in normal operation: all `flow-execute` units terminal.

1. Main writes `Result.md` per the template above.
2. Main writes `.solo-run/result/coverage-matrix.json` — one row per (tree, flow, scenario) with outcome, bug-id-if-any, attempts-used, recovery-cycles-used.
3. No `result-sanity` subagent (no cross-flow contradiction pass). `Bugs.md` is the source of truth; cross-flow analysis is a follow-up `duo-review` mission over the mission folder.
4. If the `teardown` modifier is present: `docker compose -f <mission>/compose.yaml down -v` after `Result.md` is written.
5. Append `phase_complete` for `result`.

## Outcome Model

Closed terminal set per scenario:

| Outcome | Meaning |
|---|---|
| **PASS** | Every `Expected:` observation confirmed by CLI evidence. |
| **FAIL** | At least one `Expected:` observation contradicted. → `Bugs.md` `kind: assertion-contradicted`. |
| **SKIPPED** | Manifest-flagged at `plan-aggregate` (`[unresolved:]` tag or unmockable external). Never executed. |
| **SKIPPED-BY-BAIL** | Executable, but the same-attempt bail prevented running this scenario. Re-runs after main repair. |

No INCONCLUSIVE. Observation gaps drive recovery loops to PASS / FAIL or to `kind: observation-exhausted` (recorded as FAIL with full attempt log).

Per-flow terminal set:

| Flow state | Meaning |
|---|---|
| **PASS-all** | Every scenario PASS. |
| **mixed** | At least one PASS and at least one FAIL or SKIPPED. |
| **FAIL-all** | Every scenario FAIL (no PASS). |
| **budget-exhausted** | Recovery budget hit before all scenarios reached a terminal state. Unresolved scenarios converted to `observation-exhausted` bugs. |

## Failure Modes

| Failure | Owner | Behavior |
|---|---|---|
| Docker / `docker compose` not on PATH | Main, pre-mission | Halt with clean error; no folder created. |
| Input slug/path unresolvable | Main, plan-aggregate | Halt with clean error listing failing inputs. |
| Test plan markdown malformed | Main, plan-aggregate | Skip the malformed page, note in `run-manifest.json` with `parse_error`, continue. All-pages failure → halt. |
| Compose-build subagent emits unbuildable compose | Main | Re-dispatch with validation errors. Budget-exhausted → mission halt. |
| Stack fails to become healthy after `up -d` | Main | Re-dispatch compose-build with container logs. Budget-exhausted → mission halt. |
| Per-flow subagent returns no output / malformed YAML payload | Main | Retry same attempt once. Second failure → flow `budget-exhausted`; append `observation-exhausted` bug with reason `subagent-malformed-output`. |
| Per-flow subagent bails with errors | Main | Recovery cycle. Re-dispatch attempt N+1. Budget-exhausted → flow `budget-exhausted` + bugs filed; continue to next flow. |
| Scrub failure | Main | Treat as infra-suspect for the upcoming flow's first attempt; consumes that flow's `recovery-budget`. |
| Stack recycle required mid-mission | Main | Append `stack-recycle` event; record in `Result.md → Caveats`. |
| Compose-build budget exhausted mid-mission | Main | `mission_halted { reason: compose-build-exhausted }`. `Result.md` written with halt details. |
| User interrupt mid-mission | Main | Journal tail is the resume point. Re-run with same slug resumes. |

## Hard Rules

- **No Codex.** No `codex` invocation, no `.codex/` directory, no codex-specific flags. The skill must not reference Codex as a runtime tool.
- **Trigger only on explicit `solo` keyword.** Same discipline as `solo-testplan`.
- **No external ports.** Generated `compose.yaml` must not declare `ports:` on any service. Main validates after every compose-build output.
- **Single runner.** All CLI execution flows through `docker compose exec -T runner sh -c '…'`.
- **Main is a thin coordinator + stack operator.** Main runs `docker compose` commands, owns the journal/manifest/ledger headers/Result.md/coverage-matrix.json, runs scrub, and drives recovery. Main does NOT author content for `compose.yaml`, the runner Dockerfile, scenario translations, or bug entries.
- **`compose.yaml` and `compose.runner.Dockerfile` are authored only by the compose-build subagent.** Main edits neither directly.
- **No INCONCLUSIVE state.** Every scenario terminates PASS / FAIL / SKIPPED / SKIPPED-BY-BAIL.
- **Append-only ledgers.** `Bugs.md` and `Log.md` are immutable after each append. Re-dispatches append new entries; they never edit prior ones.
- **Per-flow subagents are short-lived, fresh-context.** Each attempt is a separate dispatch. No nested subagents.
- **Subagents read only what's in their prompt + their own unit subfolder + the linked-testplan rulebook + source within declared scope.** Subagents write only inside their own unit subfolder + via append to `Bugs.md` and `Log.md`.
- **Web always allowed.**
- **Strict sequential flows.** No parallel flow execution in v1.
- **Scrub before every flow attempt** (first dispatch and every re-dispatch).
- **Recovery budgets are bounded.** `recovery-budget=N` (default 5).
- **No polling.** Main waits for harness completion notifications between subagent dispatches.
