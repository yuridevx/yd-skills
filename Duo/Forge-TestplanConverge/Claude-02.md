# Forge - Round 02 (Claude, mutual revision)

## Status vs peer's Round 01

DISAGREEMENTS_REMAIN — minor, expected to resolve this round.

## Agreements added since my Round 01

- **`web_search="disabled"` not `"off"`** — Codex is right; `disabled` is the actual codex CLI accepted value per `s:/yd-skills/skills/duo-testplan-build/SKILL.md:44`. Adopting in the updated draft.
- **Failure Modes table** — Codex-01 added a structured failure-modes table (line 587-603) covering broken paths, dispatch failures, timeouts, malformed outputs, cap-hit, phase-specific blocks. Useful; keeping verbatim.
- **Terminal state schema** — Codex-01 added AGREED / DEGRADED-CONTINUE / BLOCKED / UNAVAILABLE explicit states (line 528-535). Cleaner than my implicit handling; keeping.
- **`CODEX_OUT` as explicit env var** — Codex's pattern (caller supplies `CODEX_OUT` rather than deriving from round number) is more flexible. Adopting.
- **`field_resolved`/`field_disputed` journal events** — Codex added per-field resolution journal events (line 149-150) above my unit-level granularity. Better for resume semantics; keeping.

## Disagreements with peer's Round 01

- **Autonomous mode required vs supported** — Codex-01 line 47 says "If autonomous mode is absent, do not start the mission; ask for an autonomous re-invocation." This makes autonomous a hard precondition. The user's instruction was "the new skill should also support autonomously" — `support`, not `require`. Other yd duo skills (e.g. `s:/yd-skills/skills/duo-design/SKILL.md:14-17`) support autonomous as an opt-in mode and allow default mode with one clarifying question. My position: support autonomous (detect via prose triggers); default mode is allowed and may ask at most one clarifying question for USER-TIER blockers. Will resolve in updated draft.

## Withdrawals from my Round 01

- **My `web_search="off"`** — withdrawn in favor of Codex's `"disabled"`.
- **Round-derived `CODEX_OUT` path** — withdrawn in favor of Codex's explicit `CODEX_OUT` env var.
- **Implicit terminal states** — withdrawn in favor of Codex's explicit schema.

## New issues raised

None.

## Verdict (current)

CREATE.

## Updated draft

