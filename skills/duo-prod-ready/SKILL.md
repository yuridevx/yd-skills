---
name: duo-prod-ready
description: 'Production-readiness refactoring through Claude+Codex convergence that WRITES CODE. Modifies the working tree. Runs build+test. Commits per cycle. Direct codex CLI only - no /codex:rescue, no plugin internals; depends only on `codex` on PATH. Pins gpt-5.5 + xhigh reasoning + live web search + yolo. TRIGGERS ONLY on explicit "duo" keyword with prod-ready: `/duo-prod-ready <scope>`, `duo prod-ready <scope>`, or `duo-prod-ready <scope>`. Scope is REQUIRED: `.` for whole repo, a category such as `dead-code` or `security`, or a path. Supports only `--autonomous`, `--bold`, prose-triggered coder role selection, and prose-triggered `fast` (Codex service tier "fast", 1.5x speed, no behavioral change). Coder defaults to Claude; Codex is coder only when prose says "codex codes", "codex writes", "codex is the coder", "codex as coder", "let codex code", or "codex writer". Fast tier activates when prose says "fast", "fast mode", "fast tier", "speed mode", "service tier fast", or "1.5x". Does NOT auto-activate on plain "refactor X" / "clean up X" / "production ready X" requests.'
---

# Duo Prod Ready

Run iterative production-readiness refactoring through duo convergence. This skill writes code, applies patches, runs verification, and commits once per successful macro cycle.

## When Invoked

Parse the user's prose as the only argument source.

Trigger only on explicit forms:
- `/duo-prod-ready <scope>`
- `duo prod-ready <scope>`
- `duo-prod-ready <scope>`

Reject bare invocation with:

```text
Usage: /duo-prod-ready <scope> [--autonomous] [--bold]
Scope is required: "." for whole repo, a category such as "dead-code" or "security", or a path.
```

Never auto-activate on plain "refactor X", "clean up X", "production ready X", or similar requests without the explicit duo prod-ready trigger.

Parse only these flags and role selectors:
- Default mode: user-tier blocks are surfaced to the user.
- `--autonomous`: no user-tier blocks; resolve through convergence and signal-based escalation handshakes, logging unresolved outcomes in `Result.md` when needed.
- `--bold`: unlock public-surface changes such as API renames, module restructuring, and dead-feature removal, subject to the BOLD approval gate below.
- `--autonomous --bold`: unlock BOLD-classified work without per-instance user questions; convergence remains mandatory.
- `coder`: prose-triggered only. Default `coder=claude`. Set `coder=codex` only when the prose contains, case-insensitively, one of: "codex codes", "codex writes", "codex is the coder", "codex as coder", "let codex code", "codex writer".
- `fast`: prose-triggered only. Default off. Set when the prose contains, case-insensitively, one of: "fast", "fast mode", "fast tier", "speed mode", "service tier fast", "1.5x". When set, every Codex dispatch adds `-c 'service_tier="fast"'` to its flags. No behavioral change to phases, convergence, or commits - only Codex turnaround speed (1.5x at higher credit cost). Record service tier in `Result.md` header.

There are no other flags. Do not invent or accept `--coder`, `--fast`, `--no-commit`, `--max-cycles`, or any additional mode switch.

Resolve scope:
- `.` means whole repository.
- A category name scopes Review to one or more categories from `references/categories.md`.
- A path scopes Review and Refactor to that path and its necessary callers, callees, tests, manifests, and project policy files.

Infer a mission slug from the scope: 2-5 PascalCase words, ASCII letters/digits only. Examples: `WholeRepo`, `DeadCode`, `AuthPolicy`, `SrcApi`. If the user names an existing `Duo/ProdReady-<slug>/` folder, reuse it.

Preflight banner:
- On the first invocation for a project, print exactly: `This skill WRITES CODE. Modifies working tree. Runs build+test. Commits per cycle.`
- A resumed invocation of an existing mission skips the banner.

Working tree guard:
- Before starting a new mission, run `git status --porcelain=v1`.
- Refuse to start if the working tree is dirty and the dirtiness cannot be attributed to a prior cycle of the same mission.
- Attribution requires the mission journal to identify a mid-cycle base SHA, applied item ids, patch hashes, and files, and the dirty files must be a subset of journal-attributed files.
- On re-entry, read `.codex/journal.jsonl` tail. If the last event is not `cycle_committed` or `aborted`, detect mid-cycle state and offer continue or rollback in default mode. In autonomous mode, converge with the peer on continue or rollback and log the decision.

