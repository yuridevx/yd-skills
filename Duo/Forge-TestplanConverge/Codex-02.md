# Forge - Round 02 (Codex, mutual revision)

## Status vs peer's Round 01

ALL_AGREED

## Agreements added since my Round 01

- Autonomous mode is supported, not required - Claude's position matches the `duo-design` pattern where autonomous mode is detected by prose and default mode may ask one clarifying question (`s:/yd-skills/skills/duo-design/SKILL.md:14-17`). I accept this and withdraw my R1 autonomous-required gate.
- `web_search="disabled"` remains the correct default - this matches the existing `duo-testplan-build` prose modifier behavior (`s:/yd-skills/skills/duo-testplan-build/SKILL.md:44`).
- Keep the explicit terminal states and failure table from Codex-01 - Claude accepted `AGREED / DEGRADED-CONTINUE / BLOCKED / UNAVAILABLE` and the phase-specific failure behavior.
- Keep explicit `CODEX_OUT` as a caller-supplied env var - Claude accepted this as more flexible than deriving the output path from round number.
- Keep per-field journal events - `field_resolved` and `field_disputed` give the coordinator enough resume and audit detail.

## Disagreements with peer's Round 01

- None.

## Withdrawals from my Round 01

- Autonomous-required gate - withdrawn because default mode should be allowed with one clarifying question max.
- R1 frontmatter wording that said autonomous mode is required - replaced with "supports autonomous mode."
- R1 user-feedback section saying the skill requires autonomous mode - replaced with default-mode and autonomous-mode paths.
- Tilde code fence for the embedded draft - replaced with a backtick markdown fence.

## New issues raised

- None.

## Verdict (current)

CREATE

## Updated draft