```markdown
---
name: duo-testplan-converge
description: Symmetric Claude+Codex convergent authoring of an e2e test plan tree for multi-repo workspaces using per-unit duo authoring plus step-by-step structured diff convergence. Six phases - P1a scope file discovery, P1b per-service scope, P2 local flow refinement, P3 cross-app discovery, P4 cross-app flow refinement, P5 result + check-refs.py. Each unit runs a per-unit Claude subagent that owns the convergence cycle and resumes one codex session across all rounds within the unit. Round cap 4 by default, user can extend via `extended-convergence`. At cap with residual disputes the artifact commits with [disputed:] tags - no separate resolver dispatch. Both peers author every unit, every phase. Code is the only source of truth - existing tests, READMEs, and documentation are excluded inputs. Consumes the `linked-testplan` rulebook AS IS (page shape, coverage vocabulary, scenario policy, mocks policy, 21-rule checklist). Produces `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow>.md` and `test-plan/cross-app/flows/<flow>.md`. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh + yolo. Web search disabled by default (source is truth); flip with `web-allowed`. Scripts run ONLY at P5 (`check-refs.py`); NEVER in the LLM convergence loop. SUPPORTS autonomous mode (prose `autonomously`/`no questions`/`hands-free`/`auto`/`unattended`) and default mode (one clarifying question max for USER-TIER blockers). TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo testplan-converge X", "duo-testplan-converge X", "/duo-testplan-converge X", "duo build a convergent test plan for X". Does NOT auto-activate on plain "test plan X" / "generate tests for X" / "e2e plan" requests.
---

# Duo Testplan Converge

Run a 6-phase, per-unit Claude+Codex convergence pipeline that writes an e2e test plan tree. Every phase uses the same unit protocol: both peers author, both peers diff by field, the per-unit Claude subagent deterministically merges resolved fields, and unresolved fields continue until first-AGREED-pair or the round cap.

The companion `linked-testplan` rulebook (sibling skill) is consumed AS IS. The main Claude session is a thin top-level coordinator; per-unit Claude subagents own the convergence cycle.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

### Trigger

Trigger only on explicit `duo` phrasing: `duo testplan-converge X`, `duo-testplan-converge X`, `/duo-testplan-converge X`, `duo build a convergent test plan for X`. Does NOT auto-activate on plain `test plan X` / `e2e plan` / `generate tests for X` / `write tests for X`.

### Mode

Detect autonomous mode when prose contains a clear execution phrase: `autonomously`, `no questions`, `hands-free`, `auto`, or `unattended`. Distinguish from topic adjectives ("design an autonomous robot" is topic, not mode). In autonomous mode: never call `AskUserQuestion`; USER-TIER blockers and residual disputes resolve to `[disputed: claude=..., codex=...]` tags or peer-attested DEGRADED-CONTINUE/BLOCKED outcomes logged in `Result.md → Unresolved`.

Default mode: may ask at most one clarifying question if the mission goal is too ambiguous to start. USER-TIER blockers surface in plain prose with `(a)/(b)/(c)` labels only after both sides have exhausted investigation.

### Modifiers (prose-detected)

| Modifier | Effect |
|---|---|
| `high-concurrency` | Shared P1b/P2/P4 cap 8 → 16. |
| `very-high-concurrency` | Shared P1b/P2/P4 cap → 32. |
| `extended-convergence` | Remove default round cap; soft warning at +2 over default per unresolved unit. |
| `web-allowed` | Codex `web_search` `disabled` → `live`. |

### Filter and Slug

Free-form repo filter in prose: `only ingestion-service`, `work on X and Y`. Empty filter → all discovered repos.

Mint a 2-5 PascalCase slug from prose (e.g. `Petclinic`, `OrdersFlow`). If the user names an existing `Duo/TestPlan-<slug>/`, resume from `.codex/journal.jsonl`.

## Plugin Layout and Path Resolution

This skill ships in the `yd` plugin alongside the `linked-testplan` rulebook (sibling skill) and `scripts/check-refs.py` (validator at the plugin root). The main session's CWD is the mission target workspace, NOT the plugin install dir — so plugin-relative paths must be resolved to absolute paths before being passed to dispatched subagents and codex sessions.

At skill activation, resolve once and reuse for the mission:

- `PLUGIN_ROOT` — derived from the skill's base directory. Compute `PLUGIN_ROOT = <skill base>/../..`.
- `RULEBOOK_ABS` = `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`
- `RULEBOOK_REFS_ABS` = `$PLUGIN_ROOT/skills/linked-testplan/references/`
- `CHECK_REFS_ABS` = `$PLUGIN_ROOT/scripts/check-refs.py`

Pass these ABSOLUTE paths in every dispatched prompt. Self-test on first run: verify `RULEBOOK_ABS` and `CHECK_REFS_ABS` exist and are readable. Halt on broken install. Pattern adapted from `s:/yd-skills/skills/duo-testplan-build/SKILL.md:12-25`.

## Mission Folder Layout

```
Duo/TestPlan-<slug>/
  Result.md                                    converged index (visible)
  test-plan/                                   final artifact tree (visible)
    <repo>/<svc>/flows/<flow-id>.md
    cross-app/flows/<flow-id>.md

  .codex/                                      ALL scratch / state / logs
    journal.jsonl                              append-only event log
    unit-manifest.json                         P1 aggregate output
    session-<unit-key>                         codex session id (one per unit)
    <unit-key>-rNN-prompt.txt                  per-round subagent-authored prompt
    <unit-key>-rNN-stream.jsonl                codex --json events
    <unit-key>-rNN-final.txt                   codex --output-last-message
    <unit-key>-rNN-stderr.log
    Author-Claude-<unit-key>.md                round 0 outputs
    Author-Codex-<unit-key>.md
    Diff-Claude-<unit-key>-rNN.md              round 1+ structured diffs
    Diff-Codex-<unit-key>-rNN.md
    Committed-<unit-key>.md                    final agreed artifact (subagent output)
