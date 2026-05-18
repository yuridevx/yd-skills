---
name: duo-discuss
description: Symmetric Claude+Codex open-ended convergence catch-all - decisions, brainstorming, tradeoff analysis, planning conversations, post-mortems, or questions that don't fit duo-design / duo-research / duo-review / duo-forge. Produces Duo/Discussion-<slug>/Result.md. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh + live web + yolo. TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo discuss X", "duo-discuss X", "/duo-discuss X". Does NOT auto-activate on plain "what do you think about X" / "let's discuss" requests.
---

# Duo Discuss

Run symmetric Claude+Codex open-ended convergence on a topic that doesn't fit any specialized duo-* skill. Catch-all for "I want both your and Codex's best converged thinking on X". Produces `Duo/Discussion-<slug>/Result.md`.

Use cases:
- Comparing approaches before committing to one (lighter than duo-design - no Spec commitment).
- Tradeoff analysis without a design endpoint.
- Pre-design exploration when you're not ready for duo-design's discipline.
- Post-mortem of a finished mission / piece of work.
- Anything else that benefits from two-model convergence but isn't design / research / review / forge.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

Detect autonomous mode same as other duo-* skills. In autonomous mode: never call `AskUserQuestion`. Unresolved choices log under `## Unresolved` in `Result.md`. Default mode: may ask one clarifying question if topic is too vague.

If the request CLEARLY matches `duo-design`, `duo-research`, `duo-review`, or `duo-forge`:
- Default mode: tell the user the better-fit skill and ask whether to switch. (One question, then proceed per their answer.)
- Autonomous mode: proceed with duo-discuss only if discussion remains a reasonable fit; otherwise log the recommendation in `## Unresolved` and continue.

Choose a mission slug: 2-5 PascalCase words from the topic (e.g. `RustVsCppForLoader`, `AuthMigrationStrategy`).

## Mission Folder Layout

```
Duo/Discussion-<slug>/
  Claude-NN.md            position files - visible
  Codex-NN.md             position files - visible
  Result.md               converged artifact - visible
  .codex/                 ALL scratch / state / logs / tmp
    session
    session-history
    rNN-prompt.txt
    rNN-stream.jsonl
    rNN-final.txt
    rNN-stderr.log
```

Root contains only position files + Result.md.

## Discovery Toolbox

Topic-adaptive. Each side picks the procedure that fits the topic and states it in the Investigation section:

1. If the topic touches the codebase → universal entry points + code dive (duo-design procedure).
2. If the topic is about external systems / vendors / frameworks → web-first (duo-research procedure).
3. If the topic is about a finished piece of work → read that work (commits, files, tests, prior `Result.md` files) first, then surrounding context.
4. If the topic is purely conceptual / hypothetical → web for prior art; code only if relevant.

Codex always receives `-c 'web_search="live"'`.

## Phase 1 - Round 1 Parallel Discussion

Both sides investigate and draft positions independently.

Claude writes `Claude-01.md`:

```markdown
# Discussion - Round 1 (Claude investigation)
## Procedure
[Which discovery procedure I picked and why]
## Investigation
- <path>:<line> or <URL> - finding
## Draft
[Initial converged-answer candidate. Shape depends on topic: options, recommendation, rationale, risks, next steps.]
## Open Questions
- [Question] - [why it matters / evidence missing] - [USER-TIER if both sides will likely
  agree user must decide; otherwise expected to resolve in revision]
```

## Signaling - DO NOT POLL

Launch via Bash `run_in_background: true`. Harness notifies on bg completion.

Claude MUST NOT poll. Launch codex, work in parallel on Claude's own draft, STOP when Claude's side is complete. On bg-completion notification, validate `Codex-NN.md` and proceed. Bash-internal `monitor_once()` is allowed.

## Prompt File Authorship

Skill body writes `$MISSION/.codex/r${NN}-prompt.txt` BEFORE dispatch. R1 prompt includes the topic, the user's prose verbatim, the adaptive-procedure note (codex picks its own procedure too), output target. R2+ prompts reference prior position files.

## Codex Dispatch

Set `CWD`, `MISSION`, `KIND=Discussion`, `ROUND`. Run via Bash with `run_in_background: true`.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?Discussion}"
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

Round NN >= 2 uses the standard R2+ format (Status, Agreements, Disagreements, Withdrawals, New issues, full Updated draft, USER-TIER Open Questions only). Editorial nits do not block.

## Convergence

**Convergence = the first round where BOTH sides declare `ALL_AGREED`, raise no new issues, and have no open USER-TIER blockers.** No confirmation round.

Same substantive disagreement persisting 3 rounds → USER-TIER.

## Phase 3 - Result

Write `Duo/Discussion-<slug>/Result.md` using the shape the topic needs. Default structure:

```markdown
# Discussion Result - <slug>
## Bottom Line
## Context
## Evidence
## Options Considered
## Recommendation / Converged Position
## Rationale
## Risks and Mitigations
## Next Steps
## Suggested next skill (optional)
## Unresolved
```

If the discussion clearly points to a design / research / review / forge next step, note it in `## Suggested next skill` but do NOT auto-invoke another skill from this session.

## Self-Review

Check for placeholders, weak assumptions, missing citations where facts matter, internal inconsistencies, whether the answer overreaches the evidence. Fix inline.

## User Feedback

Default: present `Result.md` as a clickable link. Approve → done. Editorial → Edit inline. Substantive → re-enter Phase 2.
Autonomous: present link and exit.

## Hard Rules

- Prefer a specialized duo-* skill when one clearly fits. Default mode: ask once. Autonomous mode: log recommendation in Unresolved and proceed.
- No premature commitment - a duo-discuss `Result.md` is a thinking artifact, not a decision.
- Direct Codex CLI only - no `/codex:rescue`, no plugin internals.
- Every Codex invocation: required flag set (see dispatch).
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`.
- Resume preferred: only R1 of a new mission folder is fresh.
- Never lower `model_reasoning_effort` below `medium`. Pin `xhigh`.
- No user questions in autonomous mode.
- Root contains only position files + `Result.md`; all scratch stays in `.codex/`.
- Claude never polls - wait for harness bg-completion notification.
- Convergence is the first AGREED pair (no confirmation round).

## File Reading Limits

Use search before reads. Read only files/sources needed to ground the discussion. Max 5 parallel Reads.