Create or reuse the mission folder before any Codex dispatch. Initialize `.codex/journal.jsonl` and append a `phase_start` record before writing each phase artifact. Every disk write must have a preceding journal record, except the initial creation of the journal file itself.

## Roles

This skill has asymmetric roles by design in Phase 3 (Refactor). Review, Plan, and Verify remain symmetric peer convergence.

The `coder` flag (default `claude`, detected from prose) determines which side authors diffs and applies them to disk:

- **Coder** (Claude by default, or Codex if prose triggers): owns all disk writes in Phase 3. Authors every diff. Applies approved patches via `git apply`. Records `item_applied` events in the mission journal. Runs build, test, and per-category verifiers in Phase 4. Writes attributed-file commits.
- **Reviewer** (the other side): never writes to the working tree. In Phase 3, reads the coder's proposed diffs and votes `APPROVE`, `REQUEST_EDITS`, `SKIP`, or `USER-TIER` in its own position file. In Phases 1, 2, and 4, acts as a symmetric peer and writes its own position files reasoning about findings, classifications, and verification status.

Why Phase 3 is asymmetric: code on disk is an atomic artifact. Two writers cannot merge a diff the way two findings can be merged. Single-writer-with-reviewer is the model that lets convergence semantics apply to mutations without merge conflicts.

Position file naming flips with `coder`:
- `coder=claude` (default): `Claude-CN-refactor-<item>-rNN.diff` for intermediate diffs and `Codex-CN-refactor-<item>-rNN.md` for intermediate votes. Canonical files are `Claude-CN-refactor-<item>.diff` and `Codex-CN-refactor-<item>.md`.
- `coder=codex`: `Codex-CN-refactor-<item>-rNN.diff` for intermediate diffs and `Claude-CN-refactor-<item>-rNN.md` for intermediate votes. Canonical files are `Codex-CN-refactor-<item>.diff` and `Claude-CN-refactor-<item>.md`.

## Mission Folder Layout

```text
Duo/ProdReady-<slug>/
  Claude-CN-review-rNN.md
  Codex-CN-review-rNN.md
  Claude-CN-review.md
  Codex-CN-review.md
  Claude-CN-plan-rNN.md
  Codex-CN-plan-rNN.md
  Claude-CN-plan.md
  Codex-CN-plan.md
  <Coder>-CN-refactor-<item>-rNN.diff
  <Reviewer>-CN-refactor-<item>-rNN.md
  <Coder>-CN-refactor-<item>.diff
  <Reviewer>-CN-refactor-<item>.md
  Claude-CN-verify-rNN.md
  Codex-CN-verify-rNN.md
  Claude-CN-verify.md
  Codex-CN-verify.md
  cycle-CN-build.log
  Result.md
  .codex/
    session
    session-history
    journal.jsonl
    rCN-<phase>-rNN-prompt.txt
    rCN-<phase>-rNN-stream.jsonl
    rCN-<phase>-rNN-final.txt
    rCN-<phase>-rNN-stderr.log
```

`CN` is the macro cycle number. `rNN` is the intra-phase mutual revision round, reset to `r01` at the start of each phase. Intermediate position files include `-rNN`. After convergence, copy or summarize the final intermediate files into canonical files without the `-rNN` suffix.

Position files and `cycle-CN-build.log` are root-visible mission artifacts. All other scratch, prompts, streams, session ids, stderr, temporary files, and state stay in `.codex/`.

`Result.md` is cumulative and append-only. It has exactly one completion signature, written only at the end.

Use this `Result.md` schema:

```markdown
# Prod Ready Result - <slug>

**Scope:** <scope>
**Mode:** default | autonomous | bold | autonomous+bold
**Coder:** claude | codex
**Status:** IN_PROGRESS | COMPLETE | BLOCKED | ABORTED
**Warning:** WARNING: No verification ran during any cycle. Codebase may not build/test. [only if every cycle is VERIFIED_NONE]

## Summary
- Cycles completed:
- Commits created:
- Current verification status:
- Remaining actionable findings:

## Build/Test Discovery
- CLAUDE.md policy:
- Manifest commands:
- Active discovery:
- Selected build command:
- Selected test command:
- Additional verifiers:

## Full Backlog
| Item | Category | Severity | Status | Evidence | Files | Notes |
|---|---|---|---|---|---|---|

## Cycle CN
### Review
- Position files:
- Findings added:
- Findings resolved:
- Full-backlog completion check:
- Zero-net-progress attestation:

### Plan
- Workset:
- Labels:
- File attribution:
- Per-category verification requirements:
- BOLD approvals or deferrals:

### Refactor
- Applied items:
- Skipped items:
- Patch hashes:
- Files touched:

### Verify
- Build:
- Tests:
- Per-category verifiers:
- Status: VERIFIED_GREEN | VERIFIED_NONE | RED
- Evidence:

### Commit
- Commit:
- Attributed files staged:
- Non-attributed dirty files:

## Intentional Keeps
| Item | Category | Evidence | Rationale |
|---|---|---|---|

## Deferred Work For Future Runs
### OUT_OF_SCOPE_NEEDS_BOLD
| Item | Category | Public surface | Evidence |
|---|---|---|---|

### OUT_OF_SCOPE_NEEDS_EVIDENCE
| Item | Category | Evidence needed | Current evidence |
|---|---|---|---|

## Unresolved
- USER-TIER blockers or autonomous escalation outcomes.

## Completion Signature
- Claude: COMPLETE - zero actionable findings remain in the full backlog.
- Codex: COMPLETE - zero actionable findings remain in the full backlog.
- Cycle verification statuses:
- Deferred enumeration:
- Completion commit:
```

## Discovery Toolbox

Build/test command discovery priority:
1. `CLAUDE.md` explicit instructions and standing project policy, including the user's `feedback_no_fallback.md` policy.
2. Project manifest scripts: `package.json`, `Cargo.toml`, `CMakeLists.txt`, `*.sln`, `pyproject.toml`, `build.gradle`, and equivalent ecosystem manifests.
3. Active discovery scan: `.tests/`, `test_*.py`, `*_test.go`, `*Test.cs`, `*.spec.*`, `.github/workflows`, `.gitlab-ci.yml`, `azure-pipelines.yml`, custom `.ps1`, `Makefile`, type checkers, linters, smoke imports, and repository-specific scripts.

Rubric:
- Load detailed category definitions from `references/categories.md`.
- If `references/categories.md` is unavailable, use `Duo/Research-AiCodeProdProblems/Result.md` as the source of truth.
- Read the 26-category rubric selectively. Load only categories relevant to the current scope and findings.

The 26 category names are:
1. Hallucinated APIs and nonexistent symbols
2. Hallucinated packages / dependency-confusion / slopsquatting
3. Injection vulnerabilities
4. Secrets and credentials in code
5. Broken authentication and authorization
6. Insecure deserialization and dynamic evaluation
7. Over-broad exception handling that swallows real errors
8. Unjustified fallback branches that mask bugs
9. Fabricated, tautological, or mock-only tests
10. Dead-code accumulation
11. Near-duplicate functions / Conditional Monsters
12. Backward-compatibility shims that should not exist
13. Premature or wrong abstractions
14. Defensive validation at internal boundaries
15. Missing error handling at REAL boundaries
16. Tight coupling and poor file cohesion
17. Leaky abstractions
18. Configuration sprawl
19. Observability gaps
20. Race conditions in concurrent code
21. Resource leaks
22. Performance regressions hidden in O(n^2) / N+1 patterns
23. Type-system escape-hatch abuse
24. WHAT-comments and comment rot
25. Unreproducible / environment-specific builds
26. Boilerplate cognitive debt + AI-induced merge churn

Always-on detection:
- Always detect no-fallback, no-shim, and no-duplication findings at category level.
- Always classify public-surface instances as BOLD during Plan.
- Backward compatibility is justified only at public API boundaries with external consumers and must be proven by evidence.

Use normal codebase tools first: `rg`, `rg --files`, language-native unused-symbol tools, type checkers, test runners, dependency validators, secret scanners, clone detectors, and git history. Use web only for current library semantics, CVEs, public package verification, or external API contracts.

## Phase 1 - Review

Start every macro cycle with Review. This phase is symmetric duo convergence.

Before writing Review artifacts, append a `phase_start` journal event:

```json
{"ts":"<ISO>","cycle":N,"phase":"review","event":"phase_start","base_sha":"<sha>","item_id":null,"patch_sha":null,"files":[]}
```

Both sides independently scan the resolved scope against the 26-category rubric. The scan is comprehensive for the full backlog, not limited to the cycle workset. Include current code, tests, manifests, CI, project policy files, and necessary callers/callees.

