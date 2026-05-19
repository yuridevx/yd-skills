---
name: solo-testplan
description: Claude-only counterpart to `duo-testplan` — same e2e test plan tree (`Solo/TestPlan-<slug>/Result.md` plus `test-plan/.../flows/<flow-id>.md`) authored by Claude alone, no codex peer. Five named phases: service-scope, local-flows, cross-app-survey (in-session mechanical reconciliation), cross-app-flows, result. Per-unit lifecycle is a chain of fresh-context subagent dispatches — one Author round plus N Refinement rounds, each reading every prior `Author-r*.md` and `Refine-r*.md` in the unit subfolder. Refinement is substance-only (missing/wrong/gap/citation-error/checklist-violation); editorial edits forbidden. Default round cap R0+1; `extended-refinement` removes the cap. Consumes the `linked-testplan` rulebook as-is. `check-refs.py` runs only at `result`. TRIGGERS ONLY on explicit "solo" keyword — `solo testplan X`, `solo-testplan X`, `/solo-testplan X`, `solo build a test plan for X`. Does NOT auto-activate on plain `test plan X`, `e2e plan`, or `generate tests for X`.
---

# Solo Testplan

Run a 5-phase, per-unit Claude-only pipeline that writes an e2e test plan tree. Each unit decomposes into a chain of independent fresh-context subagent dispatches: one Author round followed by Refinement rounds. Refinement is substance-only — editorial edits are forbidden. Refinement terminates at first round with zero substantial diffs (CLEAN) or at the round cap (CAPPED with inline `[unresolved:]` tags).

The companion `linked-testplan` rulebook is consumed AS IS. It owns the page shape, coverage vocabulary, scenario policy, mocks policy, cross-app rules, and 21-rule checklist. Do not modify it from this skill.

## When Invoked

Parse the user's prose as the only argument source. No CLI flags.

### Trigger

Trigger only on explicit `solo` phrasing:

- `solo testplan X`
- `solo-testplan X`
- `/solo-testplan X`
- `solo build a test plan for X`

Do not activate on plain `test plan X`, `e2e plan`, `generate tests for X`, or `write tests for X`.

### Mode

Detect autonomous mode when prose contains a clear execution phrase: `autonomously`, `no questions`, `hands-free`, `auto`, or `unattended`. Distinguish execution mode from topic adjectives. In autonomous mode, never call `AskUserQuestion`; USER-TIER blockers and residual gaps resolve to `[unresolved:]` tags or peer-attested `CAPPED` / `BLOCKED` outcomes logged in `Result.md`.

Default mode is allowed. Ask at most one clarifying question if the mission goal is too ambiguous to start. Surface USER-TIER blockers only after the subagent has exhausted source investigation; present concise `(a)/(b)/(c)` options inline as text.

### Modifiers

| Modifier | Effect |
|---|---|
| `high-concurrency` | Shared cap 8 → 16 across `service-scope` / `local-flows` / `cross-app-flows`. |
| `very-high-concurrency` | Shared cap → 32. |
| `extended-refinement` | Remove the round cap; soft warning every +2 unresolved rounds per unit. (Default cap is R0 + 1.) |
| `web-allowed` | Per-unit subagents may use WebFetch / WebSearch. |

### Filter and Slug

Support free-form repo/service filters in prose such as `only ingestion-service` or `work on X and Y`. Empty filter means all discovered repos/services.

Mint a 2-5 PascalCase slug from prose, for example `Petclinic` or `OrdersFlow`. If the user names an existing `Solo/TestPlan-<slug>/`, resume from `.solo/journal.jsonl`.

## Plugin Layout and Path Resolution

This skill ships in the `yd` plugin alongside the `linked-testplan` rulebook and root `scripts/check-refs.py` validator. The mission CWD is the user's target workspace, not the plugin install directory, so plugin-relative paths must be resolved to absolute paths before they are passed to dispatched subagents.