```

Root contains only `Result.md` + `test-plan/`. All scratch/state/logs in `.codex/`.

## Discovery Toolbox

Source code is the only ground truth. Existing tests, READMEs, and documentation are excluded inputs at every phase.

1. Production source under each repo (per exclusion set below).
2. `RULEBOOK_ABS` and `RULEBOOK_REFS_ABS` (page shape, checklist, vocabulary, policies).
3. Mission journal at `.codex/journal.jsonl` for resume semantics.
4. Upstream committed artifacts (`.codex/Committed-*.md`) for downstream phases.
5. `.codex/unit-manifest.json` from P1.
6. Web only when `web-allowed` is in prose.

Exclusion set:

```
Tests:    **/*.{spec,test,e2e}.*, **/test/**, **/tests/**, **/__tests__/**, **/spec/**, **/e2e/**
Build:    **/dist/**, **/build/**, **/.next/**, **/coverage/**
Vendor:   **/node_modules/**, **/local-packages/**
VCS/IDE:  **/.git/**, **/.idea/**, **/.vscode/**
Docs:     **/*.md, **/*.pdf, **/*.txt, **/CHANGELOG*, **/README*
```

## Per-Unit Protocol

Every unit (P1a, each P1b service, each P2 flow, P3, each P4 cross-app flow, P5 sanity) uses the same protocol. The main session spawns one Claude subagent per unit. The subagent owns the full convergence cycle and exits with a committed artifact.

```
PER UNIT  (one Claude subagent)

  R0  AUTHOR (parallel)
        Subagent self-authors (Claude voice) → Author-Claude-<unit-key>.md
        Subagent spawns codex (NEW session per unit; codex session id captured to
          .codex/session-<unit-key>) → Author-Codex-<unit-key>.md

  R1..N DIFF (parallel, while round count < cap and disputes remain)
        Subagent self-diffs → Diff-Claude-<unit-key>-rNN.md
        Subagent dispatches codex via RESUME of same session → Diff-Codex-<unit-key>-rNN.md
        Subagent applies per-field merge table (deterministic; not LLM)
        Journal field_resolved or field_disputed per field
        If all fields resolved → exit, COMMIT (AGREED)
        If round count == cap → commit fields where peers agreed;
                                tag remaining with [disputed:];
                                journal cap_hit; COMMIT (AGREED if zero disputes,
                                DEGRADED-CONTINUE if some, BLOCKED if all disputed)

  COMMIT
        Subagent writes Committed-<unit-key>.md.
        Subagent exits; main session receives bg-completion notification.
```

Round cap default: R0 + 4 diff rounds. `extended-convergence` removes cap; soft warning every 2 extra diff rounds. P3 cross-app discovery defaults to 1-round cap (enumerative).

## Per-Field Merge Table

Both peers emit a structured per-field stance in each diff round. The subagent (deterministic logic, not LLM) applies this table.

Field stance enum: `keep | drop | replace <value> | augment <addition> | dispute`.

Diff field shape (YAML-like):

```yaml
field_id: <stable id>
stance: keep | drop | replace | augment | dispute
value: <replacement or augmentation, if any>
evidence:
  - <path>:<line>
