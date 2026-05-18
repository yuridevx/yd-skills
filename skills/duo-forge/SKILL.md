---
name: duo-forge
description: Meta-skill - uses the duo convergence protocol to design a new duo-<name> skill for a requested domain. R1 evaluates three gating criteria (pattern recurs across missions / artifact has stable shape / domain has definable investigation procedure); if both sides converge on REJECT, writes only a reject rationale. If converge on CREATE, writes ~/.claude/skills/duo-<name>/SKILL.md plus mission Result.md. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh + live web + yolo. TRIGGERS ONLY on explicit "duo" keyword - phrases like "duo forge X", "duo-forge X", "/duo-forge X", "duo make a skill for X". Does NOT auto-activate on plain "make a skill" / "create a skill" requests.
---

# Duo Forge

Drink your own kool-aid. Use the duo convergence protocol to design a new `duo-<name>` skill. The artifact being negotiated IS a SKILL.md. Produces `Duo/Forge-<slug>/Result.md` and, on CREATE, `~/.claude/skills/duo-<new-name>/SKILL.md`. Direct codex CLI only.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

Detect autonomous mode same as other duo-* skills. In autonomous mode: never call `AskUserQuestion`. Missing preferences and gating uncertainty log under `## Unresolved` in `Result.md`. Default mode: may ask one clarifying question if the proposed skill domain cannot be inferred.

Infer from prose:
- **Domain** of the new skill (e.g. "security audit", "perf benchmarking", "API surface design")
- **New skill name** = `duo-<kebab-case-domain>` (lowercase letters/digits/hyphens, max 64 chars, must start with `duo-`)
- **Artifact hint** (optional) = if prose says "the result should be X" / "output X" / "produce X"
- **Examples hint** (optional) = if prose says "for example X" / "use cases like Y"

Mission slug for the forge run itself = `Forge<NewSkillKebabAsPascal>` (e.g. forging `duo-security-audit` → mission folder `Duo/Forge-SecurityAudit/`).

## Mission Folder Layout

```
Duo/Forge-<slug>/
  Claude-NN.md            position files - visible
  Codex-NN.md             position files - visible
  Result.md               forge outcome (CREATE or REJECT) - visible
  .codex/                 ALL scratch / state / logs / tmp
    session
    session-history
    rNN-prompt.txt
    rNN-stream.jsonl
    rNN-final.txt
    rNN-stderr.log
```

If CREATE: ALSO writes `~/.claude/skills/duo-<new-name>/SKILL.md`.
If REJECT: ONLY `Result.md` (with rationale + alternative suggestion).

## Gating Criteria

Round 1 MUST evaluate all three before drafting a SKILL.md:

1. **Pattern recurs across missions** - will this skill be invoked multiple times on different topics in the same shape? Or is the request a one-shot that should be a direct conversation, not a skill?
2. **Artifact has a stable shape** - can we describe a `Result.md` schema that's consistent across invocations?
3. **Domain has a definable investigation procedure** - is there a procedure both sides can follow consistently?
4. **Distinct from existing duo-* skills** - does this domain not fit duo-design / duo-research / duo-review / duo-discuss?

If R1 finds any criterion fails, the Draft must include a REJECT verdict with rationale + suggested alternative (which existing duo-* skill to use, or "this is a one-shot; don't make a skill").

## Discovery Toolbox

1. Read existing `duo-*` skills at `~/.claude/skills/duo-*/SKILL.md` for conventions (frontmatter, section order, dispatch block, hard rules).
2. Read sibling `duet-*` skills (if relevant) for additional patterns; explicitly do NOT copy their `/codex:rescue` dispatch.
3. `WebSearch`, `WebFetch`, context7 MCP for the domain (e.g. forging `duo-security-audit` → OWASP checklists, threat-modeling references).
4. Inspect local examples and prior `Duo/` artifacts when domain is rooted in repeated work.
5. Codex always receives live web.

## Phase 1 - Round 1 Parallel Forge

