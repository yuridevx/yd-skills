---
name: linked-testplan
description: Rulebook for e2e flow-grain test plan authoring. Owns page shape, coverage vocabulary, scenario policy, mocks policy, and the 21-rule refinement checklist. Companion to the `duo-testplan-build` orchestrator, which loads this rulebook into every authoring and refinement agent. This is a PASSIVE rulebook, NOT an executor. Standalone activation only when prose explicitly references it - phrases like "apply linked-testplan rules to X", "linked-testplan checklist on X", "use linked-testplan rules". Does NOT auto-activate on plain "write tests" / "make a test plan" / "e2e plan" / "generate test cases" prose. Run the full pipeline via `duo-testplan-build`, not via this skill.
---

# Linked Testplan: Rulebook

A structured approach for authoring e2e test plans from source code in multi-repo workspaces. Defines a uniform per-flow page shape, a coverage vocabulary, a scenario policy, a mocks policy, and a 21-rule refinement checklist that authoring and refinement agents enforce.

This is the **rulebook**. The companion executor `duo-testplan-build` runs the full 8-phase pipeline. Loading this skill standalone is for inline rule application — applying these rules to an existing draft, validating a single flow page against the checklist, or referencing the page shape during manual authoring.

## Activation

Activate this skill when:

1. The `duo-testplan-build` orchestrator dispatches an authoring or refinement agent — every such agent loads `skills/linked-testplan/SKILL.md` plus relevant references.
2. The user's prose explicitly references the rulebook: `apply linked-testplan rules to X`, `check linked-testplan compliance`, `use linked-testplan checklist`, `lint with linked-testplan`.

Do NOT activate this skill on:
- Plain `write tests` / `make a test plan` / `e2e plan` / `generate test cases` / `test the flow X` / `add tests for X`.
- Any prose that does not literally reference `linked-testplan` or load this skill via orchestrator dispatch.

When activated standalone, do not run the orchestrator pipeline. Apply only the rules to whatever the user supplied (a draft page, a fragment, a checklist run).

## Core Structure

A test plan tree contains exactly two kinds of pages plus an index:

```
Result.md                                       index, coverage matrix, summary, unresolved
test-plan/
  <repo>/<svc>/flows/<flow-id>.md              per-flow plan, service-local
  cross-app/flows/<flow-id>.md                 per-flow plan, spans services
```

One file per flow. No multi-flow files. No nested sub-pages. The index lives in `Result.md`, written by the orchestrator at P8.

## Per-Flow Page Shape

Both service-local and cross-app pages share this shape:

```markdown
# <flow-id>

## Flow under test
Trigger: <event / endpoint / topic / cron>
Entry: <file>:<line>
Brief: <one terse sentence on what the flow does>

## Scenarios

### Scenario: <name> · HAPPY
- Preconditions:
  - Seeded state: <description>
  - Inbound event: <description>
  - Feature flag / config: <description>
  - External dependency state: <description>
- Steps:
  1. <action — verb-led, terse>
  2. <action>
- Expected:
  - <outcome — observable side effect, response, emitted message, persisted row, file/object write, scheduled job, or absence thereof>
- Mocks: none — pure e2e   |   <service-X stubbed because Y>
- Code refs: <file>:<line>, <file>:<line>

### Scenario: <name> · NEGATIVE
- Branch covered: <file>:<line> — <condition description>
- Preconditions:
  - <as above>
- Steps:
  1. <action>
- Expected:
  - <error outcome — status code, error payload, no side effect>
- Mocks: <...>
- Code refs: <...>
```

For cross-app pages, Steps prefix the actor: `<service> → <service>: <action>`. No internal mutations across the service boundary appear in cross-app steps — only the contract-level interactions.

See [references/page-shape.md](references/page-shape.md) for worked examples and edge cases.

## Coverage Vocabulary

| Term | Definition |
|---|---|
| **flow** | A code-traceable end-to-end execution path triggered by a single external stimulus (HTTP request, Kafka message, cron tick, S3 event, gRPC call). One owning service per flow; cross-app flows have multiple participants but exactly one triggering actor. |
| **flow-id** | Stable kebab-case identifier derived from trigger + entry symbol. Examples: `post-owners`, `consume-petclinic-owner-updated`, `cron-cleanup-stale-sessions`, `crossapp-view-owner-profile`. |
| **entrypoint** | A code location where the flow begins: HTTP handler, Kafka consumer handler, cron registration, gRPC service method. Identified by `file:line`. |
| **branch** | A code-level decision point inside a flow that produces externally observable behavior (different response, different emission, different persistence, different downstream call). Field-level validation branches that produce no externally observable difference are NOT branches for test-plan purposes. |
| **scenario** | One test case for one flow. Tagged HAPPY (success path) or NEGATIVE (branch-covered failure / rejection / partial-state path). |
| **external actor** | A producer or consumer outside the workspace (browser, mobile client, third-party API, system clock). External actors are unlinked references in cross-app flows. |
| **mock** | A stub or fake used to replace a real dependency during e2e test execution. Mocks REQUIRE a named boundary (which service / system is mocked) and a reason (why mocking is necessary). |
| **observable outcome** | A side effect visible outside the flow's owning service: HTTP response, Kafka message emission, database row persistence, file/object write, scheduled job creation, downstream service call, or the documented absence of one of these. |
| **unresolved** | A finding the refinement passes could not close mechanically within skill scope. Surfaced in `Result.md → Unresolved` and (for non-blocking unresolved on DEGRADED-CONTINUE flows) in the flow page's `## Unresolved` section. |

