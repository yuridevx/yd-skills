---
name: duo-testplan-build
description: Symmetric Claude+Codex authoring of an e2e test plan tree for multi-repo workspaces, with independent fresh-dispatch refinement after every authoring phase. Eight phases - scope, per-service extract, per-service refine, cross-app extract, cross-app refine, per-flow test-plan write, per-flow refine, result. Streaming dispatch across per-service and per-flow units. Code is the only source of truth - existing tests, READMEs, and documentation are excluded inputs. Produces `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow>.md` and `test-plan/cross-app/flows/<flow>.md`. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh + yolo. Web search OFF by default (source is truth); flip with `web-allowed`. TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo testplan X", "duo-testplan X", "/duo-testplan X", "duo build a test plan for X". Does NOT auto-activate on plain "test plan X" / "generate tests for X" / "e2e plan" requests.
---

# Duo Testplan Build

Run an 8-phase pipeline that produces an e2e test plan tree from source code. Every authoring phase pairs with a refinement phase: WRITE (Claude+Codex co-author, single round, orchestrator union-merges) then REFINE (N parallel FRESH-dispatch passes per iteration; iteration exits on all-CLEAN; no hard cap, soft warning at 3, escalation handshake at 5).

The rulebook lives in the companion `linked-testplan` skill. Every dispatched authoring or refinement agent reads the rulebook plus references for page shape, coverage vocabulary, and the 21-rule checklist. This skill is the executor; nothing here duplicates the rulebook.

## Plugin Layout and Path Resolution

This skill ships in the `yd` plugin alongside the `linked-testplan` rulebook (sibling skill) and `scripts/check-refs.py` (deterministic validator at the plugin root). The orchestrator's CWD is the mission target workspace, NOT the plugin install dir — so plugin-relative paths must be resolved to absolute paths before being passed to dispatched agents.

**At skill activation, resolve once and reuse for the mission:**

- `PLUGIN_ROOT` — derived from the skill's base directory (announced by the harness as "Base directory for this skill: ..."). Compute `PLUGIN_ROOT = <skill base>/../..`. For example, if the skill is at `C:\Users\<user>\.claude\plugins\cache\yd\yd\0.3.0\skills\duo-testplan-build`, then `PLUGIN_ROOT` is `C:\Users\<user>\.claude\plugins\cache\yd\yd\0.3.0`.
- `RULEBOOK_ABS` = `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`
- `RULEBOOK_REFS_ABS` = `$PLUGIN_ROOT/skills/linked-testplan/references/`
- `CHECK_REFS_ABS` = `$PLUGIN_ROOT/scripts/check-refs.py`

**Pass these ABSOLUTE paths in every dispatched prompt.** Task subagent prompts and codex stdin prompts both receive the absolute path; dispatched agents Read / Run them regardless of their CWD. Never instruct a dispatched agent to resolve `skills/...` or `scripts/...` relative to its own CWD — that fails because dispatched agents run in the user's workspace, not the plugin install dir.

**Self-test on first run of a mission.** Before P1 writes any artifact, verify that `RULEBOOK_ABS` and `CHECK_REFS_ABS` exist and are readable. If either is missing, halt with a clear error pointing at the broken install. Do not attempt to continue with placeholder paths.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

### Trigger

Triggers on explicit `duo` phrasing: `duo testplan X`, `duo-testplan X`, `/duo-testplan X`, `duo build a test plan for X`. Does NOT auto-activate on plain `test plan X` / `e2e plan` / `generate tests for X`.

### Modifiers (prose-detected)

| Modifier | Effect |
|---|---|
| `autonomously`, `no questions`, `hands-free`, `auto`, `unattended` | Autonomous mode: never call `AskUserQuestion`; missing preferences log to `Result.md → Unresolved`. |
| `high-concurrency` | Concurrency cap 4/4 → 8/8 (Claude/Codex). |
| `very-high-concurrency` | Concurrency cap → 16/16. |
| `refine-passes=N` | Parallel passes per refinement iteration (default 2). |
| `extended-budget` | Total mission wall-clock 90 min → 180 min. |
| `web-allowed` | Codex `web_search` flipped from `off` to `live` (default off; test planning grounds in source). |

Distinguish autonomous trigger phrases from topic adjectives ("design an autonomous system" is topic, not mode).

### Filter

Free-form repo filter in prose: `only ingestion-service`, `work on X and Y`, `ingestion-service, kafka-contract`. Empty filter → all discovered repos.

### Slug

Mint a 2-5 PascalCase slug from prose (e.g. `Petclinic`, `OrdersFlow`). If the user names an existing `Duo/TestPlan-<slug>/` folder, reuse it — the orchestrator picks up from journal tail.

## Mission Folder Layout