reason: <terse source-grounded rationale>
```

Merge table:

| Claude stance | Codex stance | Outcome |
|---|---|---|
| `keep` | `keep` | Commit field as-is |
| `drop` | `drop` | Drop field |
| `augment a` | `augment b` | Commit + union(a, b) preserving citations |
| `replace x` | `replace x` | Commit replacement x |
| `keep` | `augment a` | Commit + a |
| `augment a` | `keep` | Commit + a |
| `keep` | `drop` | Unresolved → next round |
| `keep` | `replace x` | Unresolved → next round |
| `drop` | `replace x` | Unresolved → next round |
| `augment a` | `replace x` | Unresolved → next round |
| `augment a` | `drop` | Unresolved → next round |
| `replace x` | `replace y` (x≠y) | Unresolved → next round |
| any | `dispute` | Unresolved → next round |
| `dispute` | `dispute` | Unresolved; mark for at-cap-tagging |

Normalization is conservative: trim whitespace, normalize unordered-list ordering only when the field is explicitly unordered. Never collapse different file:line evidence.

## Codex Session Policy

Deliberate deviation from `duo-testplan-build`'s "refinement-passes-must-be-fresh" rule:

- **Within a unit:** codex session is NEW at R0, then RESUMED for every diff round R1..N.
- **Across units:** sessions never share. Each unit gets its own NEW codex cold-start at `.codex/session-<unit-key>`.
- **Across phases:** sessions never share. Same flow referenced by P2 and P4 → P4 dispatches a NEW codex session.

Rationale: codex new-session is the expensive operation; within-unit resume preserves codex's reasoning across rounds. Cross-unit and cross-phase freshness preserves convergence integrity.

## Concurrency

| Setting | Default | Override |
|---|---|---|
| Shared active per-unit subagents (P1b/P2/P4) | 8 | `high-concurrency` → 16; `very-high-concurrency` → 32 |
| Per-unit codex sessions | 1 | (none) |
| Per-unit round cap | R0 + 4 diff | `extended-convergence` removes cap |
| P3 discovery cap | 1 diff | `extended-convergence` extends |
| Per-codex-dispatch hard ceiling | 20 minutes | (none) |
| Web search | disabled | `web-allowed` → live |

Dispatch budget target for 5 services × 10 flows: ~290 floor / ~580 ceiling peer dispatches (Claude subagent spawns are cheap; codex new-sessions are the cost driver, bounded at one per unit).

## Phase 1 — Mission Setup

Main session does:

1. Parse trigger, mode, modifiers, filter, slug, `WEB_SEARCH`.
2. Create `Duo/TestPlan-<slug>/.codex/`.
3. Create or resume `.codex/journal.jsonl`.
4. Resolve and self-test `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, `CHECK_REFS_ABS`.
5. Append `phase_start` for P1a.

### Journal Events

| Event | Fields | When |
|---|---|---|
| `phase_start` | `phase`, `ts` | Before phase work starts |
| `subagent_spawn` | `phase`, `unit_key`, `cap_consumed` | Before Task() dispatch |
| `dispatch_start` | `phase`, `unit_key`, `round`, `prompt_path`, `expected_output_path` | Before each codex dispatch |
| `artifact_accepted` | `path`, `status` | After validating an output |
| `artifact_rejected` | `path`, `reason` | After rejecting malformed/stale output |
| `field_resolved` | `unit_key`, `round`, `field_id`, `resolution` | After deterministic merge commits a field |
| `field_disputed` | `unit_key`, `round`, `field_id`, `claude`, `codex` | When a field remains unresolved |
| `gate_resolved` | `phase`, `unit_key`, `state` (AGREED\|DEGRADED-CONTINUE\|BLOCKED\|UNAVAILABLE) | At unit terminal state |
| `cap_hit` | `unit_key`, `disputed_field_count` | When round cap reached with residuals |
| `phase_complete` | `phase`, `counts` | At phase exit |
| `mission_halted` | `reason` | On fatal failure |

On harness restart: read journal tail, resume pending units. Per-unit `.codex/session-<unit-key>` files persist.

### Terminal States

| State | Meaning |
|---|---|
| `AGREED` | All fields resolved before cap |
| `DEGRADED-CONTINUE` | Some fields tagged `[disputed:]` at cap; downstream may consume |
| `BLOCKED` | Unit cannot produce source-grounded artifact; downstream does not consume except Result.md summary |
| `UNAVAILABLE` | Dispatch failure; autonomous mode converts to DEGRADED-CONTINUE or BLOCKED based on Claude-side evidence |

## Phase-by-Phase Orchestration

### P1a — Scope File Discovery