```markdown
---
name: duo-testplan-converge
description: "Symmetric Claude+Codex convergent authoring of an e2e test plan tree for multi-repo workspaces using per-unit duo authoring plus step-by-step structured diff convergence. Six phases: P1a scope file discovery, P1b per-service scope, P2 local flow refinement, P3 cross-app discovery, P4 cross-app flow refinement, P5 result plus check-refs.py. Each unit runs a per-unit Claude subagent that owns the convergence cycle and resumes one Codex session across all rounds inside that unit. Round cap is R0 plus four diff rounds by default; user can extend via `extended-convergence`. At cap with residual disputes the artifact commits with `[disputed: claude=..., codex=...]` tags and no separate resolver dispatch. Both peers author every unit, every phase. Code is the only source of truth; existing tests, READMEs, and documentation are excluded inputs. Consumes the `linked-testplan` rulebook AS IS. Produces `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow-id>.md` and `test-plan/cross-app/flows/<flow-id>.md`. Direct Codex CLI only; no /codex:rescue, no plugin internals, no shared helper skill. Pins gpt-5.5, model_reasoning_effort=xhigh, yolo, --json, --output-last-message, --skip-git-repo-check, and -C $CWD. Web search disabled by default; flip to live with `web-allowed`. Scripts run ONLY at P5 (`check-refs.py`), never in the LLM convergence loop. Supports autonomous mode with prose `autonomously`, `no questions`, `hands-free`, `auto`, or `unattended`; otherwise default mode allows one clarifying question max for USER-TIER blockers. TRIGGERS ONLY on explicit `duo` keyword: `duo testplan-converge X`, `duo-testplan-converge X`, `/duo-testplan-converge X`, or `duo build a convergent test plan for X`. Does NOT auto-activate on plain `test plan X`, `e2e plan`, or `generate tests for X`."
---

# Duo Testplan Converge

Run a 6-phase, per-unit Claude+Codex convergence pipeline that writes an e2e test plan tree. Every phase uses the same unit protocol: both peers author, both peers diff by field, the per-unit Claude subagent deterministically merges resolved fields, and unresolved fields continue until first-AGREED-pair or the round cap.

The companion `linked-testplan` rulebook is consumed AS IS. It owns the page shape, coverage vocabulary, scenario policy, mocks policy, cross-app rules, and 21-rule checklist. Do not modify it from this skill.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

### Trigger

Trigger only on explicit `duo` phrasing:

- `duo testplan-converge X`
- `duo-testplan-converge X`
- `/duo-testplan-converge X`
- `duo build a convergent test plan for X`

Do not activate on plain `test plan X`, `e2e plan`, `generate tests for X`, or `write tests for X`.

### Mode

Detect autonomous mode when prose contains a clear execution phrase: `autonomously`, `no questions`, `hands-free`, `auto`, or `unattended`. Distinguish execution mode from topic adjectives. In autonomous mode, never call `AskUserQuestion`; USER-TIER blockers and residual disputes resolve to `[disputed: claude=..., codex=...]` tags or peer-attested `DEGRADED-CONTINUE` / `BLOCKED` outcomes logged in `Result.md`.

Default mode is allowed. Ask at most one clarifying question if the mission goal is too ambiguous to start. Surface USER-TIER blockers only after both peers have exhausted source investigation; present concise `(a)/(b)/(c)` options.

### Modifiers

| Modifier | Effect |
|---|---|
| `high-concurrency` | Shared P1b/P2/P4 cap 8 -> 16. |
| `very-high-concurrency` | Shared P1b/P2/P4 cap -> 32. |
| `extended-convergence` | Remove default round cap; soft warning at +2 over default per unresolved unit. |
| `web-allowed` | Codex `web_search` `disabled` -> `live`. |

### Filter and Slug

Support free-form repo/service filters in prose such as `only ingestion-service` or `work on X and Y`. Empty filter means all discovered repos/services.

Mint a 2-5 PascalCase slug from prose, for example `Petclinic` or `OrdersFlow`. If the user names an existing `Duo/TestPlan-<slug>/`, resume from `.codex/journal.jsonl`.

## Plugin Layout and Path Resolution

This skill ships in the `yd` plugin alongside the `linked-testplan` rulebook and root `scripts/check-refs.py` validator. The mission CWD is the user's target workspace, not the plugin install directory, so plugin-relative paths must be resolved to absolute paths before they are passed to dispatched subagents and Codex sessions.

At activation, resolve once and reuse for the mission:

- `PLUGIN_ROOT`: two directories above this skill directory.
- `RULEBOOK_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`.
- `RULEBOOK_REFS_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/references/`.
- `CHECK_REFS_ABS`: `$PLUGIN_ROOT/scripts/check-refs.py`.

Pass these absolute paths in every dispatched prompt. Before P1a writes any artifact, verify `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS` exist and are readable. Halt on broken install.

## Mission Folder Layout

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
        Author-Claude-P<n>-<unit-key>.md
        Author-Codex-P<n>-<unit-key>.md
        Diff-Claude-P<n>-<unit-key>-rNN.md
        Diff-Codex-P<n>-<unit-key>-rNN.md
        Committed-P<n>-<unit-key>.md

Root contains only visible deliverables: `Result.md` and `test-plan/`. All scratch, sessions, streams, journals, prompts, per-unit author files, per-unit diff files, and committed intermediate artifacts stay in `.codex/`.

## Discovery Toolbox

Source code is the only ground truth by default. Existing tests, READMEs, generated documentation, and ordinary Markdown are excluded as evidence.

Use:

1. Production source under each repo.
2. `RULEBOOK_ABS` for page shape, coverage vocabulary, scenario policy, mocks policy, cross-app policy, and the 21-rule checklist.
3. `RULEBOOK_REFS_ABS` selectively for page examples, checklist rationale, and flow-id edge cases.
4. `.codex/unit-manifest.json` after P1b.
5. Upstream `.codex/Committed-*` artifacts from earlier phases.
6. Web only when `web-allowed` appears in the user's prose.

Apply this exclusion set to source walks:

    Tests:    **/*.{spec,test,e2e}.*, **/test/**, **/tests/**, **/__tests__/**, **/spec/**, **/e2e/**
    Build:    **/dist/**, **/build/**, **/.next/**, **/coverage/**
    Vendor:   **/node_modules/**, **/local-packages/**
    VCS/IDE:  **/.git/**, **/.idea/**, **/.vscode/**
    Docs:     **/*.md, **/*.pdf, **/*.txt, **/CHANGELOG*, **/README*

## Phase 1 - Mission Setup

The main Claude session is a thin coordinator. It resolves paths, initializes the mission folder, writes journal events, dispatches per-unit Claude subagents, enforces phase gates, copies committed unit outputs into final locations, and runs P5 checks. It does not run convergence rounds itself.

Initialize:

1. Parse trigger, mode, modifiers, filters, slug, and `WEB_SEARCH`.
2. Create `Duo/TestPlan-<slug>/.codex/`.
3. Create or resume `.codex/journal.jsonl`.
4. Resolve and self-test `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS`.
5. Append `phase_start` for P1a.

Journal events:

| Event | Fields | When |
|---|---|---|
| `phase_start` | `phase`, `ts` | Before phase work starts. |
| `subagent_spawn` | `phase`, `unit_key`, `cap_consumed` | Before a per-unit Claude subagent dispatch. |
| `dispatch_start` | `phase`, `unit_key`, `round`, `prompt_path`, `expected_output_path` | Before each Codex dispatch. |
| `artifact_accepted` | `path`, `status` | After validating an output. |
| `artifact_rejected` | `path`, `reason` | After rejecting malformed or stale output. |
| `field_resolved` | `unit_key`, `round`, `field_id`, `resolution` | After deterministic merge commits a field. |
| `field_disputed` | `unit_key`, `round`, `field_id`, `claude`, `codex` | When a field remains unresolved. |
| `gate_resolved` | `phase`, `unit_key`, `state` | At unit terminal state. |
| `cap_hit` | `unit_key`, `disputed_field_count` | When round cap is reached with residual disputes. |
| `phase_complete` | `phase`, `counts` | At phase exit. |
| `mission_halted` | `reason` | On fatal failure. |

On harness restart, read the journal tail, resume pending units, and preserve per-unit `.codex/session-<unit-key>` files.

## Per-Unit Protocol

Every unit uses the same protocol: P1a, each P1b service, each P2 local flow, P3, each P4 cross-app flow, and P5 sanity. The main session spawns one Claude subagent per unit. The subagent owns the full convergence cycle and exits with a committed artifact.

Unit-key examples:

- `P1a-scope`
- `P1b-<repo>-<svc>`
- `P2-<flow-id>`
- `P3-crossapp`
- `P4-<flow-id>`
- `P5-sanity`

R0 AUTHOR:

- The subagent self-authors as the Claude-side voice and writes `Author-Claude-P<n>-<unit-key>.md`.
- The subagent writes the Codex R0 prompt, starts a new Codex session for the unit, and Codex writes `Author-Codex-P<n>-<unit-key>.md`.
- The new Codex session id is captured in `.codex/session-<unit-key>`.

R1..N DIFF:

- The subagent self-diffs as Claude and writes `Diff-Claude-P<n>-<unit-key>-rNN.md`.
- The subagent resumes the same unit Codex session and Codex writes `Diff-Codex-P<n>-<unit-key>-rNN.md`.
- The subagent applies the deterministic per-field merge table and journals `field_resolved` / `field_disputed`.
- If all fields resolve, the unit commits with `AGREED`.
- If unresolved fields remain and round count is below cap, continue to the next diff round.
- If cap is reached, commit agreed fields and tag residuals with `[disputed: claude=..., codex=...]`.

Default round cap: R0 plus four diff rounds. `extended-convergence` removes the cap and writes a soft warning every two additional diff rounds. P3 cross-app discovery defaults to one diff round because it is enumerative; `extended-convergence` can extend it.

## Per-Field Merge Table

Both peers emit structured per-field diffs. Field stance enum:

    keep | drop | replace | augment | dispute

Diff field shape:

    field_id: <stable id>
    stance: keep | drop | replace | augment | dispute
    value: <replacement or augmentation, if any>
    evidence:
      - <path>:<line>
    reason: <terse source-grounded rationale>

Merge table:

| Claude stance | Codex stance | Outcome |
|---|---|---|
| `keep` | `keep` | Commit field as-is. |
| `drop` | `drop` | Drop field. |
| `augment` | `augment` | Union augmentations, preserving citations. |
| `replace x` | `replace y` where `x == y` | Commit replacement. |
| any | `dispute` | Unresolved; continue next round. |
| `dispute` | any | Unresolved; continue next round. |
| asymmetric `replace` | any non-identical stance | Unresolved; continue next round. |
| other asymmetric pair | any | Unresolved unless both values are source-identical after conservative normalization. |

Normalization is conservative: trim whitespace, normalize unordered-list ordering only when the field is explicitly unordered, and never collapse different file:line evidence.

## Codex Session Policy

Deliberate deviation from `duo-testplan-build`:

- Within a unit: Codex session is new at R0, then resumed for every diff round R1..N.
- Across units: sessions never share. Each unit gets its own new Codex cold start at `.codex/session-<unit-key>`.
- Across phases: sessions never share. If the same flow appears in P2 and P4, P4 still starts a new unit session.

Rationale: Codex new-session is the expensive operation. Within-unit resume preserves Codex's prior reasoning across rounds, while cross-unit freshness preserves convergence boundaries.

## Concurrency

P1b, P2, and P4 share one queue.

| Setting | Default | Override |
|---|---|---|
| Shared active per-unit subagents | 8 | `high-concurrency` -> 16; `very-high-concurrency` -> 32 |
| Per-unit Codex sessions | 1 | none |
| Per-unit round cap | R0 + 4 diff rounds | `extended-convergence` removes cap |
| P3 discovery cap | 1 diff round | `extended-convergence` extends |
| Per-dispatch hard ceiling | 20 minutes | none |
| Web search | disabled | `web-allowed` -> live |

Dispatch budget target for a 5 service x 10 flow mission: about 290-580 total peer dispatches.

## Phase-by-Phase Orchestration

### P1a - Scope File Discovery

Sequential first. Spawn one Claude subagent with unit key `P1a-scope`. The subagent and Codex inspect the workspace under `CWD`, apply the exclusion set, classify production source versus tests/build/vendor/docs, identify repos, identify services, and establish source boundaries.

Repo detection: subdirectory with `.git/`; otherwise `CWD` is the single repo. Service detection: `apps/<svc>/` pattern when present; otherwise top-level if monorepo.

Field set: `repos[]`, `services_per_repo`, `source_boundaries`, `exclusions_used`.

Commit: `.codex/Committed-P1a-scope.md`.

### P1b - Per-Service Scope

Parallel after P1a, one unit per `(repo, service)`, sharing the global concurrency cap. Unit keys: `P1b-<repo>-<svc>`.

Each unit identifies candidate source roots, entrypoints, and stable flow IDs. Entrypoints include HTTP controllers, Kafka producers/consumers, gRPC servers/clients, cron or scheduled jobs, S3/DDB/SQL/Redis access, and similar externally observable triggers.

Stable flow IDs derive from trigger plus entry symbol per linked-testplan Rule 11.

Field set: `candidate_roots[]`, `entrypoints[]` with file, line, trigger kind, and trigger, plus `flow_ids[]`.

Commit: `.codex/Committed-P1b-<repo>-<svc>.md`. The main session aggregates all P1b commits into `.codex/unit-manifest.json`.

### P2 - Local Flow Refinement

Parallel after all P1b units complete. Enumerate local flows from `.codex/unit-manifest.json`; spawn one unit per flow up to the shared cap. Unit keys: `P2-<flow-id>`.

Each unit reads the flow entry `file:line`, downstream call sites, related persistence/emission code, `RULEBOOK_ABS`, and relevant `RULEBOOK_REFS_ABS`.

Field set follows the linked-testplan page shape:

- `flow_under_test`: trigger, entry `file:line`, brief.
- `scenarios[]`: each with name, HAPPY/NEGATIVE tag, preconditions, steps, expected outcomes, mocks, and code refs.
- `code_refs[]`: flow-level supporting references.

Commit: `.codex/Committed-P2-<flow-id>.md`, then copy to `test-plan/<repo>/<svc>/flows/<flow-id>.md`.

### P3 - Cross-App Discovery

Sequential after every P2 unit completes. Spawn one subagent with unit key `P3-crossapp`.

The unit reads all P2 commits and identifies cross-repo seams: Kafka producer/consumer across repos, REST/gRPC server-client across repos, S3 writer-reader across repos, and equivalent workspace-spanning contracts.

Field set: `cross_app_flows[]` with `flow_id`, `participants`, `triggering_actor`, `seam_kind`, and evidence. Cross-app flow IDs use the `crossapp-*` prefix.

Default cap: one diff round. `extended-convergence` extends.

Commit: `.codex/Committed-P3-crossapp.md`.

### P4 - Cross-App Flow Refinement

Parallel after P3, one unit per cross-app flow up to the shared cap. Unit keys: `P4-<flow-id>`.

Each unit reuses producer-side and consumer-side P2 pages as converged facts and reads source only to validate or fill gaps.

Field set follows the linked-testplan cross-app shape. Steps prefix the actor as `<service> → <service>: <action>`. Do not include internal mutation steps across service boundaries.

Commit: `.codex/Committed-P4-<flow-id>.md`, then copy to `test-plan/cross-app/flows/<flow-id>.md`.

### P5 - Result

Sequential final phase.

1. Main session writes `Result.md`.
2. Spawn one sanity duo unit with unit key `P5-sanity` over `Result.md` plus the final `test-plan/` tree. It catches cross-flow contradictions such as incompatible payload claims for the same topic or conflicting expected outcomes for shared dependencies.
3. Run `$CHECK_REFS_ABS` over committed `test-plan/**/*.md`.
4. Run `$CHECK_REFS_ABS` over `Result.md` and `.codex/unit-manifest.json` for file:line refs and entrypoint coverage when supported by the validator.
5. Apply source-grounded corrections from P5-sanity and validator output. Residuals become `## Unresolved`.
6. Append `phase_complete` for P5.