```
Duo/TestPlan-<slug>/
  Result.md                                            converged index + summary  (visible)

  Claude-P2-<repo>-<svc>.md                            P2 author positions        (visible)
  Codex-P2-<repo>-<svc>.md
  Extracted-P2-<repo>-<svc>.md                         orchestrator union-merge

  Claude-P3-<repo>-<svc>-iter<i>-pass<k>.md            P3 refinement pass files
  Codex-P3-<repo>-<svc>-iter<i>-pass<k>.md

  Claude-P4-crossapp.md                                P4 author positions
  Codex-P4-crossapp.md
  Extracted-P4-crossapp.md                             orchestrator union-merge

  Claude-P5-crossapp-iter<i>-pass<k>.md                P5 refinement pass files
  Codex-P5-crossapp-iter<i>-pass<k>.md

  Claude-P6-<flow-id>.md                               P6 author positions
  Codex-P6-<flow-id>.md
  Drafted-P6-<flow-id>.md                              orchestrator union-merge

  Claude-P7-<flow-id>-iter<i>-pass<k>.md               P7 refinement pass files
  Codex-P7-<flow-id>-iter<i>-pass<k>.md

  test-plan/                                           final artifact tree        (visible)
    <repo>/<svc>/flows/<flow-id>.md
    cross-app/flows/<flow-id>.md

  .codex/                                              ALL scratch / state / logs
    journal.jsonl                                      pre-write event log
    unit-manifest.json                                 P1 output
    dispatch-budget.json                               P1 budget estimate
    test-plan-index.json                               P8 internal index (optional)
    session-P2-<repo>-<svc>                            authoring session id (retry-only resume)
    session-P4-crossapp
    session-P6-<flow-id>
    (P3/P5/P7 refinement passes NEVER persist sessions — always fresh)
    <unit-key>-prompt.txt                              skill-body-authored prompts
    <unit-key>-stream.jsonl
    <unit-key>-final.txt
    <unit-key>-stderr.log
```

Root contains only position files + merged artifacts + `Result.md` + `test-plan/`. All scratch / sessions / streams / journal stay in `.codex/`.

## Discovery Toolbox

Source code is the only ground truth. Existing tests, READMEs, and documentation are excluded inputs at every phase.

1. Production source under each repo (per the exclusion set in P1 below).
2. `linked-testplan` rulebook (resolved as `$RULEBOOK_ABS` per Plugin Layout and Path Resolution above) — every authoring and refinement agent reads it.
3. Mission journal at `.codex/journal.jsonl` for resume semantics.
4. Prior position files within the mission — only the orchestrator reads them for control flow (Status header only); authoring agents see their own slice; refinement passes see ONLY the merged artifact, not authoring positions.
5. Web access is OFF by default. The `web-allowed` prose modifier flips Codex to `web_search="live"` for cases where external contract specs (Avro schema registry, public API spec) are part of the source-of-truth. Claude `WebSearch` / `WebFetch` follow the same gate.

Exclusion set (apply at every source walk):

```
Tests:    **/*.{spec,test,e2e}.*, **/test/**, **/tests/**, **/__tests__/**, **/spec/**, **/e2e/**
Build:    **/dist/**, **/build/**, **/.next/**, **/coverage/**
Vendor:   **/node_modules/**, **/local-packages/**
VCS/IDE:  **/.git/**, **/.idea/**, **/.vscode/**
Docs:     **/*.md, **/*.pdf, **/*.txt, **/CHANGELOG*, **/README*
```

## Pipeline

```
P1  Scope + manifest                  orchestrator (fast)
P2  Extract per-service               WRITE — duo per service (parallel)
P3  Refine extracts per-service       REFINE — fresh N parallel passes per iteration; emits two readiness bits
P4  Cross-app extract                 WRITE — single duo (gated on seam_index_ready from ALL services)
P5  Refine cross-app                  REFINE — may emit LATE-SERVICE-GAP patches
P6  Test plan write per-flow          WRITE — duo per flow, STREAMS as P3 per-service clears
P7  Refine test plans per-flow        REFINE — per-flow iteration
P8  Result                            orchestrator + final sanity duo + late-gap-empty check
```

### Phase 1 — Scope and Manifest

Orchestrator-only. Records source roots and entrypoint probes; does NOT claim file completeness.

Steps (in journal-correct order — pre-write records ALWAYS precede their writes):

1. Parse prose for repo filter, autonomous flag, concurrency, refine-passes, extended-budget, web-allowed.
2. Initialize `.codex/journal.jsonl` (create if missing). Append `phase_start` event for P1.
3. Enumerate target repos: each immediate subdir of cwd containing `.git/`, or cwd itself if a single repo.
4. Glob production source per the exclusion set above; classify per `apps/<svc>/` vs `_common`.
5. Probe entry-point surfaces per service: HTTP controllers, Kafka producers/consumers, gRPC servers/clients, cron / scheduled jobs, S3/DDB/SQL/Redis access points.
6. **Mint stable IDs:**
   - Per-service unit IDs from `<repo>/<service-dir-name>`.
   - **Per-entrypoint flow IDs derived from trigger + entry symbol** (e.g. `post-owners`, `consume-petclinic-owner-updated`, `cron-cleanup-stale-sessions`). Flow IDs are stable across runs; same code → same ID. Stored per entrypoint in the manifest so P2 and P6 prompts consume them directly rather than minting ad-hoc.
7. Estimate dispatch budget (see "Concurrency, Budget, Ceilings").
8. Append `dispatch_start` for the upcoming manifest/budget writes.
9. Write `.codex/unit-manifest.json` and `.codex/dispatch-budget.json`.
10. Append `artifact_accepted` events for each just-written file.
11. Append `phase_complete` event for P1.
12. `TodoWrite` one entry per P2 unit; P3/P6/P7 entries appended as upstream units complete.

`.codex/unit-manifest.json` shape (the orchestrator and every dispatched agent consume this):