Sequential first. One Claude subagent (unit key `P1a-scope`). Both peers walk workspace under `CWD`, apply exclusion set, classify production source vs tests/build/vendor/docs, identify repos (subdir with `.git/` or CWD if single) and services (`apps/<svc>/`, `services/<svc>/`, or top-level for monorepos).

Field set: `repos[]`, `services_per_repo`, `source_boundaries`, `exclusions_used`.

Commit: `.codex/Committed-P1a-scope.md`.

### P1b — Per-Service Scope

Parallel after P1a, one unit per `(repo, service)`. Unit keys: `P1b-<repo>-<svc>`. Subagent identifies candidate source roots, enumerates entrypoints (HTTP controllers, Kafka producers/consumers, gRPC servers/clients, cron, S3/DDB/SQL/Redis access), mints stable flow IDs per `s:/yd-skills/skills/linked-testplan/SKILL.md:147-148` (rule 11).

Field set: `candidate_roots[]`, `entrypoints[]` (each with `file`, `line`, `trigger_kind`, `trigger`), `flow_ids[]`.

Commit: `.codex/Committed-P1b-<repo>-<svc>.md`. Main session aggregates all P1b commits into `.codex/unit-manifest.json` (same schema as `s:/yd-skills/skills/duo-testplan-build/SKILL.md:159-183`).

### P2 — Local Flow Refinement

Parallel after all P1b complete. One unit per flow. Unit keys: `P2-<flow-id>`. Subagent reads flow's entry `file:line`, downstream call sites, related persistence/emission code, and `RULEBOOK_ABS`.

Field set (per linked-testplan page shape `s:/yd-skills/skills/linked-testplan/SKILL.md:38-80`):
- `flow_under_test` — trigger, entry `file:line`, brief
- `scenarios[]` — each with: name (HAPPY/NEGATIVE), preconditions (seeded/inbound/flag/external), steps, expected, mocks, code refs
- `code_refs[]` — flow-level supporting references

Commit: `.codex/Committed-P2-<flow-id>.md` → copy to `test-plan/<repo>/<svc>/flows/<flow-id>.md`.

### P3 — Cross-App Discovery

Sequential after every P2 unit. One subagent unit `P3-crossapp`. Reads all P2 commits + source; identifies cross-repo seams (Kafka producer/consumer in different repos, REST/gRPC server-client across repos, S3 writer-reader across repos).

Field set: `cross_app_flows[]` (each with `flow_id`, `participants`, `triggering_actor`, `seam_kind`). Cross-app flow IDs use `crossapp-*` prefix per `s:/yd-skills/skills/linked-testplan/SKILL.md:118-126`.

Default cap: 1 diff round. `extended-convergence` extends.

Commit: `.codex/Committed-P3-crossapp.md`.

### P4 — Cross-App Flow Refinement

Parallel after P3. One unit per cross-app flow. Unit keys: `P4-<flow-id>`. Subagent reuses producer-side and consumer-side P2 commits as converged facts; reads source only to validate or fill gaps.

Field set (per linked-testplan cross-app shape `s:/yd-skills/skills/linked-testplan/SKILL.md:78-80,118-126`): same as P2 plus actor-prefix Steps form (`<service> → <service>: <action>`); no internal-mutation steps across service boundaries.

Commit: `.codex/Committed-P4-<flow-id>.md` → copy to `test-plan/cross-app/flows/<flow-id>.md`.

### P5 — Result

Sequential final.

1. Main session writes `Result.md` (template below).
2. Spawn 1 Claude subagent (unit key `P5-sanity`) for cross-flow sanity sweep over the full `test-plan/` tree. Same per-unit protocol. Output: contradictions across flows (same topic with incompatible payloads, conflicting expected outcomes for shared deps).
3. Run `python "$CHECK_REFS_ABS"` over `test-plan/**/*.md` (ref validation).
4. Run `python "$CHECK_REFS_ABS" --manifest .codex/unit-manifest.json` (entrypoint coverage).
5. Fold check-refs failures and sanity findings into `Result.md → Unresolved`.
6. Append final `phase_complete` journal event.

`Result.md` template:

```markdown
# TestPlan Result — <slug>

## Summary
[1-3 sentence mission summary]

## Scope
- Repos: [list]
- Services: [list]
- Local flows: <count>
- Cross-app flows: <count>

## Coverage Matrix
| Entrypoint (file:line) | Flow ID | Status |
|---|---|---|
| ... | ... | covered / excluded |

## Convergence Counts
- P1a: <rounds_used>
- P1b: <avg> avg, <max> max
- P2: <avg> avg, <max> max
- P3: <rounds_used>
- P4: <avg> avg, <max> max
- P5-sanity: <rounds_used>

## Disputed Fields
- <unit-key> · <field_id> — claude: ... / codex: ...

## Exclusions
- <file:line> — <reason>

## Unresolved
- [disputed: ...] inventory, check-refs.py failures, DEGRADED-CONTINUE/BLOCKED units
```

## Signaling — DO NOT POLL

Every codex dispatch runs via Bash with `run_in_background: true`. Harness notifies on completion.

Subagent and main session MUST NOT:
- Poll stream files with sleep loops
- Repeatedly check whether output exists
- Use mtime loops
- Spawn watcher scripts

Subagent dispatches codex, works in parallel on its Claude-side authoring/diff, STOPS when its side is complete. Next message is harness's bg-completion notification or user interruption. On notification, validate codex output, apply merge table, decide commit-vs-next-round.

Main session likewise never polls subagents. Subagents spawned via Task(); main session receives completion notifications and advances phase state.

The dispatch script's internal `monitor_once()` is allowed (runs inside the background process, enforces 20-minute ceiling, consumes zero Claude tokens).

## Prompt File Authorship

Each per-unit subagent writes the full codex prompt before invoking dispatch:

```
$MISSION/.codex/<unit-key>-rNN-prompt.txt
```

Dispatch script validates non-empty and pipes to codex stdin. Dispatch script does NOT write prompts.

Every prompt includes:

- Mission path and CWD
- Absolute `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, `CHECK_REFS_ABS`
- Phase, unit key, round number, round cap, expected output path
- Source scope and upstream committed artifacts (for the phase)
- Exact output format: AUTHOR (R0) or structured DIFF (R1+) per the per-field merge schema
- Web policy (`disabled` or `live`)

## Codex Dispatch

Set env vars before invoking. Run via Bash with `run_in_background: true`.

Required env:
- `CWD` — absolute target workspace
- `MISSION` — absolute `Duo/TestPlan-<slug>` folder
- `KIND` — `TestPlanConverge`
- `UNIT_KEY` — path-safe stable unit key
- `ROUND` — unit-local round number starting at 0
- `PROMPT_FILE` — absolute prompt path
- `CODEX_OUT` — absolute expected codex output path
- `WEB_SEARCH` — `disabled` or `live`

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?TestPlanConverge}"
UNIT_KEY="${UNIT_KEY:?path-safe unit identifier}"
ROUND="${ROUND:?unit-local round number starting at 0}"
PROMPT_FILE="${PROMPT_FILE:?absolute prompt path}"
CODEX_OUT="${CODEX_OUT:?absolute codex output path}"
WEB_SEARCH="${WEB_SEARCH:-disabled}"
NN="$(printf "%02d" "$ROUND")"

mkdir -p "$MISSION/.codex"

STREAM="$MISSION/.codex/${UNIT_KEY}-r${NN}-stream.jsonl"
FINAL_CAPTURE="$MISSION/.codex/${UNIT_KEY}-r${NN}-final.txt"
STDERR_LOG="$MISSION/.codex/${UNIT_KEY}-r${NN}-stderr.log"
SESSION_FILE="$MISSION/.codex/session-$UNIT_KEY"
HISTORY_FILE="$MISSION/.codex/session-history"
LAUNCH_EPOCH="$(date +%s)"

if [[ ! -s "$PROMPT_FILE" ]]; then
  cat > "$CODEX_OUT" <<EOF
# $KIND - $UNIT_KEY round $NN (Codex unavailable)
## Status
UNAVAILABLE
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
  rm -f "$SESSION_FILE.new"
  "${CMD[@]}" < "$PROMPT_FILE" 2>>"$STDERR_LOG" | while IFS= read -r line; do
    printf '%s\n' "$line" >> "$STREAM"
    if [[ "$line" =~ \"type\":\"thread.started\" ]] && [[ "$line" =~ \"thread_id\":\"([^\"]+)\" ]]; then
      printf '%s\n' "${BASH_REMATCH[1]}" > "$SESSION_FILE.new"
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
  if [[ -s "$SESSION_FILE.new" ]]; then mv "$SESSION_FILE.new" "$SESSION_FILE"; fi
}

# Flag ordering CRITICAL: all flags BEFORE `resume <session> -`.
# codex 0.130.0 rejects -C placed AFTER the session id.
# Within-unit resume: R0 fresh; R1..N resume same session.
if [[ -s "$SESSION_FILE" ]]; then
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
  FALLBACK_PROMPT="$MISSION/.codex/${UNIT_KEY}-r${NN}-prompt-fallback.txt"
  {
    cat "$PROMPT_FILE"
    printf '\n\n# Resume failed; unit-local prior artifacts pasted for continuity.\n'
    find "$MISSION/.codex" -maxdepth 1 -type f -name "*${UNIT_KEY}*.md" | sort | while IFS= read -r f; do
      printf '\n\n## %s\n' "$f"
      sed -n '1,260p' "$f"
    done
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
# $KIND - $UNIT_KEY round $NN (Codex unavailable)
## Status
UNAVAILABLE
## Reason
Codex dispatch did not produce a valid output. See $STREAM, $FINAL_CAPTURE, $STDERR_LOG.
## Dispatch Metadata
- Mode: $MODE
- Status: ${RUN_STATUS:-unknown}
- Stalled: ${RUN_STALLED:-unknown}
EOF
fi
```