At activation, resolve once and reuse for the mission:

- `PLUGIN_ROOT`: two directories above this skill directory.
- `RULEBOOK_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`.
- `RULEBOOK_REFS_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/references/`.
- `CHECK_REFS_ABS`: `$PLUGIN_ROOT/scripts/check-refs.py`.

Pass these absolute paths in every dispatched prompt. Before the first subagent writes any artifact, verify `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS` exist and are readable. Halt on broken install.

## Mission Folder Layout

```
Solo/TestPlan-<slug>/
  Result.md
  test-plan/
    <repo>/<svc>/flows/<flow-id>.md
    cross-app/flows/<cflow-id>.md
  .solo/
    journal.jsonl
    unit-manifest.json
    Reconciled-crossapp.json
    service-scope/
      <repo>__<svc>/
        Author-r00.md
        Refine-r01.md
        Author-r01.md
    local-flows/
      <flow-id>/
        Author-r00.md
        Refine-r01.md
        Author-r01.md
    cross-app-flows/
      <cflow-id>/
        ... same shape ...
    result-sanity/
      Findings.md
```

Root contains only visible deliverables: `Result.md` and `test-plan/`. All scratch, per-round artifacts, and journals stay in `.solo/`.

Slash characters in repo names become `__` to keep paths flat under `service-scope/`. The `<flow-id>` and `<cflow-id>` follow `linked-testplan` Rule 11.

**Unit key format** (used as the journal `unit_key` field):

| Phase | Unit key |
|---|---|
| `service-scope` | `service-scope/<repo>__<svc>` |
| `local-flows` | `local-flows/<flow-id>` |
| `cross-app-flows` | `cross-app-flows/<cflow-id>` |
| `result-sanity` | `result-sanity` |

The unit key is the relative path of the unit's subfolder under `.solo/`, which makes the journal navigable.

## Discovery Toolbox

Source code is the only ground truth by default. Existing tests, READMEs, generated documentation, and ordinary Markdown are excluded as evidence.

Use:

1. Production source under each repo.
2. `RULEBOOK_ABS` for page shape, coverage vocabulary, scenario policy, mocks policy, cross-app policy, and the 21-rule checklist.
3. `RULEBOOK_REFS_ABS` selectively for page examples, checklist rationale, and flow-id edge cases.
4. `.solo/unit-manifest.json` after `service-scope`.
5. Upstream converged artifacts from earlier phases (the max-N `Author-r<N>.md` of each terminal unit), with absolute paths passed in by main via the dispatch prompt.
6. Web only when `web-allowed` appears in the user's prose.

Apply this exclusion set to source walks:

```
Tests:    **/*.{spec,test,e2e}.*, **/test/**, **/tests/**, **/__tests__/**, **/spec/**, **/e2e/**
Build:    **/dist/**, **/build/**, **/.next/**, **/coverage/**
Vendor:   **/node_modules/**, **/local-packages/**
VCS/IDE:  **/.git/**, **/.idea/**, **/.vscode/**
Docs:     **/*.md, **/*.pdf, **/*.txt, **/CHANGELOG*, **/README*
```

## Pipeline

Five phases. Phase names are descriptive — no letter codes.

| Phase | Role | Concurrency |
|---|---|---|
| `service-scope` | One unit per `(repo, service)`. Catalog candidate roots, entrypoints with external-dep tags, flow ids. | parallel, shared cap |
| `local-flows` | One unit per local `flow-id`. Author the per-flow page per rulebook. | parallel, shared cap |
| `cross-app-survey` | **Main session, no subagent.** Reconcile producer/consumer pairs from external-dep tags. | sequential |
| `cross-app-flows` | One unit per `cflow-id`. Author the cross-app page per rulebook. | parallel, shared cap |
| `result` | Main writes `Result.md`; spawn one `result-sanity` unit; run `check-refs.py`. | sequential |

**Gates.**