```json
{
  "schema_version": 1,
  "repos": {
    "<repo>": {
      "services": {
        "<service-id>": {
          "candidate_roots": ["<path>", ...],
          "entrypoints": [
            {
              "flow_id": "post-owners",
              "trigger": "HTTP POST /owners",
              "entry_file": "<path>",
              "entry_line": <int>,
              "trigger_kind": "http | kafka-consumer | kafka-producer | grpc | cron | s3 | other"
            }
          ]
        }
      },
      "_common": { "candidate_roots": [...], "entrypoints": [...] }
    }
  }
}
```

The manifest is the once-globbed inventory both peers consume in P2. Each peer may ADD relevant files; neither may REMOVE.

### Phase 2 — Extract per-service (WRITE)

For each service unit, dispatch one duo. Claude Task subagent + background Codex session run independently against the unit's manifest slice + the rulebook. Each authors `Claude-P2-<repo>-<svc>.md` / `Codex-P2-<repo>-<svc>.md`:

```markdown
---
Artifact-Kind: P2-position
Schema-Version: 1
Unit: <repo>/<svc>
Status: EXTRACTED
---
# Flow extraction — <repo>/<svc> (<side>)

## Source coverage
- <relative path>:<line range> — <role: HTTP controller / Kafka consumer / etc.>

## Flows
### <flow-id>
- Trigger: <event / endpoint / topic / cron>
- Entry: <file>:<line>
- Touches: <objects / contracts referenced, grouped by kind>
- Pseudocode steps (terse): <inline <pre> or bullet sequence>

## Open Questions
- <issue> — <USER-TIER if substantive>
```

Orchestrator union-merges both positions into `Extracted-P2-<repo>-<svc>.md` (`Status: READY`). A flow named by only one side is preserved with a `[claimed-by: claude]` or `[claimed-by: codex]` tag — P3 will validate or remove it.

### Phase 3 — Refine extracts per-service (REFINE)

Independent improvement of each `Extracted-P2-<repo>-<svc>.md`. Default 2 parallel fresh passes per iteration (`refine-passes=N` to override). No hard iteration cap; soft warning at iteration 3 logged to `Result.md`; escalation handshake at iteration 5.

Iteration loop, per service unit:

```
artifact_v <- Extracted-P2-<repo>-<svc>.md
i <- 1
loop:
  dispatch N parallel FRESH duos against artifact_v
    each pass: new Claude Task subagent + new codex exec session (NO resume)
    inputs: artifact_v + source roots + linked-testplan rulebook + refinement checklist
    inputs DO NOT include: prior authoring positions, prior pass files (this iteration or earlier)
    output: pass file `{Claude|Codex}-P3-<repo>-<svc>-iter<i>-pass<k>.md`
            with Status: CLEAN | PATCHED | BLOCKED
            and ## Patches / ## Blocked sections
  await all 2N passes
  validate frontmatter + parse Status header
  if any pass file is invalid → synthesize INCONCLUSIVE; one retry within budget; then peer-attest DEGRADED-CONTINUE or BLOCKED
  if all 2N report CLEAN:
    artifact_v → Status: GATE-PASSED
    emit local_flows_ready
    emit seam_index_ready (after seam-index reconciliation; see below)
    exit loop
  union-merge non-conflicting patches → artifact_v+1
  conflicts → tie-breaker mini-duo (see Patch System)
  apply validators after patch batch (check-refs.py)
  i <- i + 1
  if i == 3: log soft warning
  if i == 5: escalation handshake (default: USER-TIER if both peers attest no progress; autonomous: peer-attested DEGRADED-CONTINUE or BLOCKED; no hard cap)
```

P3 emits two readiness bits per service:

- `local_flows_ready` — local flows extraction is gate-resolved; downstream P6 may dispatch for this service's flows.
- `seam_index_ready` — this service's contribution to cross-app seam discovery is trustworthy; P4 may consume its artifact.

The two bits can clear independently within a single iteration (e.g. local flows agree but a seam claim disputes). Cross-app P4 waits for `seam_index_ready` from ALL services. Local P6 streams aggressively on `local_flows_ready` per service.

### Phase 4 — Cross-app extract (WRITE)

Fires only when all per-service P3 units have emitted `seam_index_ready` (or terminated as DEGRADED-CONTINUE / BLOCKED). Single Claude + single Codex session, single round.

Inputs: every gate-resolved per-service extraction artifact. Both peers scan for cross-repo seams (Kafka producer/consumer in different repos, REST/gRPC server vs client, S3 writer vs reader). Each writes `Claude-P4-crossapp.md` / `Codex-P4-crossapp.md`. Orchestrator union-merges into `Extracted-P4-crossapp.md` (`Status: READY`).

P4 reads SERVICE ARTIFACTS by default, NOT raw source. Source consulted only when validating a disputed seam.

### Phase 5 — Refine cross-app (REFINE)

Same iteration loop as P3, applied to `Extracted-P4-crossapp.md`. Single artifact, single unit — still N parallel fresh passes per iteration.

P5 passes may emit `LATE-SERVICE-GAP` patches when cross-app synthesis discovers that a service missed a flow or a seam connection. A `LATE-SERVICE-GAP` patch:

- Reopens ONLY the affected service's artifact (P2/P3 cycle restarts for that service).
- Enqueues required downstream P6/P7 work for the gap.
- Does NOT invalidate finalized flows on other services or finalized cross-app flows that don't touch the gap.