Both sides evaluate gates and draft either a new SKILL.md (CREATE) or a reject rationale (REJECT). Codex launched in background.

Claude writes `Claude-01.md`:

```markdown
# Forge - Round 1 (Claude investigation)

## Investigation
- <path>:<line> or <URL> - finding
- Sibling duo-* skills reviewed: ~/.claude/skills/duo-{design,research,review,discuss}/SKILL.md

## Gating Evaluation
- Pattern recurs across missions? - YES | NO - [evidence]
- Stable artifact shape? - YES | NO - [proposed schema or why not]
- Definable investigation procedure? - YES | NO - [proposed procedure or why not]
- Distinct from existing duo-*? - YES | NO - [why]
- **Verdict:** CREATE | REJECT

## Draft (CREATE branch)
[Full SKILL.md draft:
  - frontmatter (name=duo-<new-name>, description with trigger text using "duo" keyword discipline)
  - body following duo-* convention: When Invoked / Mission Folder Layout / Discovery Toolbox /
    Phase 1 / Signaling / Prompt File Authorship / Codex Dispatch (inlined verbatim) /
    Phase 2 / Convergence (first AGREED pair) / Phase 3 / Self-Review / User Feedback /
    Hard Rules / File Reading Limits]

## Reject rationale (REJECT branch)
- Failed criterion(s): [list]
- Suggested alternative: [existing duo-* skill that fits, OR "don't make this a skill - one-shot conversation is sufficient"]

## Open Questions
- [USER-TIER blockers only]
```

## Signaling - DO NOT POLL

Launch via Bash `run_in_background: true`. Harness notifies on bg completion.

Claude MUST NOT poll. Launch codex, work in parallel on Claude's own forge draft, STOP when Claude's side is complete. On bg-completion notification, validate `Codex-NN.md` and proceed. Bash-internal `monitor_once()` is allowed.

## Prompt File Authorship

Skill body writes `$MISSION/.codex/r${NN}-prompt.txt` BEFORE dispatch. R1 prompt includes the proposed domain, the gating criteria, the discovery procedure, the user's prose verbatim, and the position-file format above. R2+ prompts reference prior position files + any user-tier resolution.

## Codex Dispatch

Set `CWD`, `MISSION`, `KIND=Forge`, `ROUND`. Run via Bash with `run_in_background: true`.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?Forge}"
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
Codex unavailable for this round. Claude continues with its own forge draft + validated prior Codex positions.

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

Round NN >= 2: each side may withdraw points, adopt peer's points, raise new issues.

R2+ format:

```markdown
# Forge - Round NN (Claude, mutual revision)
## Status vs peer's Round (NN-1)
ALL_AGREED | DISAGREEMENTS_REMAIN
## Agreements added since my Round (NN-1)
- [Point I now accept] - [why peer's argument convinced me]
## Disagreements with peer's Round (NN-1)
- [Gate, skill shape, dispatch detail, or verdict point] - [my position] - [evidence] - [counter-proposal]
## Withdrawals from my Round (NN-1)
- [Point I'm dropping] - [why]
## New issues raised
- [Issue] - [evidence] - [my position]
## Verdict (current)
CREATE | REJECT
## Updated draft
[Full revised proposed SKILL.md (CREATE) OR reject rationale (REJECT)]
## Open Questions
- [USER-TIER blockers only]
```

**Verdict must converge first.** Both sides must agree on CREATE vs REJECT before settling on draft details. If one side says CREATE and other says REJECT after 3 rounds → USER-TIER.

## Convergence

**Convergence = the first round where BOTH sides declare `ALL_AGREED`, agree on the same Verdict (CREATE or REJECT), raise no new issues, and have no open USER-TIER blockers.** No confirmation round.

Same substantive disagreement persisting 3 rounds → USER-TIER.

## Phase 3 - Write Artifacts

### If CREATE:

1. Write `~/.claude/skills/duo-<new-name>/SKILL.md` from the converged draft. Verify:
   - Frontmatter `name:` matches the directory name (`duo-<new-name>`)
   - `description:` includes the "duo" keyword trigger discipline
   - Codex Dispatch block is inlined verbatim (no shared helper)
   - All standard sections present: When Invoked / Mission Folder Layout / Discovery Toolbox / Phase 1 / Signaling - DO NOT POLL / Prompt File Authorship / Codex Dispatch / Phase 2 / Convergence (first AGREED pair) / Phase 3 / Self-Review / User Feedback / Hard Rules / File Reading Limits
   - Hard Rules include: direct codex CLI only, the required flag set, flag ordering, never below `medium` reasoning, no user questions in autonomous mode, root-cleanliness, no-polling rule
2. If the new skill needs non-default templates (rare): write under `~/.claude/skills/duo-<new-name>/templates/`. Most domains don't need this.
3. Write mission `Result.md`:

```markdown
# Forge Result - duo-<new-name>

## Decision
CREATE

## Gate Evaluation
- Pattern recurs: YES - [evidence]
- Stable artifact shape: YES - [schema]
- Definable investigation procedure: YES - [procedure]
- Distinct from existing duo-*: YES - [why]

## Convergence Narrative
[Round count, key decisions, any USER-TIER blockers resolved]

## Installed File
`~/.claude/skills/duo-<new-name>/SKILL.md`

## Test Invocation
/duo-<new-name> <example prose from the design>

## SKILL.md
[Full installed skill body for reference]

## Unresolved
- [None, or specific user-tier items the user should be aware of]
```

### If REJECT:

1. Write mission `Result.md`:

```markdown
# Forge Result - duo-<proposed-name>

## Decision
REJECT

## Failed Gates
- [Gate] - [why it failed - evidence]

## Rationale
[Why a dedicated skill isn't justified]

## Suggested Alternative
- Use existing duo-<other>, OR
- Treat as a one-shot conversation - no skill needed

## Unresolved
- [None, or items requiring user input]
```

2. Do NOT write anything to `~/.claude/skills/`.

## Self-Review (CREATE only)

Before writing into `~/.claude/skills/`:
1. Frontmatter sanity - `name` matches dir, `description` has "duo" keyword trigger discipline
2. Codex Dispatch block inlined verbatim (no shared helper dependency)
3. All standard sections present (per Phase 3 CREATE checklist above)
4. No `/codex:rescue` references, no Agent subagent dispatch, no plugin-internal calls
5. Hard Rules include the convergence-is-first-AGREED-pair rule, the no-polling rule, the root-cleanliness rule

Fix inline. No second review.

## User Feedback

Default: present `Result.md` as a clickable link. If CREATE, also present the installed `SKILL.md` path + test-invocation suggestion. Approve → done. Editorial → Edit inline (on `Result.md` or the installed `SKILL.md`). Substantive → re-enter Phase 2.

Autonomous: present link(s) and exit.

## Hard Rules

- Direct Codex CLI only - no `/codex:rescue`, no plugin internals.
- Every Codex invocation: required flag set (see dispatch).
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`.
- Resume preferred: only R1 of a new mission folder is fresh.
- Never lower `model_reasoning_effort` below `medium`. Pin `xhigh`.
- **Gating must converge BEFORE drafting.** Both sides agree CREATE vs REJECT first.
- **Dispatch fragment inlined verbatim** in every forged skill. No shared helper.
- **No write to `~/.claude/skills/` on REJECT.**
- **New skill names**: lowercase letters/digits/hyphens, start with `duo-`, max 64 chars.
- **Forged skills inherit the convergence-is-first-AGREED-pair rule.** Do NOT add a confirmation round.
- **Forged skills inherit the "TRIGGERS ONLY on duo keyword" trigger discipline** in their `description:`.
- No user questions in autonomous mode.
- Root contains only position files + `Result.md`; all scratch stays in `.codex/`.
- Claude never polls - wait for harness bg-completion notification.

## File Reading Limits

Read existing skills selectively (skim frontmatter + section list first). Max 5 parallel Reads. Range-read files >300 lines.