`Result.md` must include:

    # Test Plan Result - <slug>

    ## Summary
    ## Scope
    ## Flow Counts
    ## Coverage Matrix
    ## Convergence Counts
    ## Disputed Fields
    ## Exclusions
    ## Unresolved

The coverage matrix maps every entrypoint in `.codex/unit-manifest.json` to exactly one flow or one explicit exclusion. The final `test-plan/` tree uses one Markdown file per flow.

## Signaling - DO NOT POLL

Every Codex dispatch runs via Bash with `run_in_background: true`. The harness notifies on completion.

The main session and subagents must not:

- Poll stream files with sleep loops.
- Repeatedly check whether output exists.
- Use mtime loops.
- Spawn watcher scripts.

The subagent dispatches Codex, works in parallel on its Claude-side authoring or diff, and stops when its side is complete. On the background-completion notification, validate Codex output, apply the merge table, and decide commit versus next round.

The dispatch script's internal `monitor_once()` is allowed because it runs inside the background process and enforces the 20-minute ceiling.

## Prompt File Authorship

Each per-unit subagent writes the full Codex prompt before invoking dispatch:

    $MISSION/.codex/<unit-key>-rNN-prompt.txt

The dispatch script validates the prompt is non-empty and pipes it to Codex stdin. The dispatch script does not write prompts.