On `GATE-PASSED` OR `DEGRADED-CONTINUE`, downstream P6 cross-app flows fire (DEGRADED-CONTINUE cross-app artifact carries `## Unresolved` into the cross-app flow plans). On `BLOCKED`, cross-app P6 does NOT fire; cross-app is summarized only in `Result.md`.

### Phase 6 — Test plan write per-flow (WRITE)

**Streaming dispatch.** The instant a per-service P3 emits `local_flows_ready` OR terminates `DEGRADED-CONTINUE`, dispatch one duo per flow that service owns. Services that terminate `BLOCKED` do NOT trigger P6 dispatch (per Failure Modes — BLOCKED units are summarized only in `Result.md`). Cross-app flows fire on P5 `GATE-PASSED` (or `DEGRADED-CONTINUE`; not on `BLOCKED`).

Each per-flow duo: Claude Task subagent + Codex session, single round, both author against the flow's gate-resolved extraction record + source roots + rulebook. Each writes:

- Position file `Claude-P6-<flow-id>.md` / `Codex-P6-<flow-id>.md` (`Status: WRITTEN`).
- A draft `test-plan/<repo>/<svc>/flows/<flow-id>.md` (or `test-plan/cross-app/flows/<flow-id>.md`).

Orchestrator union-merges scenarios into `Drafted-P6-<flow-id>.md`:

- Overlapping scenarios deduped by `(name, trigger, expected)` triple.
- Non-overlapping scenarios preserved with `[claimed-by: <side>]` tags.

BLOCKED service units do NOT emit a P6 file (per Failure Modes); only `Result.md` summarizes them.

### Phase 7 — Refine test plans per-flow (REFINE)

Same iteration loop as P3 and P5, applied per flow. Patches extended with scenario-level operations (`ADD-SCENARIO`, `REMOVE-SCENARIO`, etc.).

On `GATE-PASSED`, finalize `test-plan/<...>/<flow-id>.md`. On DEGRADED-CONTINUE, finalize with `## Unresolved` section. BLOCKED flows: NOT finalized; appear only in `Result.md`.

### Phase 8 — Result

Orchestrator-only. Sequence:

1. Read every finalized `test-plan/**/*.md` (terse by rulebook).
2. Run `$CHECK_REFS_ABS` (resolved per Plugin Layout and Path Resolution above) over the full tree. Pass the absolute path to the Bash invocation, not the plugin-relative `scripts/check-refs.py` form, because the orchestrator's CWD is the user's workspace.
3. Generate coverage matrix: every entrypoint in `unit-manifest.json` maps to exactly one flow OR one explicit "not externally observable" exclusion record.
4. Write `Result.md`: summary, scope, per-repo summary, scenario counts, refinement-iteration counts per unit, DEGRADED-CONTINUE / BLOCKED units, coverage matrix, unresolved.
5. Final sanity duo (single round): Claude scans `Result.md` + tree for cross-flow contradictions (incompatible payloads on same topic, conflicting expected outcomes for shared dependencies); Codex same. Disagreements log to `Unresolved`.
6. Late-gap-empty precondition: confirm `.codex/journal.jsonl` shows zero open `LATE-SERVICE-GAP` patches. If any open, escalate per failure flow before completing.
7. Append `phase_complete` journal event for P8.

## Refinement Pass Mechanics

A pass is the atomic unit of refinement. Each pass:

1. **FRESH dispatch.** New Task subagent (Claude) and new `codex exec` session (NO `resume`).
2. **Inputs.** Merged artifact + source roots + rulebook + 21-rule checklist.
3. **Forbidden inputs.** Prior authoring positions (`Claude-P<n>-*.md`, `Codex-P<n>-*.md`), prior pass files (any iteration), any session resume.
4. **Procedure.** Walk the rulebook checklist against the artifact. For each failing check that's mechanically fixable → emit a patch. For each that isn't → emit a Blocked entry. Re-walk source inventory for missing flows / scenarios. Re-validate every `file:line` ref. Identify ungrounded claims.
5. **Output.** Pass file with frontmatter `Status: CLEAN | PATCHED | BLOCKED` plus structured `## Patches` and `## Blocked` sections.

## Patch System

### Schema

```yaml
patch:
  patch_id: <uuid>
  operation: ADD-FLOW | ADD-SCENARIO | CORRECT-REF | STRENGTHEN
           | REMOVE-FLOW | REMOVE-SCENARIO | REMOVE-CLAIM | LATE-SERVICE-GAP
  target_kind: flow | scenario | field
  target_id: <flow-id> | <flow-id>.<scenario-name>
  field: <field-name>                # only for STRENGTHEN / CORRECT-REF
  operation_family: add | remove | correct | strengthen | gap
  precondition_hash: <hash of target state before patch>
  proposed_value: <type-dependent payload>
  evidence_refs: [<file:line>]
  depends_on: [<patch_id>]
  supersedes: [<patch_id>]
```

Merge key: `(target_kind, target_id, field, operation_family)`.

### Apply pipeline

1. Normalize artifact to AST (markdown is OUTPUT, NOT merge substrate).
2. Group patches by merge key.
3. Apply in deterministic order: **REMOVE → CORRECT-REF → ADD → STRENGTHEN → format-only**.
4. Run validators after every batch (including `$CHECK_REFS_ABS`).
5. Re-emit markdown from AST.

### Conflict resolution

