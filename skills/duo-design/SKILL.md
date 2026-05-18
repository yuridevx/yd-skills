---
name: duo-design
description: Symmetric Claude+Codex convergence on a system/architecture design, producing Duo/Design-<slug>/Result.md. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh reasoning + live web search + yolo (--dangerously-bypass-approvals-and-sandbox). TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo design X", "duo-design X", "/duo-design X". Does NOT auto-activate on plain "design X" / "spec X" / "architect X" requests. User must explicitly opt into the duo convergence flow.
---

# Duo Design

Run symmetric Claude+Codex design convergence that writes `Duo/Design-<slug>/Result.md`. Direct codex CLI only.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

Detect autonomous mode when prose contains a clear execution phrase: "autonomously", "no questions", "hands-free", "don't ask me", "auto", or "unattended". Distinguish from topic adjectives - "design an autonomous robot" is topic, not mode. In autonomous mode: never call `AskUserQuestion`, never wait for user input between invocation and `Result.md`. USER-TIER blockers and stuck disagreements log under `## Unresolved` in `Result.md`.

Default mode: may ask at most one clarifying question if the design goal is too ambiguous to start. USER-TIER blockers surface in plain prose with `(a)/(b)/(c)` labels only after both sides have exhausted investigation.

Choose a mission slug from the prose: 2-5 PascalCase words, ASCII letters/digits only (e.g. `CacheInvalidation`, `PluginAuthFlow`). If the user names an existing `Duo/Design-<slug>/` folder, reuse it - the dispatch block resumes from `.codex/session` automatically. Otherwise create the folder.

## Mission Folder Layout

```
Duo/Design-<slug>/
  Claude-NN.md            position files - visible
  Codex-NN.md             position files - visible
  Result.md               converged artifact - visible
  .codex/                 ALL scratch / state / logs / tmp - never in root
    session               codex thread id (from the thread.started event)
    session-history       resume-failure log
    rNN-prompt.txt        per-round prompt written by skill body
    rNN-stream.jsonl      codex --json events
    rNN-final.txt         codex --output-last-message
    rNN-stderr.log        codex stderr
```

Root contains only position files + Result.md. Everything else under `.codex/`.

## Discovery Toolbox

Use local and web discovery every round, both sides:

1. Universal entry points: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `README.md` at repo root + subdirectories.
2. Project-specific docs the entry points reference (specs, ADRs, design notes).
3. Code dive on files relevant to the design goal. Cite path:line.
4. Reference services / sibling repos if entry points point at them.
5. Toolkit/library packages: project's curated docs first, installed source as fallback.
6. Web: `WebSearch`, `WebFetch`, context7 MCP - always in the toolbox, not gated. Use for vendor docs, framework specs, RFCs, library APIs.
7. Mission-local memory: prior `Duo/Design-<slug>/Result.md` if mission was reopened.

Cite findings with path:line or URL. Reference, don't transcribe.

## Phase 1 - Round 1 Parallel Investigation

Both sides investigate independently. Codex launched in background via the dispatch fragment below. Claude works in parallel; neither side reads the other's R1 until both are written.

Claude writes `Claude-01.md`:

```markdown
# Design - Round 1 (Claude investigation)
## Investigation
- <path>:<line> or <URL> - finding
## Draft
[Initial design body. Scale sections to topic: goal, context, constraints, proposed
architecture, components, data flow, interfaces, risks, validation, migration, out of scope.]
## Open Questions
- [Question] - [why it matters / evidence missing] - [USER-TIER if both sides will likely
  agree user must decide; otherwise expected to resolve in revision]
```

## Signaling - DO NOT POLL

The dispatch block launches via Claude Code's Bash tool with `run_in_background: true`. The harness automatically delivers a `<task-notification>` to Claude when the background command exits.

Claude MUST NOT:
- Poll stream files with sleep loops
- Repeatedly check whether `Codex-NN.md` exists
- Use `find ... -mmin` mtime checks
- Spawn watcher scripts

Instead: launch codex, continue Claude's own R1/RN work in parallel, STOP when Claude's side is complete. The next message will be either the harness's bg-completion notification or a user interruption. On notification, validate `Codex-NN.md` and proceed to R(N+1) prep.

The bash-internal `monitor_once()` loop in the dispatch is allowed - it runs inside the background process, consumes zero Claude tokens, and enforces the 20-minute hard ceiling so the bg job is guaranteed to terminate.

## Prompt File Authorship

Before invoking the dispatch block, the skill body writes the full round-specific prompt to `$MISSION/.codex/r${NN}-prompt.txt` (using Claude's Write tool - Claude controls every byte). R1 prompts include the goal text, discovery procedure, output target. R2+ prompts include the new round constraints + reference to peer's prior position files.

The dispatch block does NOT write the prompt. It validates `$PROMPT_FILE` is non-empty and pipes it to codex stdin.

## Codex Dispatch

Set `CWD`, `MISSION`, `KIND=Design`, and `ROUND` before invoking. Run via Bash with `run_in_background: true`.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?Design|Research|Review|Discussion|Forge}"
ROUND="${ROUND:?round number}"
NN="$(printf "%02d" "$ROUND")"

mkdir -p "$MISSION/.codex"

CODEX_OUT="$MISSION/Codex-$NN.md"
PROMPT_FILE="$MISSION/.codex/r${NN}-prompt.txt"
STREAM="$MISSION/.codex/r${NN}-stream.jsonl"
FINAL_CAPTURE="$MISSION/.codex/r${NN}-final.txt"
STDERR_LOG="$MISSION/.codex/r${NN}-stderr.log"
SESSION_FILE="$MISSION/.codex/session"
HISTORY_FILE="$MISSION/.codex/session-history"
LAUNCH_EPOCH="$(date +%s)"