See [references/coverage-vocab.md](references/coverage-vocab.md) for boundary cases and disambiguation.

## Scenario Policy

- **E2E boundary only.** Every scenario exercises the flow from its triggering boundary (HTTP request, Kafka message, etc.) to its observable outcome. No scenario stays inside a single private function.
- **Major-branch coverage.** Every branch in code that produces an externally observable difference gets at least one NEGATIVE scenario. Branches that produce no observable difference (e.g. internal logging, format-only differences) do NOT require a scenario.
- **No field-level edge cases.** Validation rules (max-length, format, type) are not tested individually unless their rejection produces a flow-level different outcome. One representative NEGATIVE for "validation rejected" covers all field-level validation branches.
- **At least one HAPPY plus one NEGATIVE per major branch.** Flows with no branches get one HAPPY (and an optional NEGATIVE for the implicit "service unavailable" path if the rule below kicks in).
- **External-service-unavailable scenarios required** when the flow has a synchronous dependency on an external service. One NEGATIVE per external dependency, covering the unavailable / timeout case.

## Mocks Policy

- Default: `Mocks: none — pure e2e`. Real databases, real message brokers, real downstream services within the workspace.
- Mock ONLY when the actor is outside the workspace (third-party API, payment gateway, public cloud service) OR when the actor is nondeterministic in a way that prevents reliable assertion (system clock, random IDs, time-of-day).
- Every mock entry names the BOUNDARY and the REASON:

```
Mocks: payment-gateway stubbed (external SaaS, not part of workspace); clock fixed at 2026-01-01 (deterministic time assertions).
```

- Existing test fixtures (real test data files, helper builders from existing test suites) are NOT mocks; do NOT reference them. The page describes the precondition state in prose; the executor sets it up.

## Cross-App Flow Specifics

A cross-app flow spans two or more services in the workspace.

- One file per cross-app flow at `test-plan/cross-app/flows/<flow-id>.md`.
- `flow-id` derives from the cross-app purpose, not the triggering service alone: `crossapp-view-owner-profile`, `crossapp-checkout-order`.
- Steps prefix the actor: `api-gateway → customers-service: GET /owners/{id}`.
- No internal mutations across the service boundary. Steps stay at contract level (HTTP request/response, Kafka emit/consume, gRPC call/return, S3 write/read).
- External actors (browsers, mobile clients, third-party APIs) are unlinked references; they appear as participants but do not have their own per-flow pages.

## The 21-Rule Refinement Checklist

Every refinement pass (P3, P5, P7 in the `duo-testplan-build` pipeline) walks this checklist against the merged artifact. Each unchecked rule the pass can mechanically fix becomes a patch (`ADD-*` / `CORRECT-REF` / `STRENGTHEN` / `REMOVE-*`). Each unchecked rule the pass cannot fix becomes a Blocked entry.

### Style and structure (10)

1. **Mandatory sections.** Every scenario has Preconditions, Steps, Expected, Mocks, Code refs.
2. **Code refs validate.** Every `file:line` reference points at a real symbol on that line. Refinement passes verify via re-reading the named file at the named line.
3. **Branch coverage.** Every code-level branching point that produces externally observable difference has at least one NEGATIVE scenario.
4. **No field-level isolation.** No scenario tests field-level validation as its sole purpose (covered en bloc by one representative NEGATIVE).
5. **No existing fixtures.** Preconditions are described in prose, not referenced by path to existing test fixture files.
6. **No existing-test or existing-doc citations.** Existing tests and documentation are not cited as evidence — code is the only ground truth.
7. **Cross-app step prefix.** Cross-app step lines use `<service> → <service>: <action>` form. No internal-mutation lines across boundaries.
8. **No tables in flow pages.** Bullets and definition lists only. (Tables are permitted in `Result.md` for the coverage matrix.)
9. **Unique scenario names within a file.** Two scenarios in the same flow page cannot share a name.
10. **Flow-under-test references entry-point code.** The Flow under test section names the entry `file:line` and a one-sentence brief.

### Coverage and evidence (11)