| Conflict | Resolution |
|---|---|
| Same target, same value | Dedupe. |
| Same target, different values | Mini-duo (narrow scope). |
| ADD vs REMOVE on same target | Mini-duo over full dependent patch cluster. |
| Dependency on a removed target | Drop dependent patch and log, unless mini-duo keeps the target. |
| Semantic duplicate (different IDs, same trigger/entry/evidence) | Mini-duo. |
| Precondition hash mismatch | Rebase patch against latest artifact; non-mechanical → mini-duo. |

### Tie-breaker mini-duo

Narrow scope. Inputs: latest merged artifact + the conflicting patch cluster + source refs + rulebook. Authoring position files are NOT visible to the tie-breaker unless the conflict is explicitly about provenance. Single round. Output is authoritative for the current iteration's merge.

## Status Schema

Agent-written (authoring phase position files, P2/P4/P6):

| Status | Meaning |
|---|---|
| `EXTRACTED` | P2 or P4 author position — flow list extracted from source. |
| `WRITTEN` | P6 author position — per-flow test plan drafted. |

These are non-gating statuses: the orchestrator union-merges the two peer positions into a merged artifact regardless of EXTRACTED / WRITTEN content.

Agent-written (refinement pass, P3/P5/P7):

| Status | Meaning |
|---|---|
| `CLEAN` | Pass found nothing to fix. |
| `PATCHED` | Pass emitted structured patches. |
| `BLOCKED` | Pass cannot fix within skill scope; surfaces unresolved. |

Orchestrator-synthetic (on dispatch / parse failure):

| Status | Meaning |
|---|---|
| `INCONCLUSIVE` | File invalid (timeout, crash, malformed frontmatter, unparsable patches). |
| `UNAVAILABLE` | Dispatch never completed (failed launch, hard ceiling). |
| `INVALID` | File exists but fails schema validation. |

Merged artifact:

| Status | Meaning |
|---|---|
| `READY` | Post-merge, awaiting refinement. |
| `GATE-PASSED` | Refinement iteration was all-CLEAN. |
| `DEGRADED-CONTINUE` | Soft budget exhausted with non-blocking unresolved; downstream may consume with `## Unresolved` carried forward. |
| `BLOCKED` | Soft budget exhausted with blocking unresolved; downstream may NOT consume; appears only in `Result.md`. |

All-CLEAN exit requires valid CLEAN from every expected pass. A synthetic-status pass requires one retry within mission budget; if retry also fails, peer-attestation drives the artifact to DEGRADED-CONTINUE or BLOCKED.

## Streaming and Gates

P3 emits two readiness bits independently:

- `local_flows_ready` — local flows extraction is gate-resolved; downstream P6 may dispatch for this service.
- `seam_index_ready` — service's seam contribution is trustworthy; P4 may consume.

Downstream behavior:

- P4 waits for `seam_index_ready` from ALL services (or per-service DEGRADED-CONTINUE / BLOCKED terminal state — both unblock P4).
- P6 streams on per-service `local_flows_ready` OR per-service DEGRADED-CONTINUE. BLOCKED services do NOT stream into P6.
- P6 cross-app flows fire on P5 `GATE-PASSED` OR `DEGRADED-CONTINUE`. BLOCKED cross-app does NOT trigger cross-app P6.

`LATE-SERVICE-GAP` from P4/P5 reopens a specific service artifact. The orchestrator:

- Restarts P2 → P3 for the affected service.
- Enqueues required downstream P6/P7 for the gap.
- Preserves finalized work on unaffected services and unaffected cross-app flows.
- Tracks open LATE-SERVICE-GAP patches in the journal; P8 cannot complete while any are open.

## Mission Journal

`.codex/journal.jsonl` — append-only, one JSON object per line. Required event types:

| Event | Fields | When |
|---|---|---|
| `phase_start` | `phase`, `ts` | Before any phase artifact write |
| `dispatch_start` | `phase`, `unit`, `iter` (if refinement), `pass` (if refinement), `prompt_path`, `expected_output_path` | Before each codex / Task dispatch |
| `artifact_accepted` | `path`, `status` | After orchestrator validates a position or pass file |
| `artifact_rejected` | `path`, `reason` | After orchestrator rejects (INCONCLUSIVE / INVALID) |
| `patch_applied` | `patch_id`, `target_id`, `before_hash`, `after_hash` | After each patch merged into artifact |
| `gate_resolved` | `unit`, `gate`, `state` | After `local_flows_ready` / `seam_index_ready` / refinement-clean |
| `late_service_gap_opened` | `gap_id`, `affected_unit` | When P4/P5 emits LATE-SERVICE-GAP |
| `late_service_gap_closed` | `gap_id` | When affected unit re-completes through P3/P5 |
| `phase_complete` | `phase`, `counts` | At phase exit |
| `mission_halted` | `reason` | On ceiling exceeded or fatal failure |

On harness restart, orchestrator reads journal tail to determine resume point. No artifact write proceeds without a preceding journal record. Authoring sessions (`.codex/session-P<n>-<unit>`) are retained for retry-only resume from mid-cycle interruption; they are NOT used for cross-phase resume.

## Concurrency, Budget, Ceilings

