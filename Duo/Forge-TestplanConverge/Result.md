# Forge Result — duo-testplan-converge

## Decision

CREATE

## Gate Evaluation

- Pattern recurs across missions: **YES** — e2e test plan authoring across microservice workspaces is a recurring mission shape; the existing `duo-testplan-build` covers the same domain, and prior `Duo/Forge-TestplanBuild/` + `Duo/Design-TestPlanSkill/` artifacts demonstrate repeated engagement.
- Stable artifact shape: **YES** — `Duo/TestPlan-<slug>/Result.md` + `test-plan/<repo>/<svc>/flows/<flow-id>.md` + `test-plan/cross-app/flows/<flow-id>.md`, identical to `duo-testplan-build`'s artifact tree per [linked-testplan/SKILL.md:29-34](../../skills/linked-testplan/SKILL.md#L29-L34).
- Definable investigation procedure: **YES** — manifest extraction (P1a + P1b) → per-flow refinement (P2) → cross-app correlation (P3 + P4) → result (P5). Each phase has a single per-unit duo protocol identical across phases.
- Distinct from existing duo-*: **YES** — `duo-testplan-build` uses an 8-phase pipeline with union-merge implicit convergence and N-parallel-pass refinement (~1,950 dispatch ceiling for 5×10 mission). The new skill uses a 6-phase per-unit duo author + diff convergence pipeline (~290-580 dispatch ceiling for the same shape). Coexist; do not replace.

## Convergence Narrative

- **R1** parallel: Claude wrote `Claude-01.md` (gating CREATE, full SKILL.md draft); Codex wrote `Codex-01.md` (gating CREATE, full SKILL.md draft).
- **R1 deltas:** four minor: (1) autonomous-required vs autonomous-supported, (2) `web_search="off"` vs `"disabled"`, (3) explicit terminal states + failure modes table (Codex added, Claude lacked), (4) explicit `CODEX_OUT` env var (Codex's pattern). Verdict already converged on CREATE.
- **R2** mutual revision: Claude accepted Codex's `web_search="disabled"`, terminal states, failure modes table, explicit `CODEX_OUT` env, and per-field journal events. Held position that autonomous mode is SUPPORTED (matching duo-design convention) rather than REQUIRED. Codex accepted Claude's autonomous-supported framing and withdrew the autonomous-required gate. Codex declared `ALL_AGREED`.
- **R3** (Claude only) confirmed `ALL_AGREED` with no further changes. Convergence per yd first-AGREED-pair rule.

## Installed File

Plugin-internal path (not `~/.claude/skills/`): the skill ships as part of the `yd` plugin and is versioned with the repo so it is installable via the yd plugin marketplace.

- `s:/yd-skills/skills/duo-testplan-converge/SKILL.md` — converged SKILL.md body (corresponds to Codex-02 § Updated draft with indented code blocks restored to fenced form for direct rendering).

## Test Invocation

```
duo testplan-converge Petclinic autonomously
```

For a multi-repo workspace at the current `CWD`, this should:
1. Detect autonomous mode (`autonomously` prose modifier).
2. Mint slug `Petclinic`, create `Duo/TestPlan-Petclinic/`.
3. Resolve `PLUGIN_ROOT`, `RULEBOOK_ABS`, `CHECK_REFS_ABS` and self-test readability.
4. Spawn `P1a-scope` Claude subagent; both peers author scope file discovery in parallel and converge field-by-field within R0 + 4 diff rounds.
5. Spawn parallel `P1b-<repo>-<svc>` subagents for each discovered service.
6. Stream P2 per-flow subagents as P1b commits.
7. Run P3 cross-app discovery (1-round cap default).
8. Stream P4 per-cross-app-flow subagents.
9. Run P5 sanity duo + `check-refs.py` over the final tree.
10. Write `Result.md` and exit with link to it.

## Mission Files

- [Claude-01.md](Claude-01.md) — Claude R1 position (gating + draft)
- [Codex-01.md](Codex-01.md) — Codex R1 position (gating + draft)
- [Claude-02.md](Claude-02.md) — Claude R2 mutual revision (4 acceptances + 1 disagreement)
- [Codex-02.md](Codex-02.md) — Codex R2 (`ALL_AGREED`, withdrawals)
- [Claude-03.md](Claude-03.md) — Claude R3 (`ALL_AGREED`, formal first-AGREED-pair)
- `.codex/` — codex sessions, streams, prompts, finals (full trace)

## Unresolved

None.

## Coexistence with `duo-testplan-build`

The new skill does NOT replace `duo-testplan-build`. Both ship in the `yd` plugin and both are user-triggerable on the explicit `duo` keyword. They differ in:

| Aspect | `duo-testplan-build` | `duo-testplan-converge` |
|---|---|---|
| Phases | 8 | 6 |
| Convergence | union-merge (implicit) | step-by-step per-field diff (first-AGREED-pair) |
| Refinement | N parallel fresh passes per iteration, all-CLEAN gate | Per-unit duo author + R1..N diff, round cap 4 (extendable) |
| Codex sessions | Fresh per refinement pass (forbidden resume in refinement) | New per unit; RESUMED across rounds within a unit |
| Orchestration | Main session drives passes + tie-breaker mini-duos | Main session = thin coordinator; per-unit Claude subagent owns its cycle |
| Cap mechanism | Soft warning at iter 3, escalation at iter 5 | Hard cap at R0 + 4 diffs; `[disputed:]` tags at cap |
| Script use | Validators per phase + tie-breakers | Only `check-refs.py` at P5; no script in LLM loop |
| Rulebook | linked-testplan AS IS | linked-testplan AS IS (identical) |
| Dispatch ceiling (5×10) | ~1,950 | ~580 (typical ~270) |

Users choose based on workload character: `duo-testplan-build` for missions where deeply iterated refinement on a converged artifact matters; `duo-testplan-converge` for missions where per-unit duo agreement and tight dispatch budget matter.