During mutual revision, Claude writes `Claude-CN-review-rNN.md` and Codex writes `Codex-CN-review-rNN.md`. After the first AGREED pair, copy or summarize the final intermediates to `Claude-CN-review.md` and `Codex-CN-review.md`.

Review position format:

```markdown
# ProdReady - Cycle CN Review rNN (Claude|Codex)

## Investigation
- <path>:<line> or <command/source> - evidence gathered

## Findings
| Item | Category | Severity | Evidence | Impact | Confidence | Public surface | Suggested action |
|---|---|---|---|---|---|---|---|

## Dropped
- Style/naming nits silently dropped. Include only if needed to explain why an apparent issue is not actionable.

## Full Backlog Check
- Actionable findings remaining:
- INTENTIONAL_KEEP count:
- OUT_OF_SCOPE_NEEDS_BOLD count:
- OUT_OF_SCOPE_NEEDS_EVIDENCE count:

## Zero-Net-Progress Attestation
- Progress since prior cycle: YES | NO
- Evidence:

## Completion Position
COMPLETE | NOT_COMPLETE

## Open Questions
- [USER-TIER only; none in --autonomous mode]
```

Reconcile findings by convergence:
- Findings need category, severity, and evidence agreement before they enter the full backlog.
- Style and naming nits never block convergence and never appear as actionable findings.
- Duplicate findings are merged under one item id.
- A finding may be removed only when both sides agree it is fixed, intentionally kept, out of scope by mode, or unsupported by evidence.

Completion check:
- Both sides must declare zero actionable findings remain in the full backlog, not just in the current cycle workset.
- `INTENTIONAL_KEEP` satisfies completion.
- `OUT_OF_SCOPE_NEEDS_BOLD` and `OUT_OF_SCOPE_NEEDS_EVIDENCE` do not satisfy completion unless the run is ending as BLOCKED/ABORTED with those items enumerated.

## Phase 2 - Plan

Plan is symmetric duo convergence on every finding's action label and on the bounded workset for this cycle.

Before writing Plan artifacts, append a `phase_start` journal event for `plan`.

During mutual revision, Claude writes `Claude-CN-plan-rNN.md` and Codex writes `Codex-CN-plan-rNN.md`. After the first AGREED pair, copy or summarize the final intermediates to `Claude-CN-plan.md` and `Codex-CN-plan.md`.

Use exactly these per-finding labels:
- `APPLY`: mechanical, no public-surface impact; auto-apply.
- `BOLD`: touches public API, exported symbol, module structure, feature behavior, deletion of a public path, or other public surface. Refactor only if `--bold` is set.
- `INTENTIONAL_KEEP`: both sides agree this is by-design forever; satisfies "no actionable findings remain."
- `OUT_OF_SCOPE_NEEDS_BOLD`: would fix, but `--bold` is not set; counts toward backlog and does not satisfy completion.
- `OUT_OF_SCOPE_NEEDS_EVIDENCE`: cannot be responsibly classified from static review; record a named evidence requirement; counts toward backlog and does not satisfy completion.
- `USER-TIER`: the peers cannot agree. Default mode asks the user to break the tie. Autonomous mode logs unresolved outcome and resolves only through convergence plus escalation handshake.

Plan position format:

```markdown
# ProdReady - Cycle CN Plan rNN (Claude|Codex)

## Backlog Classification
| Item | Label | Rationale | Public surface | Evidence needed | Required verifier |
|---|---|---|---|---|---|

## Cycle Workset
| Item | Order | Blast radius | Files attributed | Hunks attributed | Required verifier |
|---|---|---|---|---|---|

## BOLD Gate
- BOLD items approved this cycle:
- BOLD items deferred as OUT_OF_SCOPE_NEEDS_BOLD:
- User approvals needed:

## Staging Attribution
- Files allowed for staging this cycle:

## Open Questions
- [USER-TIER only; none in --autonomous mode]
```

Workset bounding:
- Converge on a bounded workset for this cycle before any refactor.
- Bound by count, category cluster, blast radius, or dependency order.
- Choose smallest blast radius first.
- The full backlog persists across cycles in `Result.md`.

File attribution:
- Every approved workset item must list expected files and hunks.
- The commit stage may stage only attributed files.
- If later implementation needs a new file, return to Plan convergence before editing.