| Setting | Default | Override prose |
|---|---|---|
| Concurrent Claude Task subagents | 4 | `high-concurrency` → 8; `very-high-concurrency` → 16 |
| Concurrent Codex sessions | 4 | `high-concurrency` → 8; `very-high-concurrency` → 16 |
| Refinement passes per iteration (N) | 2 | `refine-passes=N` |
| Max refinement iterations (M) | no hard cap | soft warning at 3; escalation handshake at 5 |
| Per-invocation hard ceiling | 20 min | — |
| Total mission ceiling | 90 min | `extended-budget` → 180 min |
| Dispatch budget soft warning | 80 Codex invocations | — |
| Adaptive throttle trigger | 2 rate-limit failures in rolling window | — |

Refinement passes share the concurrency cap with authoring duos. Orchestrator runs a semaphore-style dispatch queue; on every background-completion notification, dequeue the next ready unit.

**Refinement-priority hint.** When a per-unit completion notification arrives AND that unit's refinement is pending dispatch AND another unit's authoring is also queued, prefer the refinement to prevent streaming starvation (P7 should not be perpetually delayed by additional P6 dispatches).

Budget estimator (P1 output):

- Authoring Codex calls: `service_units + 1_crossapp + flow_count`
- Refinement Codex calls: `refine_passes × est_iterations × (service_units + 1_crossapp + flow_count)`
- Tiebreakers and retries: tracked separately.

If estimate exceeds 80 Codex invocations in default mode, prompt the user with the estimate before continuing. In autonomous mode, log and continue. Estimate recorded in `Result.md` header and `.codex/dispatch-budget.json`.

Adaptive throttle: if 2 Codex dispatches fail with rate-limit / usage / timeout symptoms in a rolling 5-minute window, halve Codex concurrency for the remainder of the mission and journal the change. No automatic restoration.

## Failure Modes

| Failure | Behavior |
|---|---|
| Codex dispatch fails (authoring P2/P4/P6) | Use Claude-only position; flag in merged artifact. Refinement still runs on the partial merge. |
| Codex dispatch fails (refinement P3/P5/P7) | Pass marked `INCONCLUSIVE`. Iteration cannot exit CLEAN. Retry once within budget; then peer-attest DEGRADED-CONTINUE or BLOCKED. |
| Pass times out (>20 min) | Pass marked `INCONCLUSIVE`. Same handling. |
| Refinement soft warning (iter 3) | Logged; continue. |
| Refinement escalation handshake (iter 5) | Default mode: USER-TIER if both peers attest no progress. Autonomous: peer-attested DEGRADED-CONTINUE or BLOCKED. No hard cap. |
| Patch conflict | Routed per Conflict Resolution table to mini-duo or auto-resolved. |
| Precondition hash mismatch | Rebase against current artifact; non-mechanical → mini-duo. |
| LATE-SERVICE-GAP from P4/P5 | Reopen affected service; preserve unaffected work; tracked in journal. |
| Unit DEGRADED-CONTINUE | Downstream consumes with `## Unresolved` carried forward; per-flow files emitted with explicit Unresolved sections. |
| Unit BLOCKED | Downstream does NOT consume. Per-flow files for BLOCKED units are NOT emitted; only `Result.md` summarizes. |
| Adaptive throttle triggered | Halve Codex concurrency; journal; continue. |
| Mission ceiling exceeded | Halt; structured summary; partial `test-plan/` preserved; journal `mission_halted`. |
| Late-gap queue non-empty at P8 | P8 cannot complete; either continue refinement or escalate per failure flow. |

## Signaling - DO NOT POLL

Launch every dispatch via Bash with `run_in_background: true`. The harness notifies on background completion.

Claude MUST NOT:
- Poll stream files with sleep loops
- Repeatedly check whether an expected output file exists
- Use mtime-checking loops
- Spawn watcher scripts

Launch the dispatch, continue Claude's own parallel work (authoring the Claude-side position, queueing the next ready unit, updating the manifest), STOP when Claude's side of the unit is complete. The next message is either the harness's bg-completion notification or a user interruption. On notification, validate the expected output path and proceed.

The dispatch script's internal `monitor_once()` loop is allowed — it runs inside the background process, consumes zero Claude tokens, and enforces the 20-minute per-invocation ceiling.

## Prompt File Authorship

Before any Codex dispatch, the skill body writes the full prompt to `.codex/<unit-key>-prompt.txt` using Claude's `Write` tool. The dispatch script does NOT write the prompt; it validates the prompt file is non-empty and pipes it to codex stdin.

Per-phase prompt content:

| Phase | Prompt includes |
|---|---|
| P2 (author) | Unit manifest slice, rulebook reference, position-file format, output path |
| P3/P5/P7 (refine) | Merged artifact path, source roots, rulebook reference, 21-rule checklist, patch grammar, pass-file format, output path. NO authoring position references. |
| P4 (author) | All gate-resolved service extraction artifacts, seam-discovery target list, output path |
| P6 (author) | Single flow's gate-resolved extraction record, source roots, rulebook reference, page-shape reference, output path |

Every prompt names the exact output file path. Every prompt for a refinement pass instructs the agent to ignore authoring artifacts even if visible.

## Codex Dispatch

