# Forge - Round 1 (Codex position)

## Investigation

- `duo-design` is the canonical symmetric duo pattern: prose-only invocation and autonomous-mode parsing are defined at `s:/yd-skills/skills/duo-design/SKILL.md:10-18`, scratch isolation at `s:/yd-skills/skills/duo-design/SKILL.md:20-36`, no-poll background dispatch at `s:/yd-skills/skills/duo-design/SKILL.md:70-83`, prompt-file authorship at `s:/yd-skills/skills/duo-design/SKILL.md:84-89`, and first-agreed/no-confirmation convergence at `s:/yd-skills/skills/duo-design/SKILL.md:280-287`.
- The new skill should adapt the `yd` plugin path-resolution pattern from `duo-testplan-build`: resolve plugin-relative rulebook and validator paths once, pass absolute paths into all dispatched prompts, and self-test readability before writing mission artifacts (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:12-25`).
- The existing `duo-testplan-build` trigger discipline, source-only discovery, source exclusions, journal schema, concurrency prose, failure-mode vocabulary, and dispatch wrapper are the closest reusable patterns (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:31-45`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:104-122`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:423-440`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:442-468`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:469-485`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:516-682`).
- `duo-testplan-build` is deliberately distinct: it is an 8-phase write/refine pipeline with independent fresh-dispatch refinement, while this proposed skill is a 6-phase per-unit duo author/diff convergence pipeline (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:6-10`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:124-134`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:684-692`).
- `linked-testplan` owns the page shape, coverage vocabulary, scenario policy, mocks policy, cross-app rules, 21-rule checklist, and `check-refs.py` contract. The new skill should consume it, not duplicate or modify it (`s:/yd-skills/skills/linked-testplan/SKILL.md:6-10`, `s:/yd-skills/skills/linked-testplan/SKILL.md:25-80`, `s:/yd-skills/skills/linked-testplan/SKILL.md:82-117`, `s:/yd-skills/skills/linked-testplan/SKILL.md:118-159`, `s:/yd-skills/skills/linked-testplan/SKILL.md:184-195`).

## Gating Evaluation

1. Pattern recurs across missions? YES - e2e test plan authoring across multi-repo and microservice workspaces is recurring.
2. Stable artifact shape? YES - `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow-id>.md` and `test-plan/cross-app/flows/<flow-id>.md`.
3. Definable investigation procedure? YES - scope discovery, per-service entrypoint probing, per-flow page refinement, cross-app seam correlation, and final reference validation.
4. Distinct from existing duo-*? YES - `duo-testplan-build` already exists but uses 8-phase union-merge plus N-pass refinement; this new skill uses 6-phase per-unit duo author plus structured diff convergence.

Verdict: CREATE.

## Draft (CREATE branch)

~~~~markdown
---
name: duo-testplan-converge
description: "Symmetric Claude+Codex convergent authoring of an e2e test plan tree for multi-repo workspaces using per-unit duo authoring plus step-by-step structured diff convergence. Produces `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow-id>.md` and `test-plan/cross-app/flows/<flow-id>.md`. Distinct from `duo-testplan-build`: this skill uses a 6-phase per-unit convergence protocol, not 8-phase union-merge plus fresh N-pass refinement. Direct codex CLI only - no /codex:rescue, no plugin internals, no shared helper skill; depends on `codex` on PATH. Pins gpt-5.5 + model_reasoning_effort=xhigh + yolo (`--dangerously-bypass-approvals-and-sandbox`) + `--json` + `--output-last-message` + `--skip-git-repo-check` + `-C $CWD`. Web search OFF by default because source code is ground truth; flip to live only with `web-allowed`. TRIGGERS ONLY on explicit `duo` phrasing such as `duo testplan-converge X`, `duo-testplan-converge X`, `/duo-testplan-converge X`, or `duo build a convergent test plan for X`. Does NOT auto-activate on plain `test plan X`, `e2e plan`, or `generate tests for X`. Autonomous mode is required: accepted prose includes `autonomously`, `no questions`, `hands-free`, `auto`, or `unattended`."
---

# Duo Testplan Converge

