# 21-Rule Refinement Checklist — Full Detail

Each refinement pass walks this list. For each rule that fails, the pass emits a structured patch (if mechanically fixable) or a Blocked entry (if not).

## Style and Structure (10 rules)

### Rule 1 — Mandatory sections

**Rule:** Every scenario has Preconditions, Steps, Expected, Mocks, Code refs.

**Rationale:** Missing sections invite reader interpretation and make scenarios non-executable. The five sections together provide a complete e2e specification.

**Compliant:**
```
### Scenario: creates owner · HAPPY
- Preconditions: ...
- Steps: ...
- Expected: ...
- Mocks: none — pure e2e
- Code refs: ...
```

**Non-compliant (refinement patches with STRENGTHEN):**
```
### Scenario: creates owner · HAPPY
- Steps: 1. POST /owners
- Expected: 201
```
Missing Preconditions, Mocks, Code refs.

### Rule 2 — Code refs validate

**Rule:** Every `file:line` reference points at a real symbol on that line.

**Rationale:** Bad refs erode trust in the entire plan; readers cannot navigate to the code being tested. Refinement passes mechanize this via `check-refs.py`.

**Refinement action:** CORRECT-REF patch if the symbol is elsewhere in the file; REMOVE-CLAIM if the symbol doesn't exist.

### Rule 3 — Branch coverage

**Rule:** Every code-level branching point that produces externally observable difference has at least one NEGATIVE scenario.

**Rationale:** The core promise of the test plan — every observable path is exercised.

**Compliant:** Three NEGATIVES for a flow with three observable branches (invalid email, duplicate email, downstream service unavailable).

**Non-compliant:** Two NEGATIVEs but the source has three observable branches. Refinement patches with `ADD-SCENARIO` for the missing branch.

### Rule 4 — No field-level isolation

**Rule:** No scenario tests field-level validation as its sole purpose.

**Rationale:** Field-level edge cases explode combinatorially. The plan covers behaviors, not validation rule catalogs.

**Compliant:** One NEGATIVE `rejects owner with invalid required field` covers all `@NotNull` violations.

**Non-compliant:** Separate scenarios for `firstName null`, `lastName null`, `email null`, etc. Refinement patches with REMOVE-SCENARIO for the redundant ones and STRENGTHEN to consolidate the survivor.

### Rule 5 — No existing fixtures

**Rule:** Preconditions are described in prose, not referenced by path to existing test fixture files.

**Rationale:** Existing tests are excluded inputs. Referencing their fixtures implicitly imports their assumptions and couples this plan to that test suite.

**Compliant:** `Seeded state: owner table with 3 rows: {Ada, age 30, email a@x}, {Brian, age 25, email b@x}, {Cleo, age 40, email c@x}`.

**Non-compliant:** `Seeded state: load fixtures from src/test/resources/owners.sql`.

### Rule 6 — No existing-test or existing-doc citations

**Rule:** Existing tests and documentation are not cited as evidence.

**Rationale:** Code is the only ground truth. Documentation may be stale; tests may encode wrong assumptions.

**Refinement action:** REMOVE-CLAIM for citations of paths matching the exclusion set (`*.md`, `test/`, `tests/`, `README`, etc.).

### Rule 7 — Cross-app step prefix

**Rule:** Cross-app step lines use `<service> → <service>: <action>` form.

**Rationale:** Cross-app flows must be readable as orchestration across services, not as one service's internal walk. The prefix makes the boundary explicit.

**Compliant:** `api-gateway → customers-service: GET /owners/42`

**Non-compliant:** `look up the owner in customers-service` (no actor prefix). Refinement patches with STRENGTHEN.

### Rule 8 — No tables in flow pages

**Rule:** Bullets and definition lists only in `test-plan/**/*.md`. Tables permitted in `Result.md` for the coverage matrix.

**Rationale:** Tables compress structure but resist iterative editing by refinement passes. Bullet lists are stable under structural mutation.

### Rule 9 — Unique scenario names within a file