Set env vars before invoking. The dispatch script handles fresh vs resume based on `SESSION_FILE` presence. Authoring phases (P2/P4/P6) persist sessions; refinement phases (P3/P5/P7) always pass `SESSION_FILE=/dev/null` (or unset path) to force a fresh dispatch.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?TestPlan}"
UNIT_KEY="${UNIT_KEY:?unit identifier, e.g. P2-customers-service or P3-customers-service-iter01-pass01}"
PROMPT_FILE="${PROMPT_FILE:?absolute prompt path}"
CODEX_OUT="${CODEX_OUT:?absolute codex output path}"
SESSION_FILE="${SESSION_FILE:-$MISSION/.codex/session-$UNIT_KEY}"
FRESH_ONLY="${FRESH_ONLY:-0}"
WEB_SEARCH="${WEB_SEARCH:-off}"

mkdir -p "$MISSION/.codex"

STREAM="$MISSION/.codex/$UNIT_KEY-stream.jsonl"
FINAL_CAPTURE="$MISSION/.codex/$UNIT_KEY-final.txt"
STDERR_LOG="$MISSION/.codex/$UNIT_KEY-stderr.log"
HISTORY_FILE="$MISSION/.codex/session-history"
LAUNCH_EPOCH="$(date +%s)"

if [[ ! -s "$PROMPT_FILE" ]]; then
  cat > "$CODEX_OUT" <<EOF
---
Artifact-Kind: dispatch-failure
Schema-Version: 1
Unit: $UNIT_KEY
Status: UNAVAILABLE
---
# $KIND - $UNIT_KEY (Codex unavailable)

## Reason
Prompt file missing or empty: $PROMPT_FILE.
EOF
  exit 2
fi

mtime_epoch() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }

CODEX_FLAGS=(
  --dangerously-bypass-approvals-and-sandbox
  -m gpt-5.5
  -c 'model_reasoning_effort="xhigh"'
  -c "web_search=\"$WEB_SEARCH\""
  --skip-git-repo-check
  --json
  --output-last-message "$FINAL_CAPTURE"
  -C "$CWD"
)

