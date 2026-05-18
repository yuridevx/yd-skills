---
name: duo-review
description: Symmetric Claude+Codex code-review convergence on a branch, PR, diff, commit, or paths, producing Duo/Review-<slug>/Result.md with file:line-grounded findings + verdict (PASS / PASS_WITH_GAPS / FAIL / BLOCKED). Read-only - no code edits. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh + live web + yolo. TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo review X", "duo-review X", "/duo-review X". Does NOT auto-activate on plain "review X" / "audit X" / "check the PR" requests.
---

# Duo Review

Run symmetric Claude+Codex code review that writes `Duo/Review-<slug>/Result.md`. Read-only - no code edits. Direct codex CLI only.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

Detect autonomous mode same as other duo-* skills. In autonomous mode: never call `AskUserQuestion`. Ambiguous base branch, unavailable PR metadata, or USER-TIER tradeoffs log under `## Unresolved`. If review target is ambiguous, autonomous mode picks current-branch-vs-merge-base default and logs the assumption.

Default mode: may ask one clarifying question if there is no review target. If there is a reasonable default (current working tree vs merge base / HEAD), proceed and state the assumption in the position files.

Infer review target from prose:
- "PR 123" / "pull request 123" → `gh pr diff 123` (resolve commits, save full diff)
- "branch foo" / "this branch" → `git diff <merge-base>...foo`
- "the diff" / "current changes" → `git diff` + `git diff --staged`
- "files X, Y, Z" / "src/foo/" → those paths, full content

Slug: target + topic, e.g. `Pr123Checkout`, `AuthDiff`, `LoaderRefactor`. If the user names an existing `Duo/Review-<slug>/` folder, reuse it.

## Mission Folder Layout

```
Duo/Review-<slug>/
  Claude-NN.md            position files - visible
  Codex-NN.md             position files - visible
  Result.md               converged verdict - visible
  .codex/                 ALL scratch / state / logs / tmp
    session
    session-history
    rNN-prompt.txt
    rNN-stream.jsonl
    rNN-final.txt
    rNN-stderr.log
    scope.diff             resolved diff (review-specific)
    scope.files            list of touched files
```

Root contains only position files + Result.md.

## Discovery Toolbox

1. Resolve review scope FIRST. Save diff to `.codex/scope.diff` and file list to `.codex/scope.files`. Skill body uses `git diff` / `gh pr diff` / etc. Do not modify code.
2. Read touched files in FULL (not just diff hunks), nearby callers/callees, tests for the changed paths.
3. Universal entry points (`CLAUDE.md` etc.) for project-specific review conventions.
4. `git log -p <file>` for changed files (last ~10 commits per file) - look for prior fix patterns / reverts.
5. `WebSearch`, `WebFetch`, context7 MCP for current library semantics, CVE references, framework behavior, external API contracts.
6. Codex always receives live web.

Review for: correctness, security, regressions, missing tests, compatibility, data loss, concurrency, migrations, observability, operational risk. Do NOT block on style/naming nits.

## Phase 1 - Round 1 Parallel Review

Both sides review independently. Codex launched in background.

Claude writes `Claude-01.md`:

```markdown
# Review - Round 1 (Claude investigation)
## Investigation
- <path>:<line> or <command/source> - finding context
## Findings
- Severity: HIGH | MEDIUM | LOW
  Finding: <specific defect/risk>
  Evidence: <path:line, diff hunk, command output, URL>
  Impact: <behavioral consequence>
  Suggested fix: <minimal correction>
## Verdict (preliminary)
PASS | PASS_WITH_GAPS | FAIL | BLOCKED
## Open Questions
- [USER-TIER blockers only]
```

Severities:
- HIGH - correctness, security, data-loss, contract breakage.
- MEDIUM - performance regression, maintainability hazard, missing test for risky path.
- LOW - code smell with concrete fix.
- INFO - observation only, no action.

## Signaling - DO NOT POLL

Launch via Bash `run_in_background: true`. Harness notifies on bg completion.

Claude MUST NOT poll stream files, repeatedly check for `Codex-NN.md`, run mtime loops, or spawn watchers. Launch codex, work in parallel on Claude's own review, STOP when Claude's side is complete. On bg-completion, validate `Codex-NN.md` and proceed.

Bash-internal `monitor_once()` is allowed.

## Prompt File Authorship

Skill body writes `$MISSION/.codex/r${NN}-prompt.txt` BEFORE dispatch. R1 prompt includes the resolved review scope (with `.codex/scope.diff` and `.codex/scope.files` as input), review rubric, output target. R2+ prompts include prior position files.