Run a 6-phase, per-unit Claude+Codex convergence pipeline that writes an e2e test plan tree. Every phase uses the same unit protocol: both peers author, both peers diff by field, the Claude subagent deterministically merges resolved fields, and unresolved fields continue until the first agreed pair or the round cap.

Pattern sources: trigger and autonomous handling adapt `duo-design` (`s:/yd-skills/skills/duo-design/SKILL.md:10-18`) and `duo-testplan-build` (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:31-45`). The page shape and checklist come from `linked-testplan` (`s:/yd-skills/skills/linked-testplan/SKILL.md:25-159`).

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

Trigger only on explicit `duo` phrasing:

- `duo testplan-converge X`
- `duo-testplan-converge X`
- `/duo-testplan-converge X`
- `duo build a convergent test plan for X`

Do not activate on plain `test plan X`, `e2e plan`, `generate tests for X`, or `write tests for X`.

Autonomous mode is required. Detect it only when prose contains a clear execution phrase: `autonomously`, `no questions`, `hands-free`, `auto`, or `unattended`. Distinguish execution mode from topic adjectives. If autonomous mode is absent, do not start the mission; ask for an autonomous re-invocation and list the accepted phrases.

In autonomous mode, never call `AskUserQuestion` and never pause for user input. USER-TIER blockers become peer-attested `DEGRADED-CONTINUE` or `BLOCKED` outcomes, with residual field disagreements committed as `[disputed: claude=..., codex=...]`.

Prose modifiers:

| Modifier | Effect |
|---|---|
| `high-concurrency` | Shared P1b/P2/P4 cap becomes 16. |
| `very-high-concurrency` | Shared P1b/P2/P4 cap becomes 32. |
| `extended-convergence` | Removes the default round cap; warn every 2 additional diff rounds per unresolved unit. |
| `web-allowed` | Codex `web_search` becomes `live`; otherwise use `disabled`. |

Mint a 2-5 word PascalCase slug from the prose. If the user names an existing `Duo/TestPlan-<slug>/`, resume from `.codex/journal.jsonl`; otherwise create it.

## Plugin Layout and Path Resolution

This skill ships in the `yd` plugin next to the passive `linked-testplan` rulebook and the root `scripts/check-refs.py` validator. The mission CWD is the target workspace, not the plugin install directory, so resolve plugin-relative paths once at activation and pass absolute paths to every Claude subagent and every Codex prompt.

At activation, resolve:

- `PLUGIN_ROOT`: two directories above this skill directory.
- `RULEBOOK_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`.
- `RULEBOOK_REFS_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/references/`.
- `CHECK_REFS_ABS`: `$PLUGIN_ROOT/scripts/check-refs.py`.

Before P1a writes anything, verify `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS` exist and are readable. Halt on broken install. Do not continue with placeholder paths.

Pattern source: adapted from the sibling testplan executor's path resolution contract (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:12-25`).

## Mission Folder Layout

```
Duo/TestPlan-<slug>/
  Result.md
  test-plan/
    <repo>/<svc>/flows/<flow-id>.md
    cross-app/flows/<flow-id>.md
  .codex/
    unit-manifest.json
    journal.jsonl
    session-<unit-key>
    <unit-key>-rNN-prompt.txt
    <unit-key>-rNN-stream.jsonl
    <unit-key>-rNN-final.txt
    <unit-key>-rNN-stderr.log
    Author-Claude-P<n>-<unit>.md
    Author-Codex-P<n>-<unit>.md
    Diff-Claude-P<n>-<unit>-rNN.md
    Diff-Codex-P<n>-<unit>-rNN.md
    Committed-P<n>-<unit>.md
```

Root contains only visible deliverables: optional top-level position files, `Result.md`, and `test-plan/`. All scratch, sessions, streams, journals, prompts, per-unit author files, per-unit diff files, and committed intermediate artifacts stay in `.codex/`.