**Rule:** Two scenarios in the same flow page cannot share a name.

**Rationale:** Downstream tools key on `(flow-id, scenario-name)`. Collisions break addressability.

### Rule 10 — Flow-under-test references entry-point code

**Rule:** The Flow under test section names the entry `file:line` and a one-sentence brief.

**Rationale:** Readers (human or downstream) need to navigate to the code being tested.

## Coverage and Evidence (11 rules)

### Rule 11 — Stable flow IDs

**Rule:** Flow IDs derive from trigger + entry symbol. Same flow in same code gets same ID across runs.

**Derivation table:**

| Trigger kind | Pattern | Example |
|---|---|---|
| HTTP | `<method-lower>-<path-kebab>` | `post-owners`, `get-owners-id` |
| Kafka consumer | `consume-<topic-kebab>` | `consume-petclinic-owner-updated` |
| Kafka producer (consumer-independent) | `publish-<topic-kebab>` | `publish-petclinic-audit-events` |
| gRPC | `grpc-<service-lower>-<rpc-lower>` | `grpc-ownersservice-getowner` |
| Cron | `cron-<job-kebab>` | `cron-cleanup-stale-sessions` |
| S3 trigger | `s3-<bucket-kebab>-<event>` | `s3-uploads-objectcreated` |
| Cross-app | `crossapp-<purpose-kebab>` | `crossapp-view-owner-profile` |

Collisions resolved by appending `-2`, `-3`. IDs persist across runs via the orchestrator's flow-id mint in `unit-manifest.json`.

### Rule 12 — Entrypoint exhaustiveness

**Rule:** Every entrypoint discovered in the source manifest maps to exactly one owning flow OR an explicit "not externally observable" exclusion record.

**Rationale:** Coverage at the workspace level — no orphan entrypoints means the test plan is complete.

**Refinement action:** `ADD-FLOW` patch for missing flow, OR `STRENGTHEN` patch on the workspace-level `Result.md` exclusions field for entrypoints that genuinely produce no externally observable behavior independent of other flows. The 8 valid patch operations are `ADD-FLOW`, `ADD-SCENARIO`, `CORRECT-REF`, `STRENGTHEN`, `REMOVE-FLOW`, `REMOVE-SCENARIO`, `REMOVE-CLAIM`, `LATE-SERVICE-GAP` — no other operations exist.

### Rule 13 — Negative scenarios cite branch

**Rule:** Every NEGATIVE scenario has a `Branch covered: <file>:<line> — <condition>` line. The branch must produce externally observable difference.

**Rationale:** A NEGATIVE without a branch citation is unverifiable. A NEGATIVE citing a no-observable-difference branch is wasted.

**Compliant:** `Branch covered: src/.../OwnerController.java:62 — @Valid fails for malformed email`

**Non-compliant:** A NEGATIVE that lists `Branch covered:` for `src/.../OwnerController.java:120 — internal logging branch` would be removed by refinement (REMOVE-SCENARIO) because the branch produces no observable difference.

### Rule 14 — Outcomes are observable

**Rule:** Every Expected outcome is externally observable: response, emitted message, persisted row, file/object write, scheduled side effect, or documented absence thereof.

**Compliant:** `Response 201 with body matching request plus generated id`; `No owner row created in MySQL`.

**Non-compliant:** `Internal counter incremented` (private state). `Helper function called` (implementation detail).

### Rule 15 — No private-state assertions across boundaries

**Rule:** Assertions about private implementation state (internal variables, intermediate computations) are forbidden unless they cross a contract boundary.

**Rationale:** Private-state assertions couple the plan to implementation details. Refactors then break the plan, not because behavior changed but because internals did.

**Compliant:** `Kafka message of kind owner.created emitted` (crosses boundary into Kafka).

**Non-compliant:** `The cache map has key `owner:42`` (private state of one service, never inspected by another service).

### Rule 16 — Precondition taxonomy