BOLD handling:
- Without `--bold`, all BOLD items become `OUT_OF_SCOPE_NEEDS_BOLD`.
- With `--bold` and not `--autonomous`, ask the user for per-instance approval for each BOLD item in the cycle workset.
- With `--autonomous --bold`, proceed only after both sides converge that each BOLD item is appropriate.
- User deferrals persist as `OUT_OF_SCOPE_NEEDS_BOLD`.

Verification planning:
- For every `APPLY` or approved `BOLD` item, record the required verifier.
- Build and test are always required when discoverable.
- Add per-category verifiers such as secret scan, dependency validation, taint or injection checks, authz negative tests, clone detection, type escape counts, clean checkout checks, benchmarks, or resource/concurrency stress tests.

## Phase 3 - Refactor

Refactor is asymmetric. It is the only non-symmetric phase.

For each approved workset item, sequentially, smallest blast radius first:
1. Before any artifact or worktree write, append the appropriate journal record.
2. `<Coder>` writes a patch file `<Coder>-CN-refactor-<item>-rNN.diff`.
3. `<Coder>` does not apply the patch to disk until the reviewer approves it.
4. `<Reviewer>` reads the diff and writes `<Reviewer>-CN-refactor-<item>-rNN.md` with one vote: `APPROVE`, `REQUEST_EDITS`, `SKIP`, or `USER-TIER`.
5. Iterate until convergence. There is no numeric iteration cap.
6. After convergence, copy the final intermediate diff to `<Coder>-CN-refactor-<item>.diff` and the final reviewer vote to `<Reviewer>-CN-refactor-<item>.md`.

Coder diff requirements:
- Patch must touch only files attributed in Plan.
- Patch must be minimal for the item.
- Patch must not include unrelated cleanup.
- Patch must remove fallback/shim/duplication only when the specific instance is approved by Plan classification.

Reviewer vote format:

```markdown
# ProdReady - Cycle CN Refactor <item> rNN (<Reviewer>)

## Vote
APPROVE | REQUEST_EDITS | SKIP | USER-TIER

## Review
- Correctness:
- Scope:
- Public surface:
- Verification impact:

## Required Edits
- [only for REQUEST_EDITS]

## Open Questions
- [USER-TIER only; none in --autonomous mode]
```

Convergence outcomes:
- `APPROVE`: record `item_applied` in `.codex/journal.jsonl` before applying the patch. Include base SHA, item id, patch SHA, and files. Then `<Coder>` applies to disk.
- `REQUEST_EDITS`: `<Coder>` writes a revised diff and repeats the micro-cycle.
- `SKIP`: log skip reason in `Result.md`; do not edit disk for the item.
- `USER-TIER`: default mode blocks for user decision. Autonomous mode log-skips only after both sides converge that no responsible non-user resolution exists.

Patch hash:
- Compute the hash from the exact diff content before applying.
- Record it as `patch_sha` in the journal.

## Phase 4 - Verify

Verify is symmetric convergence over command discovery, command results, failures, and commit eligibility. Command execution is owned by `<Coder>` because `<Coder>` applied the patch.

Before verification starts, append:

```json
{"ts":"<ISO>","cycle":N,"phase":"verify","event":"verify_start","base_sha":"<sha>","item_id":null,"patch_sha":null,"files":["<attributed files>"]}
```

`<Coder>` runs:
- Discovered build command.
- Discovered test command.
- Union of all per-category verifiers declared in Plan.

Command output:
- Save build/test/verifier output to `cycle-CN-build.log`.
- During mutual revision, Claude writes `Claude-CN-verify-rNN.md` and Codex writes `Codex-CN-verify-rNN.md`.
- After the first AGREED pair, copy or summarize final intermediates to `Claude-CN-verify.md` and `Codex-CN-verify.md`.

Verify position format:

```markdown
# ProdReady - Cycle CN Verify rNN (Claude|Codex)

## Commands
| Command | Purpose | Result |
|---|---|---|

## Evidence
- cycle-CN-build.log:
- Additional verifier outputs:

## Status
VERIFIED_GREEN | VERIFIED_NONE | RED

## Failures
- [for RED only]

## Commit Eligibility
- Attributed files dirty:
- Non-attributed files dirty:
- Ready to commit: YES | NO

## Open Questions
- [USER-TIER only; none in --autonomous mode]
```

GREEN:
- Stage only attributed files.
- Refuse commit if non-attributed files are dirty.
- `<Coder>` creates one commit per cycle:

```text
duo-prod-ready cycle N: <categories>
```