11. **Stable flow IDs.** Flow IDs derive from `trigger + entry symbol`, deterministic across runs. Same flow in the same code gets the same ID. See `references/coverage-vocab.md` for the derivation table.
12. **Entrypoint exhaustiveness.** Every entrypoint discovered in the source manifest maps to exactly one owning flow OR an explicit "not externally observable" exclusion record. The Result.md coverage matrix has no orphan entrypoints.
13. **Negative scenarios cite branch.** Every NEGATIVE scenario has a `Branch covered: <file>:<line> — <condition>` line. The branch must produce an externally observable difference.
14. **Outcomes are observable.** Every Expected outcome is externally observable: response, emitted message, persisted row, file/object write, scheduled side effect, or documented absence thereof.
15. **No private-state assertions across boundaries.** Assertions about private implementation state (internal variables, intermediate computations) are forbidden unless they cross a contract boundary.
16. **Precondition taxonomy.** Preconditions distinguish four kinds: seeded persistent state, inbound event/request, feature flag/config, external dependency state. Missing-kind preconditions for kinds the flow actually depends on are a refinement gap.
17. **Mock boundaries and reasons.** Every mock names the actor boundary and the reason for mocking. Default is `Mocks: none — pure e2e`.
18. **Existing-tests-and-docs ban.** No mention of existing test files, test fixture paths, READMEs, or doc files appears in any flow page.
19. **Non-generic scenario names.** Scenario names cannot be `happy path`, `error case`, `success`, `failure` unless scoped by trigger or branch (e.g. `happy path · creates new owner`, `error case · duplicate email`).
20. **Coverage matrix at workspace level.** `Result.md` includes a coverage matrix mapping every entrypoint to its owning flow (or exclusion) and every covered branch to its NEGATIVE scenario.
21. **No empty boilerplate.** `## Unresolved` section appears only when the flow has unresolved items. Empty boilerplate sections are forbidden.

See [references/checklist-21.md](references/checklist-21.md) for rationale, examples, and counter-examples per rule.

## Refinement Workflow Context

The `duo-testplan-build` orchestrator runs three refinement phases (P3, P5, P7), each as an iteration loop of N parallel fresh-dispatch passes. Each pass:

- Reads the merged artifact + source code + this rulebook + the 21-rule checklist.
- Does NOT read prior authoring positions or prior pass files.
- Walks every rule. Emits structured patches for fixable findings, Blocked entries for non-fixable findings.

Patches use this grammar:

| Operation | Applies | Effect |
|---|---|---|
| `ADD-FLOW` | P3 | Append a new flow record for a discovered entrypoint missing from the artifact. |
| `ADD-SCENARIO` | P7 | Append a scenario for an uncovered branch or missing HAPPY/NEGATIVE. |
| `CORRECT-REF` | P3, P5, P7 | Replace a `file:line` reference that fails source validation. |
| `STRENGTHEN` | P3, P5, P7 | Rewrite a vague field (preconditions / expected / mocks) into a sharper, rule-compliant version. |
| `REMOVE-FLOW` | P3, P5 | Delete a flow with no code grounding. |
| `REMOVE-SCENARIO` | P7 | Delete a scenario with no code grounding or out of scope. |
| `REMOVE-CLAIM` | P3, P5, P7 | Delete a partial hallucination (a single line within an otherwise valid scenario). |
| `LATE-SERVICE-GAP` | P5 | Reopen a service artifact when cross-app synthesis discovers a missed flow/seam. |

Refinement passes do NOT apply patches; the orchestrator merges them. Refinement passes only PROPOSE patches against the rulebook.

## Deterministic Validators

The rulebook is enforced partly by LLM refinement passes and partly by deterministic scripted validators. The orchestrator runs validators after every patch batch (Rule 2 and Rule 12 are mechanizable).

`scripts/check-refs.py` (repo-root, NOT under any skill folder) is the canonical validator:

| Mode | Flag | Validates | Rule enforced |
|---|---|---|---|
| Ref validation (always on) | none | Every `file:line` reference under `<target-dir>` resolves to a real file under `--source-roots` with the line in range. | Rule 2 (file + line range). Does NOT validate that the line contains a specific symbol — that semantic check stays with refinement passes per Rule 13. |
| Entrypoint coverage | `--manifest <path>` | Every entrypoint listed in `unit-manifest.json` maps to exactly one per-flow markdown OR an exclusion record in `Result.md`. Also flags duplicate flow_id assignments. | Rule 12 (entrypoint exhaustiveness), Rule 11 (stable flow IDs — duplicate detection). |

Output: human-readable to stdout by default; `--json` for orchestrator-consumable structured failure list. Exit codes: 0 pass / 1 fail / 2 argument error.

The `Result.md` exclusion section format the validator recognizes:

```markdown
## Exclusions

- src/.../WarmupRunner.java:12 - <reason>
- src/.../SchedulerInit.java:8 - <reason>
```

## References

- [references/page-shape.md](references/page-shape.md) — worked examples of the per-flow page (service-local + cross-app), with edge cases.
- [references/checklist-21.md](references/checklist-21.md) — full rationale, example, and counter-example for each of the 21 rules.
- [references/coverage-vocab.md](references/coverage-vocab.md) — disambiguation table for flow, branch, scenario, entrypoint, mock, and the flow-id derivation rules.

## File Reading Limits

- Authoring and refinement agents should read this SKILL.md once per dispatch and the relevant `references/*.md` selectively (page-shape for authoring, checklist-21 for refinement passes, coverage-vocab for ambiguous calls).
- Do not read existing markdown, READMEs, or test files in the target codebase — code is the only ground truth.
- Cite `file:line` for every claim in authoring and refinement output.
