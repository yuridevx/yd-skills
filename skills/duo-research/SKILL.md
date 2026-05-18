---
name: duo-research
description: Symmetric Claude+Codex convergence on a research deliverable, producing Duo/Research-<slug>/Result.md. Web access central on both sides. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh + live web + yolo. TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo research X", "duo-research X", "/duo-research X". Does NOT auto-activate on plain "research X" / "compare X vs Y" / "investigate X" requests. User must explicitly opt into the duo convergence flow.
---

# Duo Research

Run symmetric Claude+Codex research convergence that writes `Duo/Research-<slug>/Result.md`. Web access is central, not optional. Direct codex CLI only.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

Detect autonomous mode when prose contains a clear execution phrase: "autonomously", "no questions", "hands-free", "don't ask me", "auto", or "unattended". Distinguish from topic adjectives. In autonomous mode: never call `AskUserQuestion`. Missing user preferences, unavailable sources, paywalls, or unresolved source conflicts log under `## Unresolved` in `Result.md`.

Default mode: may ask one clarifying question if the research target cannot be identified. Otherwise start.

Choose a mission slug: 2-5 PascalCase words from the topic (e.g. `CodexCliSurvey`, `OAuth2VendorMatrix`). If the user names an existing `Duo/Research-<slug>/` folder, reuse it - the dispatch resumes from `.codex/session`. Otherwise create it.

## Mission Folder Layout

```
Duo/Research-<slug>/
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

Web is primary, not supplemental:

1. `WebSearch` for source discovery, recency checks, competing claims, official sources.
2. `WebFetch` for primary pages, PDFs, papers, laws, standards, vendor docs, cited articles.
3. context7 MCP for current library/API documentation when research concerns software behavior.
4. Local repo files and prior `Duo/` artifacts only when research is project-specific.
5. Codex always receives `-c 'web_search="live"'`.

Prefer primary sources. Record source dates and access dates when recency matters. Do not let secondary summaries override primary evidence. Avoid source sprawl - gather enough independent primary evidence to answer the question, then stop.

## Phase 1 - Round 1 Parallel Research

Both sides gather sources and draft independently. Codex launched in background via the dispatch fragment below.

Claude writes `Claude-01.md`:

```markdown
# Research - Round 1 (Claude investigation)
## Investigation
- <URL or path:line> - finding, source type, date/access note when recency matters
## Draft
[Initial deliverable: answer, evidence, source comparison, confidence per claim, caveats, recommendations if requested.]
## Open Questions
- [Question] - [why it matters / evidence missing] - [USER-TIER if both sides will likely
  agree user must decide; otherwise expected to resolve in revision]
```

## Signaling - DO NOT POLL

Launch via Bash `run_in_background: true`. The harness notifies Claude when the bg command exits.

Claude MUST NOT poll stream files, repeatedly check for `Codex-NN.md`, run mtime loops, or spawn watchers. Launch codex, work in parallel on Claude's own R/N, STOP when Claude's side is complete. On the bg-completion notification, validate `Codex-NN.md` and proceed.

The bash-internal `monitor_once()` is allowed - it runs inside the background process, consumes zero Claude tokens, and enforces the 20-minute hard ceiling.

## Prompt File Authorship

The skill body writes the full round prompt to `$MISSION/.codex/r${NN}-prompt.txt` BEFORE dispatch (using Claude's Write tool). R1 prompts include the research question, scope, source-quality rules, output target. R2+ prompts include peer position files + source disputes to resolve. Dispatch reads `$PROMPT_FILE`; it does NOT write the prompt.

## Codex Dispatch

Set `CWD`, `MISSION`, `KIND=Research`, `ROUND` before invoking. Run via Bash with `run_in_background: true`.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?Research}"
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

# Flag ordering: all flags BEFORE `resume <session>`.
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

Round NN >= 2: Claude reads `Codex-(NN-1).md`, writes `Claude-NN.md` per the R2+ format. Skill body builds `.codex/rNN-prompt.txt` referencing prior position files; dispatches Codex with resume.

R2+ format:

```markdown
# Research - Round NN (Claude, mutual revision)
## Status vs peer's Round (NN-1)
ALL_AGREED | DISAGREEMENTS_REMAIN
## Agreements added since my Round (NN-1)
- [Point I now accept] - [why peer's source/evidence convinced me]
## Disagreements with peer's Round (NN-1)
- [Specific claim] - [my position] - [evidence: URL/path:line/date] - [counter-proposal]
## Withdrawals from my Round (NN-1)
- [Point I'm dropping] - [why]
## New issues raised
- [Issue] - [evidence] - [my position]
## Updated draft
[Full revised research deliverable - replace, don't diff]
## Open Questions
- [USER-TIER blockers only]
```

Source quality disagreements are substantive. Editorial wording, section ordering, headings are NOT - silently accept.

## Convergence

**Convergence = the first round where BOTH sides declare `ALL_AGREED`, raise no new issues, and have no open USER-TIER blockers.** No confirmation round.

Same substantive disagreement persisting 3 rounds without progress → USER-TIER.

## Phase 3 - Result

Write `Duo/Research-<slug>/Result.md`:

```markdown
# Research Result - <slug>
## Executive Summary
## Scope and Method
## Key Findings
## Evidence Table
| Claim | Evidence | Source Type | Date / Access Note | Confidence |
## Source Comparison
## Analysis
## Recommendations
## Limitations
## Unresolved
## Bibliography
```

Use inline citations or footnotes consistently. Avoid long quotations - summarize unless a short exact quote is necessary.

## Self-Review

Check placeholder text, source coverage, quote limits, date consistency, claim/source alignment, confidence labels, and whether any recommendation exceeds the evidence. Fix inline.

## User Feedback

Default: present `Result.md` as a clickable link. Approve → done. Editorial → Edit inline. Substantive → re-enter Phase 2.
Autonomous: present link and exit.

## Hard Rules

- Direct Codex CLI only - no `/codex:rescue`, no plugin internals.
- Every Codex invocation: `gpt-5.5`, `model_reasoning_effort="xhigh"`, `web_search="live"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `-C "$CWD"`.
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`. codex 0.130.0 rejects `-C` after the session id.
- Resume preferred: only R1 of a brand-new mission folder is fresh.
- Never lower `model_reasoning_effort` below `medium` - `web_search` is incompatible with `minimal`. Pin `xhigh` always.
- Web is mandatory, not optional. A duo-research mission where neither side hit the web is malformed - restart.
- No claims without sources - every fact gets a URL or path:line citation.
- No user questions in autonomous mode.
- Root contains only position files + `Result.md`; all scratch stays in `.codex/`.
- Claude never polls - wait for harness bg-completion notification.
- Convergence is the first AGREED pair (no confirmation round).

## File Reading Limits

Use search before broad reads. Read focused ranges. Max 5 files per parallel Read batch. For web: gather enough independent primary evidence to answer the question, then stop.