- Append `cycle_committed` journal event after commit with commit SHA and staged files.
- Continue to the next Review cycle.

RED:
- Treat verification failures as reviewer objections.
- Re-enter Refactor for the responsible item(s).
- If red persists and both sides converge that the current cycle cannot be repaired responsibly, append `cycle_reverted` before reverting, then restore from the journal base SHA.
- Revert uses the base SHA recorded for the cycle. Do not use unrecorded destructive commands.

NO TEST/BUILD FOUND:
- Enter active discovery before any waiver.
- Search `.tests/`, test file patterns, CI configs, type checkers, linters, smoke imports, custom scripts, `Makefile`, manifests, and project docs.
- Only after exhaustive discovery may both sides attest: `no verification path exists in this codebase`.
- Log status as `VERIFIED_NONE`, not `VERIFIED_GREEN`.
- `Result.md` and the completion signature must list every `VERIFIED_NONE` cycle.
- If every cycle is `VERIFIED_NONE`, add the warning banner in `Result.md`.

## Macro Cycle Loop

Run:

```text
REVIEW -> PLAN -> REFACTOR -> VERIFY -> REVIEW
```

No numeric iteration caps exist anywhere. Convergence and signal-based escalation are the only termination paths.

Cycle orchestration:
1. Review the full backlog against the rubric.
2. Plan labels and a bounded workset.
3. Refactor approved workset items through `<Coder>` diff and `<Reviewer>` vote.
4. Verify build, tests, and per-category verifiers.
5. Commit one green cycle.
6. Review again.

Exit only on co-signed completion signature:
- Claude declares COMPLETE.
- Codex declares COMPLETE.
- Both attest zero actionable findings remain in the full backlog.
- All `INTENTIONAL_KEEP`, `OUT_OF_SCOPE_NEEDS_BOLD`, `OUT_OF_SCOPE_NEEDS_EVIDENCE`, `USER-TIER`, and verification statuses are enumerated.

Zero-net-progress:
- At the end of each Review phase, compare the actionable full backlog to the prior Review.
- If the same actionable findings remain with no net reduction, both sides must enter an escalation handshake before the next Plan.
- Default mode may surface USER-TIER.
- Autonomous mode cannot block on the user; it must converge on continue, re-scope, log unresolved, or abort.

Aborted missions:
- Append an `aborted` journal event.
- `Result.md` status becomes `ABORTED` or `BLOCKED`.
- Enumerate unresolved findings and verification status.

## Signaling - DO NOT POLL

Launch Codex via Bash with `run_in_background: true`. Harness notifies on background completion.

Claude MUST NOT poll stream files, repeatedly check for `Codex-CN-<phase>-rNN.md`, run mtime loops, or spawn watchers. Launch Codex, work in parallel on Claude's own phase artifact, STOP when Claude's side is complete. On bg-completion notification, validate the expected Codex output path and proceed.

Bash-internal `monitor_once()` is allowed.

## Prompt File Authorship

Skill body writes `$MISSION/.codex/r${CN}-${PHASE}-r${NN}-prompt.txt` before dispatch. For refactor item rounds, include the item id in the prompt path: `$MISSION/.codex/r${CN}-refactor-${ITEM}-r${NN}-prompt.txt`.

Per-phase prompts:
- Review prompt includes scope, mode, coder, rubric reference, prior full backlog, prior `Result.md`, and output target.
- Plan prompt includes converged Review artifacts, label definitions, BOLD/autonomous mode, file-attribution requirement, and verifier requirement.
- Refactor prompt includes the single item, approved files/hunks, coder/reviewer assignment, coder diff path, reviewer vote path, and public-surface constraints.
- Verify prompt includes workset, applied patch hashes, expected attributed files, build/test discovery, verifier list, coder ownership, and commit eligibility rules.

Prompts must name the output file exactly. Prompts must remind the peer that no iteration caps exist and convergence is the first AGREED pair.

## Codex Dispatch

Set `CWD`, `MISSION`, `KIND=ProdReady`, `CYCLE`, `ROUND`, `PHASE=review|plan|refactor|verify`, `CODER=claude|codex`, and optional `ITEM` before invoking. Run via Bash with `run_in_background: true`.