Every prompt includes:

- Mission path and CWD.
- Absolute `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS`.
- Phase, unit key, round number, round cap, and expected output path.
- Source scope and upstream committed artifacts for the phase.
- Exact output format: AUTHOR for R0 or structured DIFF for R1+.
- Web policy: `disabled` or `live`.

## Codex Dispatch

Set env vars before invoking. Run via Bash with `run_in_background: true`.

Required env:

- `CWD`: absolute target workspace.
- `MISSION`: absolute `Duo/TestPlan-<slug>` folder.
- `KIND`: `TestPlanConverge`.
- `UNIT_KEY`: path-safe stable unit key.
- `ROUND`: unit-local round number starting at 0.
- `PROMPT_FILE`: absolute prompt path.
- `CODEX_OUT`: absolute expected Codex output path.
- `WEB_SEARCH`: `disabled` or `live`.

Dispatch script:

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

## Phase 2 - Per-Unit Convergence

For each unit:

1. Main session writes `subagent_spawn` and dispatches the per-unit Claude subagent.
2. Subagent writes the R0 Codex prompt to `.codex/<unit-key>-r00-prompt.txt`.
3. Subagent launches Codex R0 with the dispatch block and authors Claude R0 in parallel.
4. On completion notification, subagent validates Codex output.
5. For R1..N, subagent writes the next prompt, resumes Codex, self-diffs in parallel, and applies the merge table.
6. If unresolved fields remain and cap is not reached, repeat.
7. On terminal state, subagent writes `.codex/Committed-P<n>-<unit-key>.md`, emits `gate_resolved`, and exits.