Pattern source: scratch isolation follows existing duo conventions (`s:/yd-skills/skills/duo-design/SKILL.md:20-36`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:56-102`).

## Discovery Toolbox

Source code is the only ground truth by default. Existing tests, READMEs, and documentation are excluded as evidence unless the user explicitly enables web or external contract discovery and the file is itself a contract source.

Use:

1. Production source under each repo.
2. `RULEBOOK_ABS` for page shape, coverage vocabulary, scenario policy, mocks policy, cross-app policy, and the 21-rule checklist.
3. `RULEBOOK_REFS_ABS` selectively for page examples, checklist rationale, and flow-id edge cases.
4. `.codex/unit-manifest.json` after P1b.
5. Already committed `.codex/Committed-*` artifacts from upstream phases.
6. Web only when `web-allowed` appears in the user's prose.

Exclusion set for source walks:

```
Tests:    **/*.{spec,test,e2e}.*, **/test/**, **/tests/**, **/__tests__/**, **/spec/**, **/e2e/**
Build:    **/dist/**, **/build/**, **/.next/**, **/coverage/**
Vendor:   **/node_modules/**, **/local-packages/**
VCS/IDE:  **/.git/**, **/.idea/**, **/.vscode/**
Docs:     **/*.md, **/*.pdf, **/*.txt, **/CHANGELOG*, **/README*
```

Pattern source: source-only discovery and exclusions adapt `duo-testplan-build` (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:104-122`).

## Phase 1 - Mission Setup

The main Claude session is a thin coordinator. It does not do deep authoring itself. It resolves paths, initializes the mission folder, writes journal events, dispatches per-unit Claude subagents, enforces phase gates, copies committed unit outputs into final locations, and runs P5 checks.

Initialize:

1. Parse trigger, autonomous mode, modifiers, filters, slug, and `WEB_SEARCH`.
2. Create `Duo/TestPlan-<slug>/.codex/`.
3. Create or resume `.codex/journal.jsonl`.
4. Resolve and self-test `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS`.
5. Append `phase_start` for `P1a`.

Journal events:

| Event | Fields | When |
|---|---|---|
| `phase_start` | `phase`, `ts` | Before phase work starts. |
| `dispatch_start` | `phase`, `unit`, `round`, `prompt_path`, `expected_output_path` | Before each Codex or Claude subagent dispatch. |
| `artifact_accepted` | `path`, `status` | After validating a unit output. |
| `artifact_rejected` | `path`, `reason` | After rejecting malformed or stale output. |
| `field_resolved` | `unit`, `field_id`, `resolution` | After deterministic merge commits a field. |
| `field_disputed` | `unit`, `field_id`, `claude`, `codex` | When a field remains unresolved. |
| `gate_resolved` | `phase`, `unit`, `state` | At unit terminal state. |
| `phase_complete` | `phase`, `counts` | At phase exit. |
| `mission_halted` | `reason` | On fatal install, dispatch, or validation failure. |

