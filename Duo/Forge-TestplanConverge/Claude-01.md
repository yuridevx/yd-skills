# Forge - Round 1 (Claude investigation)

## Investigation

- `skills/duo-design/SKILL.md:6-340` — canonical duo convergence pattern, single-mission shape, inlined dispatch block; reference for canonical sections and Hard Rules.
- `skills/duo-testplan-build/SKILL.md:12-26` — Plugin Layout and Path Resolution pattern (compute `$PLUGIN_ROOT` from skill base dir, resolve `$RULEBOOK_ABS`, `$CHECK_REFS_ABS`; pass absolute paths to dispatched agents because dispatched agents' CWD is the user workspace, not the plugin install dir).
- `skills/duo-testplan-build/SKILL.md:104-122` — exclusion set for production-source walks (tests/build/vendor/VCS/docs); reused as-is for P1a/P1b.
- `skills/duo-testplan-build/SKILL.md:138-186` — manifest schema (`unit-manifest.json` with repos→services→entrypoints→flow IDs); reused for P1 outputs.
- `skills/linked-testplan/SKILL.md:38-79` — per-flow page shape; consumed AS IS by P2/P4 authoring.
- `skills/linked-testplan/SKILL.md:83-96` — coverage vocabulary; consumed AS IS.
- `skills/linked-testplan/SKILL.md:128-159` — 21-rule refinement checklist; per-unit diff agents walk this.
- `skills/linked-testplan/SKILL.md:184-205` — `scripts/check-refs.py` modes (refs + manifest coverage); P5 runs this.
- `.claude-plugin/plugin.json:1-14` — plugin manifest version `0.3.0`; needs description bump when new skill ships.
- `.claude-plugin/marketplace.json:13-19` — marketplace description; needs same bump.
- `.codex-plugin/plugin.json:1-15` — codex plugin manifest mirror.
- `AGENTS.md:11-21` — skill catalog; needs `duo-testplan-converge` entry.
- `README.md` — needs same catalog entry mirror.
- `CLAUDE.md:9-15` — skill catalog mirror per CLAUDE.md convention.

## Gating Evaluation

- Pattern recurs across missions? **YES** — e2e test plan authoring across microservice workspaces is a recurring mission shape; the existing `duo-testplan-build` covers the same domain, and missions in `Duo/Forge-TestplanBuild/` and `Duo/Design-TestPlanSkill/` show the domain has been engaged repeatedly.
- Stable artifact shape? **YES** — `Duo/TestPlan-<slug>/Result.md` + `test-plan/<repo>/<svc>/flows/<flow-id>.md` + `test-plan/cross-app/flows/<flow-id>.md`, identical to `duo-testplan-build`'s artifact tree per `linked-testplan/SKILL.md:29-34`.
- Definable investigation procedure? **YES** — manifest extraction (P1a + P1b) → per-flow refinement (P2) → cross-app correlation (P3 + P4) → result (P5). Each phase has a single per-unit duo protocol, identical shape across all phases.
- Distinct from existing duo-*? **YES** — `duo-testplan-build` exists at `skills/duo-testplan-build/SKILL.md` with 8-phase pipeline, union-merge implicit convergence, N-parallel-pass refinement, and ~1,950 dispatch ceiling. The new skill uses 6-phase per-unit duo author + diff convergence, ~290-580 dispatch ceiling, per-unit Claude subagent orchestration, codex session reuse within units. Coexist; do not replace.
- **Verdict: CREATE.**

## Draft (CREATE branch)

```markdown
---
name: duo-testplan-converge
description: Symmetric Claude+Codex authoring of an e2e test plan tree for multi-repo workspaces, using per-unit duo author + step-by-step diff convergence (distinct from `duo-testplan-build` which uses union-merge + N-parallel-pass refinement). Six phases - P1a scope file discovery, P1b per-service scope, P2 local flow refinement, P3 cross-app discovery, P4 cross-app flow refinement, P5 result. Each unit runs a per-unit Claude subagent that owns the convergence cycle and resumes one codex session across all rounds within the unit. Round cap 4 by default, user can extend. At cap with residual disputes the artifact commits with [disputed:] tags - no separate resolver dispatch. Both peers author every unit, every phase. Code is the only source of truth - existing tests, READMEs, and documentation are excluded inputs. Consumes the `linked-testplan` rulebook AS IS. Produces `Duo/TestPlan-<slug>/Result.md` plus `test-plan/<repo>/<svc>/flows/<flow>.md` and `test-plan/cross-app/flows/<flow>.md`. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh + yolo. Web search OFF by default (source is truth); flip with `web-allowed`. Scripts run ONLY at P5 (`check-refs.py`); NEVER in the LLM convergence loop. TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo testplan-converge X", "duo-testplan-converge X", "/duo-testplan-converge X", "duo build a convergent test plan for X". Does NOT auto-activate on plain "test plan X" / "generate tests for X" / "e2e plan" requests.
---

# Duo Testplan Converge

Run a 6-phase pipeline that produces an e2e test plan tree from source code via per-unit duo author + diff convergence. Each unit (a scope step, a flow, a cross-app flow) runs a dedicated Claude subagent that owns its own author-then-converge cycle and resumes a single codex session across all rounds within the unit. The main Claude session is a thin top-level coordinator only.

The rulebook lives in the companion `linked-testplan` skill. Every dispatched authoring or diff agent reads the rulebook for page shape, coverage vocabulary, the 21-rule checklist, scenario policy, and mocks policy. This skill is the executor; nothing here duplicates the rulebook.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

### Trigger

Triggers on explicit `duo` phrasing: `duo testplan-converge X`, `duo-testplan-converge X`, `/duo-testplan-converge X`, `duo build a convergent test plan for X`. Does NOT auto-activate on plain `test plan X` / `e2e plan` / `generate tests for X`.

### Modifiers (prose-detected)

| Modifier | Effect |
|---|---|
| `autonomously`, `no questions`, `hands-free`, `auto`, `unattended` | Autonomous mode: never call `AskUserQuestion`; missing preferences log to `Result.md → Unresolved`. |
| `high-concurrency` | Shared concurrency cap 8 → 16 across P1b/P2/P4. |
| `very-high-concurrency` | Shared concurrency cap → 32. |
| `extended-convergence` | Round cap 4 → unbounded (soft warning at +2 over default). |
| `web-allowed` | Codex `web_search` flipped from `off` to `live` (default off; test planning grounds in source). |

Distinguish autonomous trigger phrases from topic adjectives ("design an autonomous system" is topic, not mode).

### Filter

Free-form repo filter in prose: `only ingestion-service`, `work on X and Y`. Empty filter → all discovered repos.

### Slug

Mint a 2-5 PascalCase slug from prose (e.g. `Petclinic`, `OrdersFlow`). If the user names an existing `Duo/TestPlan-<slug>/` folder, reuse it — the orchestrator picks up from journal tail.

## Plugin Layout and Path Resolution

This skill ships in the `yd` plugin alongside the `linked-testplan` rulebook (sibling skill) and `scripts/check-refs.py` (validator at the plugin root). The main session's CWD is the mission target workspace, NOT the plugin install dir — so plugin-relative paths must be resolved to absolute paths before being passed to dispatched subagents and codex sessions.

**At skill activation, resolve once and reuse for the mission:**

- `PLUGIN_ROOT` — derived from the skill's base directory (announced by the harness as "Base directory for this skill: ..."). Compute `PLUGIN_ROOT = <skill base>/../..`. For example, if the skill is at `C:\Users\<user>\.claude\plugins\cache\yd\yd\<version>\skills\duo-testplan-converge`, then `PLUGIN_ROOT` is `C:\Users\<user>\.claude\plugins\cache\yd\yd\<version>`.
- `RULEBOOK_ABS` = `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`
- `RULEBOOK_REFS_ABS` = `$PLUGIN_ROOT/skills/linked-testplan/references/`
- `CHECK_REFS_ABS` = `$PLUGIN_ROOT/scripts/check-refs.py`

**Pass these ABSOLUTE paths in every dispatched prompt.** Subagent prompts and codex stdin prompts both receive the absolute path; dispatched agents Read / Run them regardless of their CWD. Never instruct a dispatched agent to resolve `skills/...` or `scripts/...` relative to its own CWD.

**Self-test on first run of a mission.** Before P1a writes any artifact, verify that `RULEBOOK_ABS` and `CHECK_REFS_ABS` exist and are readable. If either is missing, halt with a clear error pointing at the broken install.

## Mission Folder Layout

```
Duo/TestPlan-<slug>/
  Result.md                                    converged index + summary  (visible)
  test-plan/                                   final artifact tree        (visible)
    <repo>/<svc>/flows/<flow-id>.md
    cross-app/flows/<flow-id>.md

  .codex/                                      ALL scratch / state / logs
    journal.jsonl                              pre-write event log
    unit-manifest.json                         P1 output
    
    # Per-unit codex session ids (one per unit, resumed within)
    session-P1a
    session-P1b-<repo>-<svc>
    session-P2-<flow-id>
    session-P3
    session-P4-<flow-id>
    session-P5-sanity
    
    # Per-round subagent-authored prompts and codex stream artifacts
    <unit-key>-r{NN}-prompt.txt
    <unit-key>-r{NN}-stream.jsonl
    <unit-key>-r{NN}-final.txt
    <unit-key>-r{NN}-stderr.log
    
    # Per-round position files (round 0 = author; round 1+ = diff)
    Author-{Claude|Codex}-<unit-key>.md
    Diff-{Claude|Codex}-<unit-key>-r{NN}.md
    
    # Per-unit committed artifact (subagent's final output)
    Committed-<unit-key>.md
```

Root contains only `Result.md` + `test-plan/`. All position files, diffs, prompts, streams, and session ids live in `.codex/`. Committed per-unit artifacts in `.codex/Committed-*.md` are copied into the `test-plan/` tree at finalization.

## Discovery Toolbox

Source code is the only ground truth. Existing tests, READMEs, and documentation are excluded inputs at every phase.

1. Production source under each repo (per the exclusion set below).
2. `linked-testplan` rulebook (resolved as `$RULEBOOK_ABS` per Plugin Layout and Path Resolution) — every authoring and diff agent reads it.
3. Mission journal at `.codex/journal.jsonl` for resume semantics.
4. Prior committed artifacts within the mission — read for P2 → P3 (cross-app discovery sees all P2 commits); read for P4 (reuses producer/consumer-side P2 commits as fact); read for P5 (sanity sweep over `test-plan/` tree).
5. Web access is OFF by default. The `web-allowed` prose modifier flips Codex to `web_search="live"` for cases where external contract specs are part of the source-of-truth.

Exclusion set (apply at every source walk; identical to duo-testplan-build):

```
Tests:    **/*.{spec,test,e2e}.*, **/test/**, **/tests/**, **/__tests__/**, **/spec/**, **/e2e/**
Build:    **/dist/**, **/build/**, **/.next/**, **/coverage/**
Vendor:   **/node_modules/**, **/local-packages/**
VCS/IDE:  **/.git/**, **/.idea/**, **/.vscode/**
Docs:     **/*.md, **/*.pdf, **/*.txt, **/CHANGELOG*, **/README*
```

## Per-Unit Protocol

Every unit (P1a, each P1b service, each P2 flow, P3, each P4 cross-app flow, P5 sanity) runs the identical per-unit duo protocol. The main session spawns one Claude subagent per unit. The subagent owns the full convergence cycle and exits with a committed artifact.

```
PER UNIT  (one Claude subagent owns this entire cycle)

  R0  AUTHOR (parallel)
        Subagent self-authors (Claude voice)  ──┐
        Subagent spawns codex (NEW session, expensive ONCE per unit) ──┤── round 0 outputs
        Codex authors via the subagent's bg dispatch                  ──┘
        Codex session_id is captured into .codex/session-<unit-key>.

  R1..N  DIFF (parallel, while round count < cap and disputes remain)
        Subagent self-diffs against R(NN-1) outputs (Claude voice) ──┐
        Subagent dispatches codex via RESUME of same session ──────┤── round NN diffs
        Codex diffs via resumed session                             ──┘
        
        Subagent applies per-field merge table (deterministic, no LLM):
          (keep, keep)       → commit field
          (drop, drop)       → drop field
          (augment, augment) → union the augmentations
          (replace x, replace x) → commit replacement
          (any, dispute) or asymmetric replace / drop / replace mismatch
                             → field unresolved, next round
        
        If all fields resolved → exit loop, COMMIT.
        If round count == cap → commit fields where peers agreed,
                                 tag remaining as [disputed: claude=..., codex=...],
                                 journal "convergence cap hit",
                                 COMMIT.

  COMMIT
        Subagent writes Committed-<unit-key>.md.
        Subagent exits.
        Main session receives bg-completion notification, advances phase state.
```

Round cap default 4 (R0 + up to 4 diff rounds = 5 LLM turns within a unit's codex session). User extends via `extended-convergence` prose modifier; soft warning at +2 over default.

## Per-Field Merge Table

The diff format both peers emit is a structured per-field stance list. The subagent (not LLM, deterministic logic) applies this table to decide commit-vs-continue per field.

Field stance enum: `keep | drop | replace <value> | augment <addition> | dispute`.

| Claude stance | Codex stance | Outcome |
|---|---|---|
| keep | keep | commit field unchanged |
| drop | drop | drop field |
| augment a | augment b | commit field + union(a, b) |
| replace x | replace x | commit replacement x |
| keep | augment a | commit field + a |
| augment a | keep | commit field + a |
| keep | drop | unresolved → next round |
| keep | replace x | unresolved → next round |
| drop | replace x | unresolved → next round |
| augment a | replace x | unresolved → next round |
| augment a | drop | unresolved → next round |
| replace x | replace y (x≠y) | unresolved → next round |
| any | dispute | unresolved → next round |
| dispute | dispute | unresolved → next round; mark for at-cap-tagging |

Field stance is structured markdown the subagent parses; not free prose. The diff position file has a fixed YAML-like body where each field name maps to one stance entry.

## Codex Session Policy

Deliberate deviation from `duo-testplan-build`'s "refinement-passes-must-be-fresh" rule:

- **Within a unit:** codex session is NEW at R0, then RESUMED for every diff round R1..N. The session retains all prior context, which speeds convergence and lowers per-round cost.
- **Across units:** sessions never share. Each unit gets its own NEW codex cold-start. Per-unit session id at `.codex/session-<unit-key>`.
- **Across phases:** sessions never share. Even when the same flow is referenced by P2 and P4, P4 dispatches a NEW codex session for the cross-app unit.

Rationale: codex new-session is the expensive operation; within-unit resume preserves codex's reasoning across rounds. Cross-unit and cross-phase freshness preserves the convergence integrity that the duo protocol depends on.

## Concurrency

- P1a: 1 unit, sequential first.
- P1b: N units (one per service); parallel up to the shared cap.
- P2: M units (one per flow); parallel up to the shared cap.
- P3: 1 unit, sequential after all P2 commit.
- P4: K units (one per cross-app flow); parallel up to the shared cap.
- P5: 1 unit, sequential final.

Shared cap defaults to 8 across P1b/P2/P4. `high-concurrency` → 16; `very-high-concurrency` → 32.

## Phase 1 — Scope

### P1a Scope File Discovery

Main session spawns 1 Claude subagent (unit key `P1a`). Subagent runs the per-unit protocol.

Per-unit field set:
- `repos[]` — list of repos in workspace (subdir with `.git/`; or CWD if single repo)
- `services_per_repo` — map<repo, list<service>>; services discovered under `apps/<svc>/`, `services/<svc>/`, or top-level if monorepo
- `source_boundaries` — explicit exclusion adjustments beyond the default set (rare)

Commit: `Committed-P1a.md`. Main session reads it; spawns P1b subagents based on services found.

### P1b Per-Service Scope

Main session spawns 1 Claude subagent per (repo, service) from P1a's commit. All parallel up to shared cap.

Per-unit field set per service:
- `candidate_roots[]` — source root paths for this service
- `entrypoints[]` — list of `{file, line, trigger_kind, trigger}` entries (HTTP controllers, Kafka producers/consumers, gRPC, cron, S3, etc.)
- `flow_ids[]` — stable kebab-case flow IDs derived from `trigger + entry symbol` per linked-testplan rule 11

Commit: `Committed-P1b-<repo>-<svc>.md`. Main session aggregates all P1b commits into `.codex/unit-manifest.json` (same schema as duo-testplan-build's manifest). When ALL P1b units have committed, P2 fires.

## Phase 2 — Local Flow Refinement

Main session enumerates flows from `unit-manifest.json` (union across all services). Spawns 1 Claude subagent per flow. Streaming dispatch up to shared cap.

Per-unit field set per flow (per `linked-testplan` page shape):
- `flow_under_test` — trigger, entry `file:line`, brief
- `scenarios[]` — list of scenarios, each with: name (HAPPY|NEGATIVE), preconditions (seeded / inbound / flag / external), steps, expected, mocks, code refs
- `code_refs[]` — flow-level supporting file:line references

Subagent reads source for the flow's entry file, downstream call sites, and any contract definitions referenced. Subagent does NOT read existing tests, READMEs, or `.md` files in the target codebase.

Commit: `Committed-P2-<flow-id>.md` → copy to `test-plan/<repo>/<svc>/flows/<flow-id>.md`.

## Phase 3 — Cross-App Discovery

Main session spawns 1 Claude subagent (unit key `P3`) after ALL P2 units commit.

Subagent inputs:
- All `Committed-P2-*.md` artifacts
- Source roots (for validating cross-repo seams)
- Rulebook (for `crossapp-*` flow ID derivation per rule 11)

Per-unit field set:
- `cross_app_flows[]` — list of `{flow_id, participants, triggering_actor, seam_kind}` for each cross-repo seam (Kafka producer in one repo + consumer in another; REST/gRPC server-client across repos; S3 writer-reader across repos)

1-round cap by default (discovery is enumerative, not deeply contested). User extends with `extended-convergence`.

Commit: `Committed-P3.md`. Main session reads it; spawns P4 subagents.

## Phase 4 — Cross-App Flow Refinement

Main session spawns 1 Claude subagent per cross-app flow from P3's commit. Parallel up to shared cap.

Per-unit field set per cross-app flow (per `linked-testplan` cross-app shape):
- `flow_under_test` — trigger, entry (in the triggering actor), brief
- `scenarios[]` — same shape as P2, but Steps use `<service> → <service>: <action>` actor-prefix form; no internal-mutation steps across the service boundary

Reuses producer-side and consumer-side flow content from P2 as fact (they're already converged). Subagent does NOT re-debate individual flow internals; only argues about the cross-service stitching.

Commit: `Committed-P4-<flow-id>.md` → copy to `test-plan/cross-app/flows/<flow-id>.md`.

## Phase 5 — Result

Main session:

1. Aggregates per-flow files in `test-plan/` (already copied from P2 and P4 commits).
2. Spawns 1 Claude subagent (unit key `P5-sanity`) for a final cross-flow sanity sweep over the full `test-plan/` tree. Per-unit duo protocol applies (round 0 author the sanity findings + round 1+ diff). Output: list of cross-flow contradictions (same topic with incompatible payloads, conflicting expected outcomes for shared deps).
3. Runs `python "$CHECK_REFS_ABS"` over `test-plan/` (ref validation) and again with `--manifest .codex/unit-manifest.json` (entrypoint coverage). Failure output is structured (JSON) and folded into `Result.md → Unresolved`.
4. Writes `Result.md`:

```markdown
# TestPlan Result - <slug>

## Summary
[mission summary]

## Scope
- Repos: [list]
- Services: [list]
- Local flows: <count>
- Cross-app flows: <count>

## Coverage Matrix
| Entrypoint (file:line) | Flow ID | Status |
|---|---|---|
| ... | ... | covered / excluded |

## Convergence
- Per-unit round counts: P1a=<n>, P1b=<avg/max>, P2=<avg/max>, P3=<n>, P4=<avg/max>, P5-sanity=<n>
- [disputed:] tags: <count> across <N units>; listed below.

## Exclusions
- <file:line> — <reason>

## Unresolved
- [disputed:] field listings (per unit)
- check-refs.py failures (if any)
- DEGRADED-CONTINUE / BLOCKED units (if any)
```

5. Appends final `phase_complete` journal event.

## Signaling — DO NOT POLL

Every codex dispatch (per subagent) runs via Bash with `run_in_background: true`. The harness notifies on background completion.

Subagent MUST NOT:
- Poll stream files with sleep loops
- Repeatedly check whether an expected output file exists
- Use mtime-checking loops
- Spawn watcher scripts

Subagent dispatches codex, works in parallel on its Claude-side authoring/diff, STOPS when its side is complete. Next message is harness's bg-completion notification or user interruption. On notification, subagent validates the codex output, applies the merge table, decides commit-vs-next-round.

Main session likewise never polls subagents. Subagents are spawned via Claude Code's Task tool; main session receives their completion notifications and advances phase state.

The dispatch script's internal `monitor_once()` loop is allowed — it runs inside the background process, consumes zero Claude tokens, and enforces the 20-minute per-invocation ceiling.

## Prompt File Authorship

Before any codex dispatch, the subagent writes the full prompt to `.codex/<unit-key>-r${NN}-prompt.txt` using Claude's `Write` tool. The dispatch script does NOT write the prompt; it validates the prompt file is non-empty and pipes it to codex stdin.

Per-round prompt content:

| Round | Prompt includes |
|---|---|
| R0 (author) | Unit's field set spec, manifest slice (for P1b/P2/P4), `$RULEBOOK_ABS`, position-file format, output path |
| R1+ (diff) | All prior-round position files for this unit, source roots, `$RULEBOOK_ABS`, per-field merge stance enum, diff position-file format, output path |

Every prompt names the exact output file path. Every prompt for a diff round instructs the agent to emit ONLY the structured per-field stance, not a rewrite of the artifact.

## Codex Dispatch

Set env vars before invoking. Refer to the dispatch script template in [appendix below]. Per-unit session file is `$MISSION/.codex/session-$UNIT_KEY`. R0 of a unit is fresh; R1+ resume.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?TestPlan}"
UNIT_KEY="${UNIT_KEY:?unit identifier, e.g. P2-post-owners}"
ROUND="${ROUND:?round number 0..N}"
PROMPT_FILE="${PROMPT_FILE:?absolute prompt path}"
WEB_SEARCH="${WEB_SEARCH:-off}"

NN="$(printf "%02d" "$ROUND")"
mkdir -p "$MISSION/.codex"

# Per-unit output convention: round 0 = author file, round NN >= 1 = diff file
if (( ROUND == 0 )); then
  CODEX_OUT="$MISSION/.codex/Author-Codex-$UNIT_KEY.md"
else
  CODEX_OUT="$MISSION/.codex/Diff-Codex-$UNIT_KEY-r$NN.md"
fi

STREAM="$MISSION/.codex/$UNIT_KEY-r$NN-stream.jsonl"
FINAL_CAPTURE="$MISSION/.codex/$UNIT_KEY-r$NN-final.txt"
STDERR_LOG="$MISSION/.codex/$UNIT_KEY-r$NN-stderr.log"
SESSION_FILE="$MISSION/.codex/session-$UNIT_KEY"
HISTORY_FILE="$MISSION/.codex/session-history"
LAUNCH_EPOCH="$(date +%s)"

if [[ ! -s "$PROMPT_FILE" ]]; then
  cat > "$CODEX_OUT" <<EOF
---
Artifact-Kind: dispatch-failure
Unit: $UNIT_KEY
Round: $NN
Status: UNAVAILABLE
---
# $KIND - $UNIT_KEY r$NN (Codex unavailable)
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

# Flag ordering CRITICAL: all flags BEFORE `resume <session>`.
# codex 0.130.0 rejects -C placed AFTER the session id.
# Within-unit resume: round 0 fresh; rounds 1..N resume the same session.
if (( ROUND > 0 )) && [[ -s "$SESSION_FILE" ]]; then
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
  printf '%s resume failed for %s/r%s with status %s\n' \
    "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$OLD_SESSION" "$NN" "$RUN_STATUS" >> "$HISTORY_FILE"
  FALLBACK_PROMPT="$MISSION/.codex/$UNIT_KEY-r$NN-prompt-fallback.txt"
  {
    cat "$PROMPT_FILE"
    printf '\n\n# Resume failed; prior position files pasted for continuity.\n'
    for f in "$MISSION"/.codex/Author-*-$UNIT_KEY.md "$MISSION"/.codex/Diff-*-$UNIT_KEY-r*.md; do
      [[ -f "$f" ]] || continue
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
---
Artifact-Kind: dispatch-failure
Unit: $UNIT_KEY
Round: $NN
Status: UNAVAILABLE
---
# $KIND - $UNIT_KEY r$NN (Codex unavailable)
## Reason
Codex dispatch did not produce a valid output. See $STREAM, $FINAL_CAPTURE, $STDERR_LOG.
## Dispatch Metadata
- Mode: $MODE
- Status: ${RUN_STATUS:-unknown}
- Stalled: ${RUN_STALLED:-unknown}
EOF
fi
```

## Mission Journal

`.codex/journal.jsonl` — append-only, one JSON object per line. Required event types:

| Event | Fields | When |
|---|---|---|
| `phase_start` | `phase`, `ts` | Before any phase artifact write |
| `subagent_spawn` | `phase`, `unit_key`, `cap_consumed` | Before Task() dispatch of a per-unit subagent |
| `round_dispatch` | `unit_key`, `round`, `codex_mode` (fresh\|resume) | Before each codex dispatch within a unit |
| `field_merged` | `unit_key`, `round`, `field`, `outcome` (committed\|unresolved) | After per-field merge table application |
| `unit_committed` | `unit_key`, `rounds_used`, `disputed_field_count` | At unit commit |
| `cap_hit` | `unit_key`, `disputed_fields` | When round cap reached with residual disputes |
| `phase_complete` | `phase`, `unit_count` | At phase exit |
| `mission_halted` | `reason` | On ceiling or fatal failure |

On harness restart, main session reads journal tail to determine resume point. Per-unit `.codex/session-<unit-key>` files persist; subagents resume from R0+ on restart.

## Convergence

Convergence has TWO shapes here, both following yd convention of first-AGREED-pair, no confirmation round.

**Per-unit convergence (per-field):** the subagent's per-field merge table decides field-level outcomes. A field "agrees" when both peers issue compatible stances (see table above). Unit "converges" when all fields agree, OR commits with `[disputed:]` tags at round cap.

**Mission convergence:** all phases complete in order P1a → P1b → P2 → P3 → P4 → P5. P5's sanity duo over the `test-plan/` tree produces the final cross-flow audit. Result.md aggregates.

Same substantive disagreement persisting to round cap → `[disputed:]` tag in committed artifact + journal `cap_hit`. Default mode surfaces unresolved at P5 in `Result.md → Unresolved`. Autonomous mode logs and continues.

## Self-Review

Before each subagent dispatch (R0 or RN), the spawning step (main session for unit spawn, subagent for codex dispatch) verifies:

1. Prompt file exists at the named path and is non-empty.
2. Output path matches the naming convention.
3. Session file presence consistent with round (R0 fresh; R1+ resume).
4. Journal `round_dispatch` record appended.

Before P5 finalization:

1. Coverage matrix complete: every entrypoint maps to flow OR exclusion.
2. `$CHECK_REFS_ABS` passes on the entire `test-plan/**/*.md` tree.
3. No unit in mission folder has `Status: UNAVAILABLE` without a downstream peer-attested resolution or `[disputed:]` tag.
4. All open `phase_start` journal events have corresponding `phase_complete` records.

Fix issues inline. No second review.

## User Feedback

Default mode:
- Ask the user only for USER-TIER blockers (uncommon under this protocol; reserved for cases where a `[disputed:]` field is so foundational that the rest of the artifact is invalid) and budget-warning approval (estimated dispatch count exceeds 800).
- Present concise options with consequences.
- Do not ask the user to resolve ordinary `[disputed:]` fields.

Autonomous mode:
- No USER-TIER blocks. Resolve through `[disputed:]` tagging and peer-attested DEGRADED-CONTINUE/BLOCKED.
- Log unresolved outcomes in `Result.md`.

At the end:
- Present `Result.md` as a clickable link.
- Approve → done. Editorial → Edit inline. Substantive → re-enter affected units by deleting their `Committed-*.md` and re-dispatching.

## Hard Rules

- Direct Codex CLI only — no `/codex:rescue`, no plugin internals.
- Every Codex invocation: `gpt-5.5`, `model_reasoning_effort="xhigh"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `-C "$CWD"`.
- `web_search` is `"off"` by default. Flip to `"live"` only when prose contains `web-allowed`.
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`. codex 0.130.0 rejects `-C` after the session id.
- Never lower `model_reasoning_effort` below `medium`. Pin `xhigh`.
- **Codex sessions: NEW per unit at R0; RESUMED across rounds within the unit's lifecycle; never shared across units or phases.** Deliberate deviation from duo-testplan-build's all-fresh refinement rule.
- **Both peers author every unit, every phase.** No rotation, no asymmetry.
- **Main session is thin top-level coordinator.** Spawn per-unit subagents via Task(). Never run convergence rounds itself.
- **Per-unit Claude subagent owns its convergence cycle.** Self-author at R0; self-diff at R1+. The subagent IS the Claude-side voice.
- **Per-field merge table applied deterministically by the subagent (not LLM).**
- **Convergence is first-AGREED-pair.** No confirmation round.
- **At round cap with residual disputes:** commit fields where peers agreed, tag remaining with `[disputed: claude=..., codex=...]`, journal `cap_hit`. No separate resolver dispatch.
- **Scripts: ONLY `$CHECK_REFS_ABS` at P5.** Never in the LLM convergence loop. No pre-converge filter. No per-phase validators.
- **Code is the only source of truth** — do NOT read existing markdown, READMEs, or tests.
- Mission journal pre-write: every disk write recorded BEFORE the write.
- Claude never polls — wait for harness bg-completion notification.
- No user questions in autonomous mode.
- Root contains only `Result.md` + `test-plan/`; scratch stays in `.codex/`.
- One `.md` per flow in the final `test-plan/` tree.
- Shared concurrency cap 8 across P1b/P2/P4 (overridable via prose modifiers).
- Trigger ONLY on explicit `duo` keyword.

## File Reading Limits

- Use Glob / Grep before broad Read.
- Max 5 files per parallel Read batch.
- Range-read source files > 300 lines.
- Read the linked-testplan rulebook and references selectively per phase.
- Cite `file:line` for every claim in authoring + diff output.
```

## Open Questions

None at USER-TIER. All design decisions locked from the prior convergence with the user. Implementation can proceed.