The only hard barrier is `all local-flows and cross-app-flows terminal → result`. Everywhere else, streaming handoffs replace barriers:

- As soon as `service-scope/<repo>__<svc>` commits, main spawns `local-flows/<flow-id>` for that service's flows.
- `cross-app-survey` runs in the main session the moment all `service-scope` units are terminal — concurrent with `local-flows`.
- `cross-app-flows/<cflow-id>` starts as soon as the producer-side and consumer-side `local-flows` units of that cflow are both terminal.

## Main Session Scope

The main Claude session is a thin coordinator. It is the only writer to `journal.jsonl`, `unit-manifest.json`, `Reconciled-crossapp.json`, `Result.md`, and `test-plan/`. It runs mechanical Glob/Grep/Read for enumeration and reconciliation. It does NOT author or refine artifact content.

Initialize:

1. Parse trigger, mode, modifiers, filters, slug, and web policy.
2. Create `Solo/TestPlan-<slug>/.solo/` plus the phase subdirectories (`service-scope/`, `local-flows/`, `cross-app-flows/`, `result-sanity/`).
3. Create or resume `.solo/journal.jsonl`.
4. Resolve and self-test `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS`.
5. Enumerate repos via Glob on `.git/`. If no nested `.git/` directories, treat `CWD` as the single repo.
6. Enumerate services per repo via `apps/<svc>/` Glob. Fallback: top-level service directories in a monorepo, or `CWD` itself as the single service.
7. Apply user prose filters (`only X`, `work on X and Y`).
8. Append `phase_start` for `service-scope`.

Main must NOT:

- Read source code for substantive analysis (mechanical enumeration only).
- Author or refine artifacts (subagents do this).
- Run refinement loops itself.
- Spawn nested subagents from a subagent.

## Journal Events

| Event | Fields | When |
|---|---|---|
| `phase_start` | `phase`, `ts` | Before phase work starts. |
| `subagent_spawn` | `phase`, `unit_key`, `role` (`author` or `refinement`), `round`, `cap_consumed`, `expected_output_path` | Before each subagent dispatch. |
| `artifact_accepted` | `path`, `status` | After validating an output. |
| `artifact_rejected` | `path`, `reason` | After rejecting malformed or empty output. |
| `round_complete` | `unit_key`, `round`, `round_kind`, `substantial_diff_count`, `change_kinds` | After accepting a round. |
| `gate_resolved` | `phase`, `unit_key`, `state` (`CLEAN`, `CAPPED`, or `BLOCKED`) | At unit terminal state. |
| `refinement_cap_hit` | `unit_key`, `unresolved_field_count` | When round cap is reached with residual diffs. |
| `phase_complete` | `phase`, `counts` | At phase exit. |
| `mission_halted` | `reason` | On fatal failure. |

On harness restart, read the journal tail. For each unit whose last event is `subagent_spawn` without a matching `round_complete`, re-spawn the same round (idempotent — output paths are deterministic and the subagent is fresh-context).

## Per-Unit Lifecycle: Independent Subagents Per Round

Every unit's progress is externalized to files on disk inside the unit's subfolder. Each round is a fresh subagent dispatch with no inherited context. The new round subagent reads all prior round artifacts from disk.

### R0 — Author

Main spawns an Author subagent via the Agent tool. The full prompt is passed directly as the Agent tool's `prompt` parameter — no prompt files are written to disk (main and subagents both run in the same Claude harness; the Agent tool is the delivery mechanism). The prompt contains:

- Mission folder absolute path, CWD absolute path.
- `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`.
- Phase name and unit key.
- Source scope (paths to walk; exclusion set).
- Upstream converged artifacts to consume, passed as absolute paths (e.g., `local-flows` units receive the path of their owning service's converged `service-scope` `Author-r<N>.md`).
- Required field set for the phase (rulebook page shape).
- For `service-scope`: the external-dep tag taxonomy below.
- Output spec: write `Author-r00.md` and append a YAML fence reporting `round_kind: author`.

The subagent reads only the rulebook, the source under its declared scope, and any upstream committed artifact passed in. It does not read other unit subfolders. It does not write outside its own unit subfolder.

### R1..N — Refinement

Main spawns a Refinement subagent when the previous round reported `substantial_diff_count > 0` (or unconditionally for R1 if cap > 0). The prompt extends R0's prompt with:

- Paths to every prior `Author-r*.md` in the unit subfolder.
- Paths to every prior `Refine-r*.md` in the unit subfolder.
- The round number and the round cap.
- The substance-vs-editorial policy (below).

The subagent:

1. Reads the latest `Author-r<k>.md`.
2. Reads every prior `Refine-r<1..k>.md`. Items already addressed in a prior round must not be re-flagged.
3. Re-walks the source within scope.
4. Emits `Refine-r<k+1>.md` as a list of structured field diffs (substance only).
5. Applies the revisions to produce `Author-r<k+1>.md`.
6. Appends a YAML fence reporting `round_kind: refinement`, `substantial_diff_count: N`, and `change_kinds_seen: [...]`.

After the round, main writes `round_complete` plus `gate_resolved` when terminal. If `substantial_diff_count == 0`, the unit terminates `CLEAN` — the latest `Author-r<N>.md` is the converged artifact. For `local-flows` and `cross-app-flows`, main copies that file to its final `test-plan/` path. If `substantial_diff_count > 0` and the round is below cap, main spawns the next refinement. If at cap with residuals, the round is `CAPPED` — the last refinement subagent must pre-apply `[unresolved: <field-id>: <reason>]` tags inline before writing `Author-r<k+1>.md`.

Downstream consumers (main during reconciliation, cross-app-flows units reading producer/consumer pairs, `result` composition) identify a unit's converged artifact by selecting the max-N `Author-r<N>.md` in the unit subfolder. No separate `Committed.md` pointer file exists — the highest-numbered Author file is authoritative because Author-r<k+1>.md is only written when round k+1 completes successfully.

## Substance-Only Refinement Policy

Refinement subagents emit `Refine-r*.md` as a list of field diffs. Each diff has shape:

```yaml
field_id: <stable id>
change_kind: missing | wrong | gap | citation-error | checklist-violation
evidence:
  - <path>:<line>
revised_value: <the substantive replacement or addition>
reason: <terse source-grounded rationale>
```

**Allowed substantial change kinds:**

| Kind | Definition |
|---|---|
| `missing` | A required field or scenario absent that the rulebook page shape requires for this phase. |
| `wrong` | An assertion about source behavior that contradicts the source code at the cited line. |
| `gap` | An entrypoint or branch with externally observable behavior covered by no scenario. |
| `citation-error` | A `file:line` reference that does not resolve, or points to a different symbol than claimed. |
| `checklist-violation` | A failure against a numbered rule in the `linked-testplan` 21-rule checklist. |

**Forbidden editorial change kinds** (must not appear in `Refine-r*.md`):

- Rewording for clarity or tone.
- Reordering fields, scenarios, or steps when the rulebook does not require a specific order.
- Polishing prose, removing hedging, adding hedging.
- Layout, formatting, header level, list-style changes.
- Renaming a `flow-id` that already satisfies Rule 11.

A refinement round whose only revisions would be editorial must report `substantial_diff_count: 0` and write `Author-r<k+1>.md` byte-identical to `Author-r<k>.md`. Inclusion of any editorial diff in `Refine-r*.md` causes main to reject the round and respawn with a stricter substance-only prompt; second failure is treated as no-output.

## External-Dep Tag Taxonomy (service-scope)

`service-scope` units must catalog each entrypoint with a normalized tag from:

```
kafka:produce:<topic>
kafka:consume:<topic>
http:server:<VERB> <path>
http:client:<VERB> <url-template>
grpc:server:<package>.<service>.<method>
grpc:client:<package>.<service>.<method>
s3:write:<bucket>[/<prefix>]
s3:read:<bucket>[/<prefix>]
sqs:produce:<queue>
sqs:consume:<queue>
ddb:write:<table>
ddb:read:<table>
redis:write:<key-template>
redis:read:<key-template>
sql:write:<table>
sql:read:<table>
cron:<schedule-or-source-ref>
```

Tags are normalized — lowercased scheme prefix, whitespace trimmed, identifier-case preserved. Main's `cross-app-survey` step matches producers to consumers by exact tag string after normalization (the `kafka:produce:foo` ↔ `kafka:consume:foo` pair, etc.). Ambiguous matches (one producer with multiple consumers, partial path matches) are listed in `.solo/Reconciled-crossapp.json` as candidates and surfaced in `Result.md → ## Unresolved`.

## Phase-by-Phase Orchestration

### service-scope

Parallel, one unit per `(repo, service)`, sharing the global concurrency cap. Unit keys: `service-scope/<repo>__<svc>`.

Each unit identifies candidate source roots, entrypoints, external-dep tags (per the taxonomy above), and stable flow IDs. Entrypoints include HTTP controllers, Kafka producers/consumers, gRPC servers/clients, cron or scheduled jobs, S3/DDB/SQL/Redis access, and similar externally observable triggers.

Stable flow IDs derive from trigger plus entry symbol per linked-testplan Rule 11.

Field set: `candidate_roots[]`, `entrypoints[]` with file, line, trigger kind, trigger, and normalized external-dep tag, plus `flow_ids[]`.

Terminal artifact: the max-N `Author-r<N>.md` in `.solo/service-scope/<repo>__<svc>/`. After each unit's terminal `gate_resolved`, main streams `local-flows` for that service's flows (no all-services barrier).

After ALL `service-scope` units are terminal, main aggregates each unit's converged artifact into `.solo/unit-manifest.json`. Main then runs `cross-app-survey` in-session.

### local-flows

Parallel, one unit per local flow_id, sharing the global concurrency cap. Unit keys: `local-flows/<flow-id>`.

Each unit reads the flow entry `file:line`, downstream call sites, related persistence/emission code, `RULEBOOK_ABS`, relevant `RULEBOOK_REFS_ABS`, and the converged `service-scope` artifact of its owning service (the path is passed in the prompt).

Field set follows the linked-testplan page shape:

- `flow_under_test`: trigger, entry `file:line`, brief.
- `scenarios[]`: each with name, HAPPY/NEGATIVE tag, preconditions, steps, expected outcomes, mocks, and code refs.
- `code_refs[]`: flow-level supporting references.

Terminal artifact: max-N `Author-r<N>.md` in `.solo/local-flows/<flow-id>/`. Main copies that file to `test-plan/<repo>/<svc>/flows/<flow-id>.md` at terminal `gate_resolved`.

### cross-app-survey

Main-session work. No subagent.

Gate: ALL `service-scope` units terminal (not all `local-flows`). Runs concurrently with `local-flows`.

Inputs: each `service-scope` unit's converged `Author-r<N>.md` (the max-N artifact in its subfolder).

Work: pair external-dep tags across services by exact normalized tag string after the scheme prefix:

- `kafka:produce:<topic>` ↔ `kafka:consume:<topic>`
- `http:server:<VERB> <path>` ↔ `http:client:<VERB> <path-or-template>`
- `grpc:server:<m>` ↔ `grpc:client:<m>`
- `s3:write:<b>[/<p>]` ↔ `s3:read:<b>[/<p>]`
- `sqs:produce:<q>` ↔ `sqs:consume:<q>`

Ambiguous matches (one producer with multiple consumers, partial path matches, wildcarded paths) are listed in `.solo/Reconciled-crossapp.json` as candidates with `match_certainty` and `notes`. They are not silently merged.

Output: `.solo/Reconciled-crossapp.json` with `cross_app_flows[]` containing `flow_id` (prefixed `crossapp-`), `participants`, `triggering_actor`, `seam_kind`, and evidence. After this step, main streams `cross-app-flows` for each `cflow-id` as soon as its producer-side AND consumer-side `local-flows` units are both terminal.

### cross-app-flows

Parallel, one unit per cross-app flow, sharing the global concurrency cap. Unit keys: `cross-app-flows/<cflow-id>`.

Each unit reuses the producer-side and consumer-side `local-flows` converged artifacts (paths passed in the prompt) as converged facts and reads source only to validate or fill gaps.

Field set follows the linked-testplan cross-app shape. Steps prefix the actor as `<service> → <service>: <action>`. Do not include internal mutation steps across service boundaries.

Terminal artifact: max-N `Author-r<N>.md` in `.solo/cross-app-flows/<cflow-id>/`. Main copies that file to `test-plan/cross-app/flows/<cflow-id>.md` at terminal `gate_resolved`.

### result

Sequential final phase. The only hard barrier in the pipeline: all `local-flows` AND all `cross-app-flows` units terminal.

1. Main writes `Result.md` (template below).
2. Spawn one `result-sanity` unit over `Result.md` plus the final `test-plan/` tree. Read-only sanity pass — catches cross-flow contradictions (incompatible payload claims for the same topic, conflicting expected outcomes for shared dependencies, coverage gaps). Writes `.solo/result-sanity/Findings.md`. Does NOT re-author flows.
3. Main applies source-grounded corrections from `Findings.md`. Ambiguities → `## Unresolved`.
4. Main runs `$CHECK_REFS_ABS` over `test-plan/**/*.md`.
5. Main runs `$CHECK_REFS_ABS` over `Result.md` and `.solo/unit-manifest.json` for file:line refs and entrypoint coverage when supported by the validator.
6. Failures from check-refs land in `## Unresolved` rather than blocking commit.
7. Append `phase_complete` for `result`.

`Result.md` must include:

```markdown
# Test Plan Result — <slug>

## Summary
## Scope
## Flow Counts
## Coverage Matrix
## Refinement Counts
## Unresolved Items
## Exclusions
## Unresolved
```

- **Coverage Matrix.** Every entrypoint in `unit-manifest.json` maps to exactly one flow or one explicit exclusion.
- **Refinement Counts.** Rounds-per-unit average and max per phase.
- **Unresolved Items.** Inventory of every `[unresolved: <field-id>: <reason>]` tag across the tree, with unit and source links.
- **Unresolved.** Cross-flow contradictions surfaced by `result-sanity`, `check-refs.py` failures, ambiguous cross-app matches from `Reconciled-crossapp.json`.

## Terminal States

| State | Meaning | Downstream consumption |
|---|---|---|
| `CLEAN` | Last refinement round reported `substantial_diff_count: 0`. | Consumed; the unit's max-N `Author-r<N>.md` is the converged artifact. |
| `CAPPED` | Round cap hit with residual items. The unit's max-N `Author-r<N>.md` carries inline `[unresolved: <field-id>: <reason>]` tags pre-applied by the last refinement subagent. | Consumed; tags inventoried in `Result.md`. |
| `BLOCKED` | Unit cannot produce a source-grounded artifact: Author failed twice, or two consecutive refinement rounds malformed. | Not consumed. Recorded in `Result.md`. |

`CLEAN` is also the state when the Author round succeeds and cap = 0. With the default cap of `R0 + 1`, a unit that converges in one refinement pass is `CLEAN`.

## Concurrency

| Setting | Default | Override |
|---|---|---|
| Shared active per-unit subagents across `service-scope` / `local-flows` / `cross-app-flows` | 8 | `high-concurrency` → 16; `very-high-concurrency` → 32 |
| Refinement round cap per unit | R0 + 1 | `extended-refinement` removes cap (soft warning every +2 unresolved rounds) |
| Web search | disabled | `web-allowed` → enabled |

Streaming handoff is throttled by the shared cap. Main may spawn `local-flows` units for a service the moment its `service-scope` unit commits, but the shared cap still gates how many total subagents are in flight.

Per-dispatch wall-clock is not enforced by the skill — subagent dispatches go through the Agent tool and the harness owns their lifecycle. If a dispatch never returns, main relies on the user interrupting; resumability ensures restart is cheap.

## Signaling — DO NOT POLL

Every subagent dispatch runs as a single Agent-tool call. The harness notifies main on completion.

The main session must not:

- Poll output files with sleep loops.
- Repeatedly check whether output exists.
- Use mtime loops.
- Spawn watcher scripts.

Main dispatches the subagent and waits for the completion notification. On notification, main validates the output, decides commit versus next round, and dispatches the next subagent.

## Prompt Construction

For every subagent dispatch, main composes the full prompt in-memory and passes it directly as the Agent tool's `prompt` parameter. Prompts are not written to disk. Main and the subagent run in the same Claude harness, so the Agent tool's prompt parameter is the delivery mechanism — there is no separate process boundary to bridge.

Every prompt includes:

- Mission path and CWD.
- Absolute `RULEBOOK_ABS`, `RULEBOOK_REFS_ABS`, and `CHECK_REFS_ABS`.
- Phase, unit key, round number, round cap, and expected output path.
- Source scope and upstream committed artifacts for the phase.
- For refinement rounds: paths to every prior `Author-r*.md` and `Refine-r*.md` in the unit subfolder, plus the substance-vs-editorial policy (per § Substance-Only Refinement Policy).
- Exact output format: `Author-rNN.md` for R0 or `Refine-rNN.md` plus `Author-rNN.md` for refinement, plus the trailing YAML fence shape.
- Web policy: enabled (when `web-allowed`) or disabled.

Resumability does not depend on prompts being on disk. On harness restart, main reconstructs the prompt deterministically from the journal state plus the on-disk per-round artifacts in the unit subfolder. The reconstruction is mechanical — same journal state and same subfolder contents always produce the same prompt.

## Subagent Dispatch

Main uses the Agent tool with `subagent_type: general-purpose` and the full prompt as the `prompt` parameter. The dispatch carries no shell command, no file path indirection, no wrapper layer.

The prompt must include the explicit boundaries:

- Do not spawn sub-subagents.
- Do not write outside the unit's subfolder.
- Do not read other unit subfolders.
- Write the expected output file at the path declared in the prompt before returning.

## Self-Review

Before each subagent dispatch:

1. Prompt includes every section listed in § Prompt Construction.
2. Output path matches the unit subfolder naming convention.
3. Journal `subagent_spawn` record is appended.
4. For refinement rounds, every prior `Author-r*.md` and `Refine-r*.md` in the unit subfolder is enumerated in the prompt's refinement context block.

Before `result` finalization:

1. Coverage matrix complete: every entrypoint maps to flow or exclusion.
2. `$CHECK_REFS_ABS` passes on `test-plan/**/*.md`, or failures are listed in `## Unresolved`.
3. `$CHECK_REFS_ABS` coverage mode passes with `.solo/unit-manifest.json` when supported, or failures are listed.
4. No unit has terminal `BLOCKED` without a journal record explaining why.
5. All open `phase_start` events have matching `phase_complete`.
6. Root contains only `Result.md` and `test-plan/`.
7. Every `[unresolved:]` tag appears in `Result.md → ## Unresolved Items`.

Fix issues inline. Do not run any script except `check-refs.py`, and only in `result`.

## User Feedback

Default mode:

- Ask at most one clarifying question if the mission cannot start. Ask in plain text inline.
- Ask for USER-TIER blockers only after the subagent has exhausted source investigation.
- Do not ask the user to resolve ordinary `[unresolved:]` items.

Autonomous mode:

- Ask no questions.
- Resolve through `[unresolved:]` tags and peer-attested `CAPPED` / `BLOCKED` outcomes.
- Log unresolved outcomes in `Result.md`.

At the end, present `Result.md` as a clickable link and summarize repos, services, local flows, cross-app flows, terminal-state counts, refinement round counts, `check-refs.py` result, and unresolved items.

If the user later supplies substantive corrections, reopen only affected units and rerun the per-unit lifecycle.

## Failure Modes

| Failure | Behavior |
|---|---|
| Broken plugin paths | Halt before `service-scope` writes any artifact. |
| Subagent output missing or empty | Main retries the same round once. Second failure → unit `BLOCKED`. |
| Subagent output malformed YAML trailer | Treat as no-output; same retry policy. |
| Refinement subagent emits editorial-only diffs | Reject the round; spawn replacement with stricter substance-only prompt. Second failure → treat as no-output. |
| Round cap reached with residual diffs | Last refinement subagent pre-applies `[unresolved:]` tags inline before writing the final `Author-r<N>.md`. State = `CAPPED`. |
| `service-scope` unit blocked | Exclude that service from `local-flows`; record in `Result.md`. |
| `local-flows` unit blocked | Do not write that flow page; record in `Result.md`. |
| Ambiguous cross-app match | List candidates in `Reconciled-crossapp.json`; do not silently merge; surface in `Result.md → ## Unresolved`. |
| `cross-app-flows` unit blocked | Do not write that cflow page; record in `Result.md`. |
| `check-refs.py` failure at result | Fix source refs when evidence is clear; otherwise list failures in `## Unresolved`. |
| All `service-scope` units blocked | Mission halted; `Result.md` records the failure and exits. |

## Hard Rules

- No Codex. No Codex CLI invocation, no `.codex/` directory, no session-resume logic, no Codex-specific flags (`gpt-5.5`, `model_reasoning_effort`, `web_search`, `--dangerously-bypass-approvals-and-sandbox`, `--output-last-message`, `--skip-git-repo-check`, `-C $CWD`). The skill must not reference Codex.
- Trigger only on explicit `solo` keyword.
- Code is the only source of truth. Tests, READMEs, generated docs, ordinary Markdown are excluded as evidence.
- Main session is a thin coordinator. Mechanical Glob/Grep/Read for enumeration and `check-refs.py` only. No substantive source analysis. No authoring or refining.
- Each round is an independent fresh-context subagent dispatch. Refinement subagents must receive paths to every prior `Author-r*.md` and `Refine-r*.md` of the unit.
- Refinement is substance-only. The refinement prompt enumerates the forbidden editorial categories.
- Refinement stops at `substantial_diff_count: 0` (CLEAN) or round cap (CAPPED).
- No nesting: subagents never spawn sub-subagents.
- Subagents read only the files passed in their prompt, the rulebook, their own unit subfolder, and source within their declared scope. Subagents write only inside their own unit subfolder.
- Main is the only writer to `journal.jsonl`, `unit-manifest.json`, `Reconciled-crossapp.json`, `Result.md`, and `test-plan/`.
- One `.md` per flow in the final `test-plan/` tree.
- `check-refs.py` runs only at the end of `result`, never inside a refinement loop.
- Rulebook (`linked-testplan`) consumed as-is. Do not modify it from this skill.
- No polling. Main waits for harness background-completion notifications between dispatches.
- Shared concurrency cap is 8 across `service-scope` / `local-flows` / `cross-app-flows`; `high-concurrency` raises it to 16 and `very-high-concurrency` raises it to 32.

## File Reading Limits

- Glob or grep before broad reads.
- Max 5 files per parallel read batch within a subagent.
- Range-read source files over 300 lines.
- Read `linked-testplan` once per subagent invocation; load references selectively.
- Cite `file:line` for every claim in author, refinement, committed, and result artifacts.
- Do not read existing markdown, READMEs, generated docs, or tests as evidence for flow behavior.