run_once() {
  : > "$STREAM"
  : > "$STDERR_LOG"
  if [[ "$FRESH_ONLY" != "1" ]]; then
    rm -f "$SESSION_FILE.new"
  fi
  "${CMD[@]}" < "$PROMPT_FILE" 2>>"$STDERR_LOG" | while IFS= read -r line; do
    printf '%s\n' "$line" >> "$STREAM"
    if [[ "$FRESH_ONLY" != "1" ]]; then
      if [[ "$line" =~ \"type\":\"thread.started\" ]] && [[ "$line" =~ \"thread_id\":\"([^\"]+)\" ]]; then
        printf '%s\n' "${BASH_REMATCH[1]}" > "$SESSION_FILE.new"
      fi
    fi
  done
  return "${PIPESTATUS[0]}"
}

monitor_once() {
  local liveness_done=0
  local stalled=0
  run_once &
  local pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    local now
    now="$(date +%s)"
    if (( now - LAUNCH_EPOCH >= 600 && liveness_done == 0 )); then
      liveness_done=1
      if [[ ! -e "$CODEX_OUT" ]]; then
        printf '%s\n' "No $CODEX_OUT after 10 minutes." >> "$STDERR_LOG"
      else
        local om
        om="$(mtime_epoch "$CODEX_OUT")"
        if (( now - om >= 600 )); then
          printf '%s\n' "$CODEX_OUT mtime has not advanced by the 10-minute liveness check." >> "$STDERR_LOG"
        fi
      fi
    fi
    if (( now - LAUNCH_EPOCH >= 1200 )); then
      stalled=1
      printf '%s\n' "Codex hard ceiling reached at 20 minutes; terminating dispatch." >> "$STDERR_LOG"
      kill "$pid" 2>/dev/null || true
      sleep 2
      kill -9 "$pid" 2>/dev/null || true
      break
    fi
    sleep 30
  done
  wait "$pid"
  RUN_STATUS=$?
  RUN_STALLED=$stalled
  if [[ "$FRESH_ONLY" != "1" && -s "$SESSION_FILE.new" ]]; then
    mv "$SESSION_FILE.new" "$SESSION_FILE"
  elif [[ "$FRESH_ONLY" == "1" ]]; then
    rm -f "$SESSION_FILE.new"
  fi
}

# Refinement passes (P3/P5/P7) MUST set FRESH_ONLY=1 to forbid session resume.
# Flag ordering: all flags BEFORE `resume <session> -`. codex 0.130.0 rejects -C after the session id.
if [[ "$FRESH_ONLY" != "1" && -s "$SESSION_FILE" ]]; then
  SESSION_ID="$(tr -d '\r\n' < "$SESSION_FILE")"
  CMD=(codex exec "${CODEX_FLAGS[@]}" resume "$SESSION_ID" -)
  MODE="resume"
else
  CMD=(codex exec "${CODEX_FLAGS[@]}" -)
  MODE="fresh"
fi

monitor_once

if [[ "$MODE" == "resume" && "${RUN_STATUS:-1}" -ne 0 && "${RUN_STALLED:-0}" -eq 0 ]]; then
  OLD_SESSION="$SESSION_ID"
  printf '%s resume failed for %s with status %s\n' \
    "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$OLD_SESSION" "$RUN_STATUS" >> "$HISTORY_FILE"
  FALLBACK_PROMPT="$MISSION/.codex/$UNIT_KEY-prompt-fallback.txt"
  {
    cat "$PROMPT_FILE"
    printf '\n\n# Resume failed; this run is fresh.\n'
  } > "$FALLBACK_PROMPT"
  PROMPT_FILE="$FALLBACK_PROMPT"
  CMD=(codex exec "${CODEX_FLAGS[@]}" -)
  MODE="fresh-after-resume-failure"
  LAUNCH_EPOCH="$(date +%s)"
  monitor_once
fi

valid=0
if [[ -f "$CODEX_OUT" ]]; then
  size="$(wc -c < "$CODEX_OUT" | tr -d ' ')"
  om="$(mtime_epoch "$CODEX_OUT")"
  if (( size > 500 && om >= LAUNCH_EPOCH )); then valid=1; fi
fi

if (( valid == 0 )); then
  cat > "$CODEX_OUT" <<EOF
---
Artifact-Kind: dispatch-failure
Schema-Version: 1
Unit: $UNIT_KEY
Status: UNAVAILABLE
---
# $KIND - $UNIT_KEY (Codex unavailable)

## Reason
Codex dispatch did not produce a valid output. See $STREAM, $FINAL_CAPTURE, $STDERR_LOG.

## Dispatch Metadata
- Mode: $MODE
- Status: ${RUN_STATUS:-unknown}
- Stalled: ${RUN_STALLED:-unknown}
EOF
fi
```

## Convergence

This skill has TWO distinct "convergence" semantics — both follow the yd convention of first-AGREED-pair, no confirmation round.

**Authoring phases (P2/P4/P6) — no peer convergence.** Claude and Codex independently author. Orchestrator union-merges. Convergence is implicit (union, not agreement). Disagreements become refinement-phase work.

**Refinement phases (P3/P5/P7) — iteration-exit on all-CLEAN.** When every pass in an iteration reports `CLEAN`, the iteration exits with `GATE-PASSED`. No confirmation iteration. If any pass is non-CLEAN, the iteration counts as PATCHED (or BLOCKED if any pass blocks) and a new iteration runs.

Same substantive unresolved item persisting iteration 5 → USER-TIER (default) or peer-attested DEGRADED-CONTINUE / BLOCKED (autonomous).

## Self-Review

Before each dispatch:

1. Prompt file exists at the named path and is non-empty.
2. Output path under `Duo/TestPlan-<slug>/` matches the naming convention.
3. Refinement dispatches set `FRESH_ONLY=1`; authoring dispatches do not.
4. Journal `dispatch_start` record appended.

Before P8 finalization:

1. Coverage matrix complete: every entrypoint maps to flow OR exclusion.
2. `$CHECK_REFS_ABS` (absolute path resolved at activation) passes on the entire `test-plan/**/*.md` tree.
3. Late-gap queue empty.
4. No artifact in the mission folder has `Status: INCONCLUSIVE` or `Status: INVALID` without a downstream peer-attested resolution.
5. All open `phase_start` journal events have corresponding `phase_complete` records.

Fix issues inline. No second review.

## User Feedback

Default mode:
- Ask the user only for USER-TIER blockers (refinement iteration 5 escalation handshake without peer-attested progress) and budget-warning approval (estimate exceeds 80 Codex invocations).
- Present concise options with consequences.
- Do not ask the user to resolve ordinary refinement disagreements.

Autonomous mode:
- No USER-TIER blocks. Resolve through convergence + peer-attested DEGRADED-CONTINUE / BLOCKED.
- Log unresolved outcomes in `Result.md`.

At the end:
- Present `Result.md` as a clickable link.
- Approve → done. Editorial → Edit inline. Substantive → re-enter refinement on the affected units.

## Hard Rules

- Direct Codex CLI only — no `/codex:rescue`, no plugin internals.
- Every Codex invocation: `gpt-5.5`, `model_reasoning_effort="xhigh"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `-C "$CWD"`.
- `web_search` is `"off"` by default. Flip to `"live"` only when prose contains `web-allowed`.
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`. codex 0.130.0 rejects `-C` placed after the session id.
- Never lower `model_reasoning_effort` below `medium`. Pin `xhigh`.
- **Authoring sessions (P2/P4/P6) persist as `.codex/session-*`; may be resumed only for retry from mid-cycle interruption, NOT for cross-phase work.**
- **Refinement passes (P3/P5/P7) ALWAYS launch FRESH (`FRESH_ONLY=1`) — no session resume. A pass that inherits authoring context invalidates the iteration.**
- **Refinement passes never see authoring position files.** Inputs limited to merged artifact + source + rulebook + checklist.
- Code is the only source of truth — do NOT read existing markdown, READMEs, or tests.
- Mission journal pre-write: every disk write recorded BEFORE the write.
- Claude never polls — wait for harness bg-completion notification.
- Orchestrator reads only `Status:` headers for control flow, never bodies.
- DEGRADED-CONTINUE units log unresolved; downstream consumes.
- BLOCKED units do NOT emit per-flow files; appear only in `Result.md`.
- No hard iteration cap. Soft warning at iter 3, escalation handshake at iter 5.
- Convergence is first-iteration all-CLEAN. No confirmation iteration.
- No user questions in autonomous mode.
- Root contains only position files + merged artifacts + `Result.md` + `test-plan/`; scratch stays in `.codex/`.

## File Reading Limits

- Use Glob / Grep before broad Read.
- Max 5 files per parallel Read batch.
- Range-read source files > 300 lines.
- Read the linked-testplan rulebook and references selectively per phase.
- Cite `file:line` for every claim in authoring + refinement output.