Pattern source: event vocabulary and pre-write journal discipline adapt `duo-testplan-build` (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:423-440`).

## Per-Unit Protocol

Every P1a, P1b, P2, P3, P4, and P5 sanity unit uses the same protocol. Both peers author every unit; there is no rotation and no asymmetry.

Roles:

- Main Claude session: top-level coordinator only.
- Per-unit Claude subagent: owns the unit lifecycle, acts as the Claude-side voice, writes Claude author/diff files, writes Codex prompt files, invokes Codex, applies deterministic merge, and commits the unit artifact.
- Codex session: one new session per unit, resumed across all rounds in that unit only.

Round 0 AUTHOR:

- Claude subagent authors `Author-Claude-P<n>-<unit>.md`.
- Codex authors `Author-Codex-P<n>-<unit>.md`.
- P2/P4 flow-page units use the `linked-testplan` page shape: Flow under test, Scenarios, per-scenario Preconditions, Steps, Expected, Mocks, Code refs.
- P1a uses a manifest slice field set: repos, services, source boundaries, exclusions used.
- P1b uses a manifest slice field set: candidate roots, entrypoints, stable flow IDs.

Round 1+ DIFF:

- Both peers emit structured per-field diffs to `Diff-{Claude|Codex}-P<n>-<unit>-rNN.md`.
- Each field diff has:

```yaml
field_id: <stable id>
stance: keep | drop | replace | augment | dispute
value: <replacement or augmentation, if any>
evidence:
  - <path>:<line>
reason: <terse source-grounded rationale>
```

The subagent applies the merge table below. Exit as soon as every field is resolved. There is no confirmation round.

Default round cap: round 0 plus up to 4 diff rounds. `extended-convergence` removes the cap; warn in the journal every 2 extra diff rounds. P3 cross-app discovery defaults to a 1-round cap because it is enumerative; `extended-convergence` can extend it.

At cap with residual disputes, commit the artifact with inline `[disputed: claude=..., codex=...]` tags on each disputed field. Do not dispatch a separate resolver.

## Per-Field Merge Table

| Claude stance | Codex stance | Result |
|---|---|---|
| `keep` | `keep` | Commit field as-is. |
| `drop` | `drop` | Drop field. |
| `augment` | `augment` | Union augmentations, preserving source citations. |
| `replace x` | `replace y` where `x == y` | Commit replacement. |
| any | `dispute` | Leave unresolved; continue next round. |
| `dispute` | any | Leave unresolved; continue next round. |
| asymmetric `replace` | any non-identical stance | Leave unresolved; continue next round. |
| other asymmetric pair | any | Leave unresolved unless both values are source-identical after normalization. |

Normalization is conservative: trim whitespace, normalize list ordering only when the field is explicitly unordered, and never collapse different file:line evidence.

## Phase-by-Phase Orchestration

### P1a - Scope File Discovery

Sequential first. Spawn one Claude subagent. The subagent and Codex each inspect the workspace under `CWD`, apply the exclusion set, classify production source versus tests/build/vendor/docs, identify repos, identify services, and establish source boundaries.

Repo detection: subdirectory with `.git/`; otherwise `CWD` is the single repo. Service detection: `apps/<svc>/` pattern when present; otherwise top-level service for a repo or monorepo segment.

Output: `.codex/Committed-P1a-scope.md` containing `repos[]`, services per repo, source boundaries, and exclusion set used.

### P1b - Per-Service Scope

Parallel after P1a, one unit per `(repo, service)`, sharing the global concurrency cap. Each subagent identifies candidate source roots, entrypoints, and stable flow IDs. Entrypoints include HTTP controllers, Kafka producers/consumers, gRPC servers/clients, cron/scheduled jobs, S3/DDB/SQL/Redis access, and similar externally observable triggers.

Stable flow IDs derive from trigger plus entry symbol per linked-testplan Rule 11 (`s:/yd-skills/skills/linked-testplan/SKILL.md:147-148`).

Output: `.codex/Committed-P1b-<repo>-<svc>.md` with candidate roots, entrypoint inventory, exclusions, and flow IDs.

Main coordinator aggregates all P1b commits into `.codex/unit-manifest.json`.

### P2 - Local Flow Refinement

Parallel after all P1b units complete. Enumerate local flows from `.codex/unit-manifest.json`; spawn one unit per flow up to the shared cap.

Each unit reads the flow's entry file:line, downstream call sites, related persistence/emission code, and the rulebook. Both peers author a per-flow page using the linked-testplan page shape (`s:/yd-skills/skills/linked-testplan/SKILL.md:38-80`) and scenario/mocks policies (`s:/yd-skills/skills/linked-testplan/SKILL.md:98-117`).

Output: `.codex/Committed-P2-<flow-id>.md`, then copy to `test-plan/<repo>/<svc>/flows/<flow-id>.md`.

### P3 - Cross-App Discovery

Sequential after every P2 unit completes. Spawn one subagent unit. The unit reads all committed P2 artifacts and discovers cross-repo or cross-service seams: Kafka producer/consumer pairs, REST/gRPC server-client pairs, S3 writer-reader pairs, and equivalent workspace-spanning contracts.

Cross-app flow IDs use the `crossapp-*` prefix and derive from cross-app purpose, aligned with linked-testplan cross-app specifics (`s:/yd-skills/skills/linked-testplan/SKILL.md:118-126`).

Default cap: 1 diff round. User can extend with `extended-convergence`.

Output: `.codex/Committed-P3-crossapp.md` with cross-app flow IDs and evidence.

### P4 - Cross-App Flow Refinement

Parallel after P3. Spawn one unit per cross-app flow up to the shared cap.

Each unit uses producer-side and consumer-side P2 pages as converged facts, then reads source only to validate or fill gaps. Cross-app steps prefix the actor as `<service> → <service>: <action>` and avoid private internal mutations across service boundaries per linked-testplan (`s:/yd-skills/skills/linked-testplan/SKILL.md:78-80`, `s:/yd-skills/skills/linked-testplan/SKILL.md:122-126`).

Output: `.codex/Committed-P4-<flow-id>.md`, then copy to `test-plan/cross-app/flows/<flow-id>.md`.

### P5 - Result

Sequential final phase.

1. Write `Result.md` with Summary, Scope, per-repo/per-service flow counts, coverage matrix, convergence counts, disputed tag inventory, exclusions, and unresolved.
2. Spawn one sanity duo unit over `Result.md` plus the final `test-plan/` tree. The unit looks for cross-flow contradictions such as incompatible payload claims for the same topic or conflicting expected outcomes for shared dependencies.
3. Run `$CHECK_REFS_ABS` over committed `test-plan/**/*.md`.
4. Run `$CHECK_REFS_ABS` over `Result.md` with the manifest to verify entrypoint coverage when supported by the validator.
5. Apply only source-grounded corrections from the sanity unit; residual disagreements become `## Unresolved`.

Validator source: `check-refs.py` validates file:line refs and manifest coverage per linked-testplan (`s:/yd-skills/skills/linked-testplan/SKILL.md:184-195`).

## Codex Session Policy

Use one Codex session per unit. A unit starts fresh on round 0 if `.codex/session-<unit-key>` does not exist. The same session is resumed for every later round in that unit. Cross-unit Codex sessions never share context.

Rationale: new Codex sessions are expensive cold starts; resuming within a unit preserves the peer's prior reasoning across author/diff rounds without leaking context across independent units.

Session files live at:

```
$MISSION/.codex/session-<unit-key>
```

The `<unit-key>` must be path-safe and stable, for example `P1a-scope`, `P1b-repo-svc`, `P2-flow-id`, `P3-crossapp`, `P4-crossapp-flow-id`, or `P5-sanity`.

## Concurrency, Budget, Ceilings

P1b, P2, and P4 share one queue.

| Setting | Default | Override |
|---|---|---|
| Shared active per-unit subagents | 8 | `high-concurrency` -> 16; `very-high-concurrency` -> 32 |
| Per-unit Codex sessions | 1 | no override |
| Per-unit round cap | round 0 + 4 diff rounds | `extended-convergence` removes cap |
| P3 discovery cap | 1 diff round | `extended-convergence` extends |
| Per-dispatch hard ceiling | 20 minutes | no override |
| Web search | disabled | `web-allowed` -> live |

Dispatch budget target for a 5 service x 10 flow mission: about 290-580 total peer dispatches, assuming all units stop at round 1 at the floor and all hit round cap at the ceiling.

Pattern source: concurrency and budget prose adapt `duo-testplan-build` but this skill changes caps and removes N-pass refinement (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:442-468`).

## Signaling - DO NOT POLL

Launch every Codex dispatch via Claude Code Bash with `run_in_background: true`. The harness delivers a background-completion notification.

Claude main session and per-unit subagents must not:

- Poll stream files with sleep loops.
- Repeatedly check whether expected output exists.
- Use mtime loops.
- Spawn watcher scripts.

After launch, continue available local work. Stop when the Claude side of the current unit is complete and wait for the harness notification. The dispatch script's internal `monitor_once()` loop is allowed because it runs inside the background process and enforces the 20-minute ceiling.

Pattern source: no-poll discipline follows `duo-design` and `duo-testplan-build` (`s:/yd-skills/skills/duo-design/SKILL.md:70-83`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:487-499`).

## Prompt File Authorship

Each per-unit Claude subagent writes the full Codex prompt before invoking dispatch:

```
$MISSION/.codex/<unit-key>-rNN-prompt.txt
```

The dispatch script validates that the prompt is non-empty and pipes it to Codex stdin. The dispatch script does not write prompts.

Every prompt includes:

- Mission path and CWD.
- Absolute `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS`.
- Phase, unit key, round number, round cap, and expected output path.
- Source scope and upstream committed artifacts for that phase.
- Exact output format: AUTHOR for round 0, structured DIFF for round 1+.
- Web policy (`disabled` or `live`).

Pattern source: prompt-file ownership follows the existing duo convention (`s:/yd-skills/skills/duo-design/SKILL.md:84-89`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:501-514`).

## Codex Dispatch

Set env vars before invoking. Run via Bash with `run_in_background: true`.

Required env:

- `CWD`: absolute target workspace.
- `MISSION`: absolute `Duo/TestPlan-<slug>` folder.
- `KIND`: `TestPlanConverge`.
- `UNIT_KEY`: path-safe stable unit key.
- `ROUND`: unit-local round number, starting at 0.
- `PROMPT_FILE`: absolute prompt path.
- `CODEX_OUT`: absolute expected Codex output path.
- `WEB_SEARCH`: `disabled` or `live`.

This dispatch block keeps the duo-design wrapper shape and changes only unit-keyed paths, web-search variable, and within-unit resume behavior. Flag ordering is critical: all flags must appear before `resume "$SESSION_ID" -` (`s:/yd-skills/skills/duo-design/SKILL.md:132-140`, `s:/yd-skills/skills/duo-design/SKILL.md:192-200`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:559-568`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:627-636`).

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?TestPlanConverge}"
UNIT_KEY="${UNIT_KEY:?path-safe unit identifier}"
ROUND="${ROUND:?unit-local round number, starting at 0}"
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

# Flag ordering is CRITICAL: -C and all flags must come BEFORE `resume <session> -`.
# codex 0.130.0 rejects -C placed AFTER the session id.
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

## Phase 2 - Per-Unit Convergence

Per-unit Claude subagents perform the author/diff loop, not the main session.

For each unit:

1. Main session writes `dispatch_start` and spawns the Claude subagent.
2. Subagent writes the Codex round prompt to `.codex/<unit-key>-rNN-prompt.txt`.
3. Subagent launches Codex with the dispatch block.
4. Subagent authors the Claude side while Codex runs.
5. On completion notification, subagent validates Codex output path, then applies the merge table.
6. If unresolved fields remain and the cap is not reached, subagent writes next-round prompts and repeats using the same Codex session.
7. On terminal state, subagent writes `.codex/Committed-P<n>-<unit>.md` and emits `gate_resolved`.

The main session only advances phase gates after all required units for the current phase are terminal.

## Convergence

Convergence is the first agreed pair: the first round where deterministic field merge resolves every field with no remaining USER-TIER blocker. No confirmation round.

Terminal states:

| State | Meaning |
|---|---|
| `AGREED` | All fields resolved before cap. |
| `DEGRADED-CONTINUE` | Residual non-blocking disputes tagged inline; downstream may consume. |
| `BLOCKED` | Unit cannot produce a source-grounded artifact; downstream does not consume except `Result.md` summary. |
| `UNAVAILABLE` | Dispatch failure produced no usable peer output; autonomous mode converts to `DEGRADED-CONTINUE` or `BLOCKED` by Claude-side source evidence. |

Pattern source: no confirmation round follows the duo convention (`s:/yd-skills/skills/duo-design/SKILL.md:280-287`).

## Phase 3 - Result

`Result.md` must include:

```markdown
# Test Plan Result - <slug>

## Summary
## Scope
## Flow Counts
## Coverage Matrix
## Convergence Counts
## Disputed Fields
## Exclusions
## Unresolved
```

The coverage matrix maps every entrypoint in `.codex/unit-manifest.json` to exactly one flow or one explicit exclusion, matching linked-testplan Rule 12 and Rule 20 (`s:/yd-skills/skills/linked-testplan/SKILL.md:147-157`).

The final `test-plan/` tree uses exactly one Markdown file per flow, matching linked-testplan core structure (`s:/yd-skills/skills/linked-testplan/SKILL.md:25-36`).

## Self-Review

Before completing:

1. Verify `RULEBOOK_ABS` and `CHECK_REFS_ABS` were absolute paths in every prompt.
2. Verify `.codex/unit-manifest.json` exists and covers every committed flow.
3. Verify every finalized flow page follows linked-testplan page shape.
4. Verify every `[disputed:]` tag is inventoried in `Result.md`.
5. Run `$CHECK_REFS_ABS` on `test-plan/**/*.md`.
6. Run `$CHECK_REFS_ABS` on `Result.md` with manifest coverage when supported.
7. Scan for placeholder text: TBD, TODO, fill in, unresolved without explanation.
8. Verify root contains only allowed visible deliverables.

Fix issues inline. Do not run any script except `check-refs.py`, and only in P5.

## User Feedback

This skill requires autonomous mode, so do not ask mid-mission questions.

At the end, present `Result.md` as a clickable link and summarize:

- Number of repos, services, local flows, and cross-app flows.
- Number of units that ended `AGREED`, `DEGRADED-CONTINUE`, `BLOCKED`, or `UNAVAILABLE`.
- Whether `check-refs.py` passed.
- Any `## Unresolved` items.

If the user later supplies substantive corrections, reopen only affected units and rerun the per-unit protocol.

## Failure Modes

| Failure | Behavior |
|---|---|
| Broken plugin paths | Halt before P1a writes artifacts. |
| Codex dispatch missing prompt | Write `UNAVAILABLE`; subagent decides `DEGRADED-CONTINUE` or `BLOCKED` from Claude-side evidence. |
| Codex timeout | Same as dispatch unavailable. |
| Malformed Codex author/diff | Retry once in the same unit session if budget allows; then tag disputed fields. |
| Round cap reached | Commit with `[disputed: claude=..., codex=...]` tags per field. |
| P1a blocked | Halt; no downstream phase has source boundaries. |
| P1b service blocked | Exclude that service from P2; summarize in `Result.md`. |
| P2 flow blocked | Do not write that flow page; summarize in `Result.md`. |
| P3 cross-app blocked | Skip P4; summarize local-only coverage and unresolved cross-app discovery. |
| P4 cross-app flow blocked | Do not write that cross-app flow page; summarize in `Result.md`. |
| P5 check-refs fails | Fix source refs when evidence is clear; otherwise list failures in `## Unresolved`. |

Pattern source: status and failure vocabulary adapt existing testplan failure handling but remove refinement-pass/tiebreaker mechanics (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:469-485`).

## Hard Rules

- Direct Codex CLI only. No `/codex:rescue`, no plugin internals, no shared helper skill.
- Both peers author every unit, every phase.
- Main Claude session is only the coordinator; per-unit Claude subagents own unit convergence.
- One new Codex session per unit; resume only inside that unit.
- Never share Codex sessions across units.
- Every Codex invocation uses `gpt-5.5`, `model_reasoning_effort="xhigh"`, `--dangerously-bypass-approvals-and-sandbox`, `--json`, `--output-last-message`, `--skip-git-repo-check`, and `-C "$CWD"`.
- Flag ordering: all flags before `resume "$SESSION_ID" -`.
- Web search default is disabled. Use `live` only with `web-allowed`.
- Shared P1b/P2/P4 concurrency cap defaults to 8; `high-concurrency` means 16; `very-high-concurrency` means 32.
- Use the linked-testplan rulebook as-is. Do not modify it.
- Scripts are forbidden in the LLM convergence loop.
- Only `check-refs.py` may run, and only in P5.
- No pre-converge filters, per-phase validators, or script gatekeeping.
- Root contains only allowed visible deliverables; scratch stays in `.codex/`.
- Claude never polls; use harness background-completion notifications.
- Convergence is first agreed pair; no confirmation round.
- At cap, commit disputed fields with `[disputed:]` tags. No resolver dispatch.

Pattern source: hard-rule shape follows duo-design and duo-testplan-build (`s:/yd-skills/skills/duo-design/SKILL.md:330-341`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:728-747`).

## File Reading Limits

- Glob or grep before broad reads.
- Range-read files over 300 lines.
- Read only production source unless the rulebook path or validator path is being read.
- Read `linked-testplan` once per unit and load references selectively.
- Cite `file:line` for every source claim in author, diff, committed, and result artifacts.
- Do not read existing markdown, READMEs, generated docs, or tests as evidence for flow behavior.

Pattern source: file-reading discipline follows the existing duo skills and linked-testplan rulebook (`s:/yd-skills/skills/duo-design/SKILL.md:344-346`, `s:/yd-skills/skills/duo-testplan-build/SKILL.md:749-755`, `s:/yd-skills/skills/linked-testplan/SKILL.md:212-216`).
~~~~

## Reject rationale (REJECT branch)

Not applicable. All forge gates pass; CREATE is the correct verdict.

## Open Questions

None.