## Codex Dispatch

Set `CWD`, `MISSION`, `KIND=Review`, `ROUND`. Run via Bash with `run_in_background: true`.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?Review}"
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
Codex unavailable for this round. Claude continues with its own findings + validated prior Codex positions.

## Open Questions
- Dispatch failure is not a substantive disagreement.

## Dispatch Metadata
- Mode: $MODE
- Status: ${RUN_STATUS:-unknown}
- Stalled: ${RUN_STALLED:-unknown}
EOF
fi
```

## Phase 2 - Mutual Revision on Findings

Round NN >= 2: each side may withdraw a finding (peer convinced me it's false positive), adopt a finding (peer surfaced something I missed), disagree on severity, or raise new findings.

R2+ format:

```markdown
# Review - Round NN (Claude, mutual revision)
## Status vs peer's Round (NN-1)
ALL_AGREED | DISAGREEMENTS_REMAIN
## Agreements added since my Round (NN-1)
- [Finding/severity/verdict I now accept] - [why peer's evidence convinced me]
## Disagreements with peer's Round (NN-1)
- [Specific finding or severity] - [my position] - [evidence: path:line, diff hunk, URL] - [counter-proposal]
## Withdrawals from my Round (NN-1)
- [Finding I'm dropping] - [why - false positive / off-scope]
## New issues raised
- [Issue] - [evidence] - [severity]
## Updated findings list (full, replaces previous)
[Complete list of remaining findings - same format as R1]
## Verdict (current)
PASS | PASS_WITH_GAPS | FAIL | BLOCKED
## Open Questions
- [USER-TIER blockers only]
```

Style / naming / formatting nits NEVER block convergence and NEVER appear in findings.

## Convergence

**Convergence = the first round where BOTH sides declare `ALL_AGREED`, produce identical findings lists (same findings, same severities), and have no open USER-TIER blockers.** No confirmation round.

Same substantive disagreement persisting 3 rounds → USER-TIER.

## Phase 3 - Result

Write `Duo/Review-<slug>/Result.md`:

```markdown
# Review Result - <slug>

**Status:** PASS | PASS_WITH_GAPS | FAIL | BLOCKED
**Reviewed Target:** <description; resolved to .codex/scope.diff + .codex/scope.files>
**Reviewed at:** <ISO-8601 timestamp>

## Commands run
- `<command>` - <result>

## Findings
### High severity
- ...
### Medium severity
- ...
### Low / informational
- ...

## Test Gaps
- <verifiable behavior with no test, with concrete obstacle to writing one>

## Positive Notes
- <non-trivial things genuinely worth calling out as well-done>

## Unresolved
- <autonomous-mode 3-round-stuck blockers, or items the user must decide>

## Evidence Appendix
- <diff hunks, file:line refs, command outputs cited above>
```

Verdict definitions:
- **PASS** - no HIGH/MEDIUM findings remain, target reviewable.
- **PASS_WITH_GAPS** - no blocking findings, but explicit verification gaps remain.
- **FAIL** - substantive findings need changes.
- **BLOCKED** - target could not be reviewed (no diff, ambiguous spec, etc.).

## Self-Review

Check every finding for: concrete evidence, behavioral impact, correct severity, non-duplication, plausible suggested fix. Remove editorial-only comments. Fix inline.

## User Feedback

Default: present `Result.md` as a clickable link. Approve → done. Editorial → Edit inline. Substantive → re-enter Phase 2.
Autonomous: present link and exit.

## Hard Rules

- Direct Codex CLI only - no `/codex:rescue`, no plugin internals.
- Every Codex invocation: `gpt-5.5`, `model_reasoning_effort="xhigh"`, `web_search="live"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `-C "$CWD"`.
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`.
- Resume preferred: only R1 of a new mission folder is fresh.
- Never lower `model_reasoning_effort` below `medium`. Pin `xhigh`.
- **Review only - no code edits by either side.** If the user wants fixes, that's a separate turn / skill.
- Findings require evidence AND behavioral impact.
- No editorial / style / naming findings - substantive correctness/security/perf/contract only.
- Severities are converged - both sides must agree on a finding's severity before it goes in Result.md.
- No user questions in autonomous mode.
- Root contains only position files + `Result.md`; all scratch stays in `.codex/`.
- Claude never polls - wait for harness bg-completion notification.
- Convergence is the first AGREED pair (no confirmation round).

## File Reading Limits

Use `git diff` and search first. Read touched files plus necessary call sites. Max 5 parallel Reads. Range-read files >300 lines.