```bash
set -u -o pipefail

CWD="${CWD:?absolute cwd}"
MISSION="${MISSION:?mission folder}"
KIND="${KIND:?ProdReady}"
CYCLE="${CYCLE:?macro cycle number}"
ROUND="${ROUND:?intra-phase round counter}"
PHASE="${PHASE:?review|plan|refactor|verify}"
CODER="${CODER:-claude}"
ITEM="${ITEM:-}"
CN="$(printf "%02d" "$CYCLE")"
NN="$(printf "%02d" "$ROUND")"

mkdir -p "$MISSION/.codex"

if [[ "$PHASE" == "refactor" && -n "$ITEM" ]]; then
  PROMPT_FILE="$MISSION/.codex/r${CN}-refactor-${ITEM}-r${NN}-prompt.txt"
  STREAM="$MISSION/.codex/r${CN}-refactor-${ITEM}-r${NN}-stream.jsonl"
  FINAL_CAPTURE="$MISSION/.codex/r${CN}-refactor-${ITEM}-r${NN}-final.txt"
  STDERR_LOG="$MISSION/.codex/r${CN}-refactor-${ITEM}-r${NN}-stderr.log"
  if [[ "$CODER" == "codex" ]]; then
    CODEX_OUT="$MISSION/Codex-${CN}-refactor-${ITEM}-r${NN}.diff"
  else
    CODEX_OUT="$MISSION/Codex-${CN}-refactor-${ITEM}-r${NN}.md"
  fi
else
  CODEX_OUT="$MISSION/Codex-${CN}-${PHASE}-r${NN}.md"
  PROMPT_FILE="$MISSION/.codex/r${CN}-${PHASE}-r${NN}-prompt.txt"
  STREAM="$MISSION/.codex/r${CN}-${PHASE}-r${NN}-stream.jsonl"
  FINAL_CAPTURE="$MISSION/.codex/r${CN}-${PHASE}-r${NN}-final.txt"
  STDERR_LOG="$MISSION/.codex/r${CN}-${PHASE}-r${NN}-stderr.log"
fi

SESSION_FILE="$MISSION/.codex/session"
HISTORY_FILE="$MISSION/.codex/session-history"
LAUNCH_EPOCH="$(date +%s)"

if [[ ! -s "$PROMPT_FILE" ]]; then
  cat > "$CODEX_OUT" <<EOF
# $KIND - Cycle $CN $PHASE r$NN (Codex unavailable)

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

# Mode: fast service tier (1.5x speed at higher credit cost; no behavioral change).
# FAST is exported by the skill body when the `fast` flag is detected in user prose.
if [[ "${FAST:-0}" == "1" ]]; then
  CODEX_FLAGS+=(-c 'service_tier="fast"')
fi

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
  FALLBACK_PROMPT="$PROMPT_FILE.fallback"
  {
    cat "$PROMPT_FILE"
    printf '\n\n# Resume failed; prior position files pasted for continuity.\n'
    for f in "$MISSION"/Claude-*.md "$MISSION"/Codex-*.md "$MISSION"/Claude-*.diff "$MISSION"/Codex-*.diff; do
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
# $KIND - Cycle $CN $PHASE r$NN (Codex unavailable)

## Investigation
- Codex dispatch did not produce a valid position file. See $STREAM, $FINAL_CAPTURE, $STDERR_LOG.

## Draft
Codex unavailable for this phase. The local side continues with its own findings + validated prior Codex positions.

## Open Questions
- Dispatch failure is not a substantive disagreement.

## Dispatch Metadata
- Mode: $MODE
- Status: ${RUN_STATUS:-unknown}
- Stalled: ${RUN_STALLED:-unknown}
EOF
fi
```

## Convergence

Convergence is the first AGREED pair. No confirmation round.

For Review, Plan, and Verify:
- Both sides must agree on the same substantive state for the phase.
- If either side declares disagreements remain, continue the phase with another `rNN` prompt and position update.
- Do not advance phases on partial agreement.
- After convergence, copy or summarize the final intermediate pair to canonical files without the `-rNN` suffix.

For Refactor:
- Convergence for an item is `APPROVE`, `SKIP`, or a resolved `USER-TIER` outcome.
- `REQUEST_EDITS` continues the item micro-cycle with the next `rNN`.
- After convergence, copy the applied diff and final vote to canonical files without the `-rNN` suffix.

For mission completion:
- Both sides must declare completion in Review.
- The completion signature is written once at the end of `Result.md`.
- There is no extra confirmation round after the first agreed completion pair.

## Self-Review