The main session advances phase gates only after all required units for the current phase are terminal.

## Convergence

Convergence is the first round where deterministic field merge resolves every field with no remaining USER-TIER blocker. No confirmation round.

Terminal states:

| State | Meaning |
|---|---|
| `AGREED` | All fields resolved before cap. |
| `DEGRADED-CONTINUE` | Some fields tagged `[disputed:]` at cap; downstream may consume. |
| `BLOCKED` | Unit cannot produce a source-grounded artifact; downstream does not consume except `Result.md` summary. |
| `UNAVAILABLE` | Dispatch failure produced no usable peer output; autonomous mode converts to `DEGRADED-CONTINUE` or `BLOCKED` based on Claude-side evidence. |

## Phase 3 - Result

P5 writes the final `Result.md` and leaves the final tree in `test-plan/`. Before completion, the main session runs the P5 sanity unit and `$CHECK_REFS_ABS`, then records any residuals in `## Unresolved`.

## Self-Review

Before each Codex dispatch:

1. Prompt file exists at the named path and is non-empty.
2. Output path matches naming convention.
3. `WEB_SEARCH` is `disabled` unless `web-allowed` is present.
4. Journal `dispatch_start` record is appended.

Before P5 finalization:

1. Coverage matrix complete: every entrypoint maps to flow or exclusion.
2. `$CHECK_REFS_ABS` passes on `test-plan/**/*.md`, or failures are listed in `Result.md`.
3. `$CHECK_REFS_ABS` coverage mode passes with `.codex/unit-manifest.json` when supported, or failures are listed in `Result.md`.
4. No unit has terminal `UNAVAILABLE` without peer-attested `DEGRADED-CONTINUE` or `BLOCKED` resolution.
5. All open `phase_start` events have matching `phase_complete`.
6. Root contains only `Result.md` and `test-plan/`.
7. Every `[disputed:]` tag appears in `Result.md` disputed inventory.