if [[ ! -s "$PROMPT_FILE" ]]; then
  cat > "$CODEX_OUT" <<EOF
# $KIND - Round $NN (Codex unavailable)

## Investigation
- Prompt file missing or empty: $PROMPT_FILE.

## Draft
Codex was not launched - skill body did not write the prompt file.

## Open Questions
- Dispatch precondition failure is not a substantive disagreement.
EOF
  exit 2
fi

mtime_epoch() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }

CODEX_FLAGS=(
  --dangerously-bypass-approvals-and-sandbox
  -m gpt-5.5
  -c 'model_reasoning_effort="xhigh"'
  -c 'web_search="live"'
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

# Flag ordering is CRITICAL: -C and all flags must come BEFORE `resume <session>`.
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
  FALLBACK_PROMPT="$MISSION/.codex/r${NN}-prompt-fallback.txt"
  {
    cat "$PROMPT_FILE"
    printf '\n\n# Resume failed; prior position files pasted for continuity.\n'
    for f in "$MISSION"/Claude-*.md "$MISSION"/Codex-*.md; do
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
# $KIND - Round $NN (Codex unavailable)

## Investigation
- Codex dispatch did not produce a valid position file. See $STREAM, $FINAL_CAPTURE, $STDERR_LOG.

## Draft
Codex unavailable for this round. Claude continues with its own draft + validated prior Codex positions.

## Open Questions
- Dispatch failure is not a substantive disagreement.

## Dispatch Metadata
- Mode: $MODE
- Status: ${RUN_STATUS:-unknown}
- Stalled: ${RUN_STALLED:-unknown}
EOF
fi
```

## Phase 2 - Mutual Revision

Round NN >= 2: Claude reads `Codex-(NN-1).md`, writes `Claude-NN.md` per the R2+ position-file format. Then the skill body builds `.codex/rNN-prompt.txt` (referencing the prior position files) and dispatches Codex. Codex resumes, reads `Claude-(NN-1).md` and `Claude-NN.md`, writes `Codex-NN.md`.

Round 2+ position-file format:

```markdown
# Design - Round NN (Claude, mutual revision)
## Status vs peer's Round (NN-1)
ALL_AGREED | DISAGREEMENTS_REMAIN
## Agreements added since my Round (NN-1)
- [Point I now accept] - [why peer's argument convinced me]
## Disagreements with peer's Round (NN-1)
- [Specific point] - [my position] - [evidence: path:line / URL / doc section] - [counter-proposal]
## Withdrawals from my Round (NN-1)
- [Point I'm dropping] - [why]
## New issues raised
- [Issue] - [evidence] - [my position]
## Updated draft
[Full revised design body - replace, don't diff]
## Open Questions
- [USER-TIER blockers only]
```

Editorial / phrasing / naming / formatting nits NEVER block convergence - silently accept in updated draft, do NOT list as disagreements.

## Convergence

**Convergence = the first round where BOTH sides declare `ALL_AGREED`, raise no new issues, and have no open USER-TIER blockers.** No confirmation round. Proceed directly to Phase 3.

Same substantive disagreement persisting 3 consecutive rounds without progress → USER-TIER (surfaced in default mode, logged to `Result.md` `## Unresolved` in autonomous mode).

Both sides must exhaust the discovery procedure before flagging USER-TIER. Default posture: find the answer in what exists; only escalate when no source decides.

## Phase 3 - Result

Write `Duo/Design-<slug>/Result.md`:

```markdown
# Design Result - <slug>
## Summary
## Goals
## Non-Goals
## Evidence
## Proposed Architecture
## Components and Responsibilities
## Data Flow / Control Flow
## Interfaces and Contracts
## Failure Modes
## Migration / Rollout
## Validation Plan
## Tradeoffs
## Unresolved
```

Omit sections that truly do not apply. Keep `## Unresolved` (write `None` if empty).

## Self-Review

Before presenting `Result.md`, scan with fresh eyes:
1. Placeholder scan - TBD / TODO / "fill in details" → fix inline.
2. Internal consistency - sections contradicting each other? architecture matches features?
3. Scope check - focused enough for one implementation, or needs decomposition?
4. Ambiguity check - any requirement interpretable two ways? pick one, make it explicit.

Fix issues inline. No second review.

## User Feedback

Default mode: present `Result.md` as a clickable link. Wait for user.
- Approve → done.
- Editorial changes → apply via Edit tool inline. Re-present.
- Substantive changes → re-enter Phase 2 with the user's input as a new constraint. Re-run convergence. Re-present.

Autonomous mode: present the link and exit.

## Hard Rules

- Direct Codex CLI only - no `/codex:rescue`, no plugin internals, no shared helper skill.
- Every Codex invocation: `gpt-5.5`, `model_reasoning_effort="xhigh"`, `web_search="live"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `-C "$CWD"`.
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`. codex 0.130.0 rejects `-C` placed after the session id.
- Resume preferred: only R1 of a brand-new mission folder is fresh. Mission folders with existing `.codex/session` always resume.
- Never lower `model_reasoning_effort` below `medium` - `web_search` is incompatible with `minimal`. This family pins `xhigh` always.
- Web is always on (codex `web_search="live"` + Claude WebSearch/WebFetch/context7).
- No user questions in autonomous mode.
- Root contains only position files + `Result.md`; all scratch stays in `.codex/`.
- Claude never polls for codex completion - wait for harness bg-completion notification.
- Convergence is the first AGREED pair (no confirmation round).
- No implementation code in duo-design output.

## File Reading Limits

Glob/Grep before Read. Max 5 files per parallel Read batch. Range-read files >300 lines. Cite path:line.