## Per-Unit Subagent Loop

For each unit:

1. Main session writes `subagent_spawn` and spawns the per-unit Claude subagent via `Task()`.
2. Subagent writes R0 prompt to `.codex/<unit-key>-r00-prompt.txt`.
3. Subagent launches codex R0 via the dispatch block; works in parallel on its Claude-side R0 author.
4. On bg-completion notification, subagent validates codex output path, then:
   - If R0: prepare R1 (write R1 prompt, dispatch codex R1 with resume; subagent self-diffs in parallel).
   - If R1+: apply per-field merge table; emit `field_resolved`/`field_disputed` events.
5. If unresolved fields remain and round count < cap, write next-round prompt and repeat (codex resumes same session).
6. On terminal state, subagent writes `Committed-<unit-key>.md`, emits `gate_resolved`, exits.

Main session advances phase gates only after all required units for the current phase reach terminal state.

## Convergence

Convergence = first round where deterministic field merge resolves every field with no remaining USER-TIER blocker. No confirmation round. Pattern: `s:/yd-skills/skills/duo-design/SKILL.md:280-287`.

## Self-Review

Before each codex dispatch:

1. Prompt file exists at named path and non-empty.
2. Output path matches naming convention.
3. Session file presence consistent with round (R0 may be fresh or resume; R1+ resume).
4. Journal `dispatch_start` record appended.

Before P5 finalization:

1. Coverage matrix complete: every entrypoint maps to flow OR exclusion.
2. `$CHECK_REFS_ABS` passes on `test-plan/**/*.md`.
3. No unit has terminal `UNAVAILABLE` without peer-attested DEGRADED-CONTINUE/BLOCKED resolution.
4. All open `phase_start` events have matching `phase_complete`.
5. Root contains only `Result.md` + `test-plan/`.

Fix issues inline. No second review.

## User Feedback

Default mode:
- Ask the user only for USER-TIER blockers (rare; reserved for cases where a `[disputed:]` field is so foundational the rest of the artifact is invalid) and budget approval if estimated dispatch count exceeds 800.
- Do not ask the user to resolve ordinary `[disputed:]` fields.