Fix issues inline. Do not run any script except `check-refs.py`, and only in P5.

## User Feedback

Default mode:

- Ask at most one clarifying question if the mission cannot start.
- Ask for USER-TIER blockers only after both peers exhaust source investigation.
- Do not ask the user to resolve ordinary `[disputed:]` fields.

Autonomous mode:

- Ask no questions.
- Resolve through `[disputed:]` tags and peer-attested `DEGRADED-CONTINUE` / `BLOCKED`.
- Log unresolved outcomes in `Result.md`.

At the end, present `Result.md` as a clickable link and summarize repos, services, local flows, cross-app flows, terminal-state counts, `check-refs.py` result, and unresolved items.

If the user later supplies substantive corrections, reopen only affected units and rerun the per-unit protocol.

## Failure Modes

| Failure | Behavior |
|---|---|
| Broken plugin paths | Halt before P1a writes artifacts. |
| Codex dispatch missing prompt | Write `UNAVAILABLE`; subagent decides `DEGRADED-CONTINUE` or `BLOCKED` from Claude-side evidence. |
| Codex timeout | Same as dispatch unavailable. |
| Malformed Codex author/diff | Retry once in the same unit session if budget allows; then tag disputed fields. |
| Round cap reached | Commit with `[disputed: claude=..., codex=...]` tags per residual field. |
| P1a blocked | Halt; no downstream phase has source boundaries. |
| P1b service blocked | Exclude that service from P2; summarize in `Result.md`. |
| P2 flow blocked | Do not write that flow page; summarize in `Result.md`. |
| P3 blocked | Skip P4; summarize local-only coverage and unresolved cross-app discovery. |
| P4 cross-app flow blocked | Do not write that cross-app flow page; summarize in `Result.md`. |
| P5 check-refs fails | Fix source refs when evidence is clear; otherwise list failures in `## Unresolved`. |