**Rule:** Preconditions distinguish four kinds explicitly:
- Seeded persistent state (DB rows, file contents, message broker state at start)
- Inbound event/request (the triggering input)
- Feature flag / config (runtime configuration that affects branching)
- External dependency state (reachability and content of downstream systems)

**Rationale:** Conflating these makes scenarios hard to set up reproducibly. Missing a kind that the flow actually depends on is a coverage gap.

**Refinement action:** `STRENGTHEN` patch on the scenario's Preconditions field — used both to split conflated preconditions and to add a missing kind. The 8 valid patch operations are `ADD-FLOW`, `ADD-SCENARIO`, `CORRECT-REF`, `STRENGTHEN`, `REMOVE-FLOW`, `REMOVE-SCENARIO`, `REMOVE-CLAIM`, `LATE-SERVICE-GAP` — there is no `ADD-PRECONDITION` operation.

### Rule 17 — Mock boundaries and reasons

**Rule:** Every mock names the actor boundary AND the reason for mocking. Default is `Mocks: none — pure e2e`.

**Compliant:**
- `Mocks: none — pure e2e`
- `Mocks: payment-gateway stubbed (external SaaS not in workspace); clock fixed at 2026-01-01T12:00:00Z (deterministic time assertion).`

**Non-compliant:**
- `Mocks: yes` (no boundary, no reason)
- `Mocks: PaymentService` (no reason)

### Rule 18 — Existing-tests-and-docs ban

**Rule:** No mention of existing test files, fixture paths, READMEs, or doc files appears in any flow page.

**Refinement action:** REMOVE-CLAIM for any line matching exclusion-set paths.

### Rule 19 — Non-generic scenario names

**Rule:** Scenario names cannot be `happy path`, `error case`, `success`, `failure` unless scoped by trigger or branch.

**Compliant:** `creates new owner with all required fields · HAPPY`, `rejects duplicate email · NEGATIVE`.

**Non-compliant:** `happy path · HAPPY`. Refinement patches with STRENGTHEN, generating a descriptive scope.

### Rule 20 — Coverage matrix at workspace level

**Rule:** `Result.md` includes a coverage matrix mapping every entrypoint to its owning flow (or exclusion) and every covered branch to its NEGATIVE scenario.

**Format (table allowed in Result.md, not in flow pages):**

```
## Coverage Matrix

### Entrypoints → Flows
| Entrypoint | Flow |
|---|---|
| src/.../OwnerController.java:54 | post-owners |
| src/.../OwnerController.java:88 | get-owners-id |
| src/.../WarmupRunner.java:12 | (excluded: no external trigger) |

### Branches → Scenarios
| Branch | Scenario |
|---|---|
| OwnerController.java:62 — invalid email | post-owners · rejects owner with invalid email |
| OwnerController.java:71 — duplicate email | post-owners · rejects duplicate email |
| ... | ... |
```

### Rule 21 — No empty boilerplate

**Rule:** `## Unresolved` section appears only when the flow has unresolved items. Empty boilerplate sections are forbidden.

**Compliant:** Omit the `## Unresolved` section if there's nothing unresolved.

**Non-compliant:** `## Unresolved\n- None`. Refinement patches with REMOVE-CLAIM.

## How refinement passes use this checklist

For each rule:
1. Pass reads the merged artifact.
2. Pass walks the rule against every flow / scenario in the artifact.
3. For each failing instance the pass can mechanically fix → emit a patch (`ADD-*` / `CORRECT-REF` / `STRENGTHEN` / `REMOVE-*`).
4. For each failing instance the pass cannot mechanically fix → emit a Blocked entry with rationale.
5. After walking all rules, the pass writes Status (CLEAN if no patches/blocked; PATCHED if patches; BLOCKED if any Blocked entries).

Patch / diff-stance merge order (from `duo-testplan/SKILL.md` Per-Field Merge Table): REMOVE / `drop` → CORRECT-REF / `replace` → ADD / `augment` → STRENGTHEN → format-only. Validators run after each batch.