Autonomous mode:
- No USER-TIER blocks. Resolve through `[disputed:]` tags and peer-attested DEGRADED-CONTINUE/BLOCKED.
- Log unresolved outcomes in `Result.md`.

At the end:
- Present `Result.md` as a clickable link.
- Summarize: repos / services / local flows / cross-app flows / unit terminal counts / check-refs result / unresolved.
- Approve → done. Editorial → Edit inline. Substantive → reopen affected units (delete `Committed-<unit-key>.md`, re-dispatch).

## Failure Modes

| Failure | Behavior |
|---|---|
| Broken plugin paths | Halt before P1a writes artifacts. |
| Codex dispatch missing prompt | Write `UNAVAILABLE`; subagent decides DEGRADED-CONTINUE or BLOCKED from Claude-side evidence. |
| Codex timeout (>20 min) | Same as dispatch unavailable. |
| Malformed codex author/diff | Retry once in the same unit session if budget allows; then tag disputed fields. |
| Round cap reached | Commit with `[disputed: claude=..., codex=...]` per residual field. |
| P1a blocked | Halt; no downstream phase has source boundaries. |
| P1b service blocked | Exclude that service from P2; summarize in `Result.md`. |
| P2 flow blocked | Do not write that flow page; summarize in `Result.md`. |
| P3 blocked | Skip P4; summarize local-only coverage and unresolved cross-app discovery. |
| P4 cross-app flow blocked | Do not write that cross-app flow page; summarize in `Result.md`. |
| P5 check-refs fails | Fix source refs when evidence is clear; otherwise list failures in `## Unresolved`. |

## Hard Rules

- Direct Codex CLI only — no `/codex:rescue`, no plugin internals, no shared helper skill.
- Every Codex invocation: `gpt-5.5`, `model_reasoning_effort="xhigh"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `-C "$CWD"`.
- `web_search` is `"disabled"` by default. Flip to `"live"` only when prose contains `web-allowed`.
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`. codex 0.130.0 rejects `-C` after the session id.
- Never lower `model_reasoning_effort` below `medium`. Pin `xhigh`.
- **Codex sessions: NEW per unit at R0; RESUMED across rounds within the unit's lifecycle; never shared across units or phases.** Deliberate deviation from duo-testplan-build's all-fresh refinement rule.
- **Both peers author every unit, every phase.** No rotation, no asymmetry.
- **Main session is thin top-level coordinator.** Spawn per-unit subagents via Task(). Never run convergence rounds itself.
- **Per-unit Claude subagent owns its convergence cycle.** Self-authors at R0; self-diffs at R1+. The subagent IS the Claude-side voice.
- **Per-field merge table applied deterministically by the subagent (not LLM).**
- **Convergence is first-AGREED-pair.** No confirmation round.
- **At round cap with residual disputes:** commit fields where peers agreed, tag remaining `[disputed: claude=..., codex=...]`, journal `cap_hit`. No separate resolver dispatch.
- **Scripts: ONLY `$CHECK_REFS_ABS` at P5.** Never in the LLM convergence loop. No pre-converge filter, no per-phase validators, no script gatekeeping.
- **Code is the only source of truth** — do NOT read existing markdown, READMEs, or tests.
- Mission journal pre-write: every disk write recorded BEFORE the write.
- Claude never polls — wait for harness bg-completion notification.
- No user questions in autonomous mode.
- Root contains only `Result.md` + `test-plan/`; scratch stays in `.codex/`.
- One `.md` per flow in the final `test-plan/` tree.
- Shared concurrency cap 8 across P1b/P2/P4 (overridable via prose modifiers).
- Trigger ONLY on explicit `duo` keyword.

## File Reading Limits

- Glob/Grep before broad reads.
- Max 5 files per parallel Read batch.
- Range-read source files > 300 lines.
- Read `linked-testplan` rulebook once per unit; load references selectively.
- Cite `file:line` for every claim in author, diff, committed, and result artifacts.
- Do not read existing markdown, READMEs, generated docs, or tests as evidence for flow behavior.
```

## Open Questions

None at USER-TIER. Expected ALL_AGREED at R2.