Before each Codex round, verify:
1. Frontmatter sanity if editing or installing this skill: `name: duo-prod-ready`, description includes explicit trigger discipline, and description states that the skill writes code, modifies the working tree, runs build+test, and commits per cycle.
2. Required sections exist: When Invoked, Roles, Mission Folder Layout, Discovery Toolbox, Phase 1 - Review, Phase 2 - Plan, Phase 3 - Refactor, Phase 4 - Verify, Macro Cycle Loop, Signaling - DO NOT POLL, Prompt File Authorship, Codex Dispatch, Convergence, Self-Review, User Feedback, Hard Rules, File Reading Limits.
3. Prompt file exists and names the exact output path.
4. Mission journal has the required pre-write event.
5. Dispatch block is inlined and uses direct Codex CLI only.
6. Codex flags are pinned and ordered before `resume "$SESSION_ID" -`.
7. `CYCLE` and `ROUND` are both set, and `ROUND` is the intra-phase revision counter.
8. `CODER` is either `claude` or `codex`, with no other writer role.
9. Root-visible mission files are only position files, `cycle-CN-build.log`, and `Result.md`.
10. Scratch files stay in `.codex/`.
11. No numeric iteration caps were introduced.
12. If the skill is installed, `references/categories.md` exists or the skill points directly to the foundation research catalog.

## User Feedback

Default mode:
- Ask the user only for USER-TIER blockers and BOLD approvals when `--bold` is set.
- Present concise options with the consequences of each choice.
- Do not ask the user to resolve ordinary peer disagreements.

Non-autonomous `--bold` mode:
- Gate each BOLD item per cycle before Refactor.
- If the user declines or defers, persist the item as `OUT_OF_SCOPE_NEEDS_BOLD`.

Autonomous mode:
- No user-tier blocks.
- Resolve through convergence and escalation handshakes.
- Log unresolved outcomes in `Result.md`.

At the end:
- Present `Result.md`, commits created, verification status, coder role used, and any deferred work.
- If any cycle is `VERIFIED_NONE`, call out the verification gap.

## Hard Rules

- Direct Codex CLI only - no `/codex:rescue`, no plugin internals.
- Every Codex invocation uses `gpt-5.5`, `model_reasoning_effort="xhigh"`, `web_search="live"`, `--json`, `--output-last-message`, `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, and `-C "$CWD"`.
- Flag ordering: all flags BEFORE `resume "$SESSION_ID" -`.
- Resume preferred: only first Codex dispatch of a new mission is fresh.
- Never lower `model_reasoning_effort` below medium. Pin xhigh.
- Convergence is the first AGREED pair. No confirmation round.
- Trigger only on explicit `duo` keyword plus `prod-ready` or `duo-prod-ready`.
- Skill WRITES CODE: preflight banner mandatory on first invocation per project.
- Supported flags are exactly `--autonomous`, `--bold`, prose-triggered `coder`, and prose-triggered `fast`. No other flags.
- Coder defaults to Claude. Codex is coder only when the allowed prose trigger is present.
- The coder flag changes only Refactor write ownership and Verify/commit execution ownership; Review, Plan, and Verify convergence remain peer-symmetric.
- The fast flag has no behavioral effect on phases, convergence, or commits. It only adds `-c 'service_tier="fast"'` to every Codex dispatch (Codex `fast_mode` / `service_tier="fast"` per OpenAI Codex CLI docs). Record service tier in `Result.md` header.
- No user-tier in `--autonomous` mode; all escalation via convergence and signal-based handshakes.
- Zero-net-progress detection at end of each Review phase: both sides must attest progress or escalate.
- Mission journal mandatory: every disk write recorded BEFORE the write.
- Attributed-file staging only: commit refuses if non-attributed files are dirty.
- Always-on no-fallback, no-shim, and no-duplication detection at category level; per-instance BOLD escalation protects public surface.
- Apply standing project policy from user's `CLAUDE.md` memory `feedback_no_fallback.md`.
- Active verification discovery mandatory before any `VERIFIED_NONE` waiver.
- No iteration caps anywhere; convergence and signal-based escalation are the only termination paths.
- Claude never polls - waits for harness bg-completion notification.
- Root contains only position files plus `Result.md`; all scratch stays in `.codex/`.

## File Reading Limits

- Max 5 parallel Reads.
- Range-read files over 300 lines.
- Read the 26-category rubric selectively, only categories relevant to findings.
- Prefer `rg` and `rg --files` for discovery before opening large files.
- Read full files only when needed to validate a finding, plan a patch, or verify public-surface impact.