## Hard Rules

- Direct Codex CLI only. No `/codex:rescue`, no plugin internals, no shared helper skill.
- Every Codex invocation uses `gpt-5.5`, `model_reasoning_effort="xhigh"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, and `-C "$CWD"`.
- `web_search` is `disabled` by default. Flip to `live` only when prose contains `web-allowed`.
- Flag ordering: all flags before `resume "$SESSION_ID" -`.
- Codex sessions are new per unit at R0, resumed across rounds within the unit lifecycle, and never shared across units or phases.
- Both peers author every unit, every phase. No rotation, no asymmetry.
- Main session is the thin top-level coordinator. Per-unit Claude subagents own convergence cycles.
- Per-unit Claude subagent is the Claude-side voice.
- Per-field merge table is deterministic and applied by the subagent.
- Convergence is first-AGREED-pair. No confirmation round.
- At round cap with residual disputes, commit agreed fields and tag remaining fields `[disputed: claude=..., codex=...]`. No separate resolver dispatch.
- Use the linked-testplan rulebook as-is. Do not modify it.
- Scripts are forbidden in the LLM convergence loop.
- Only `$CHECK_REFS_ABS` may run, and only in P5.
- No pre-converge filters, per-phase validators, or script gatekeeping.
- Code is the only source of truth. Do not read existing markdown, READMEs, generated docs, or tests as evidence.
- Claude never polls. Wait for harness background-completion notifications.
- No user questions in autonomous mode.
- Root contains only `Result.md` and `test-plan/`; scratch stays in `.codex/`.
- One `.md` per flow in the final `test-plan/` tree.
- Shared concurrency cap is 8 across P1b/P2/P4; `high-concurrency` raises it to 16 and `very-high-concurrency` raises it to 32.
- Trigger only on explicit `duo` keyword.

## File Reading Limits

- Glob or grep before broad reads.
- Max 5 files per parallel read batch.
- Range-read source files over 300 lines.
- Read `linked-testplan` once per unit; load references selectively.
- Cite `file:line` for every claim in author, diff, committed, and result artifacts.
- Do not read existing markdown, READMEs, generated docs, or tests as evidence for flow behavior.
```

## Open Questions

- None.
