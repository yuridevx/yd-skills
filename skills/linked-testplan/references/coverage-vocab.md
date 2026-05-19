# Coverage Vocabulary — Disambiguation

When two terms could plausibly apply to the same code construct, this reference picks one and explains why. Refinement passes follow these calls.

## Flow vs Step vs Helper Function

| Construct | Term |
|---|---|
| HTTP handler entered by a request | **flow** (its own page) |
| Kafka consumer handler for a topic | **flow** (its own page) |
| Cron `@Scheduled` method | **flow** (its own page) |
| Public service method called by an HTTP handler that aggregates two downstream calls | **step** within the calling flow, NOT its own flow |
| Private validation method | **helper** — invisible in test plan; only its observable effect (the rejection) appears in a scenario |
| Service-to-service REST call inside a flow | **step** in the calling flow; the receiving handler is a step in a different (cross-app) flow |

**Heuristic:** if the construct is reachable independently from outside the workspace (HTTP, Kafka, cron, S3, gRPC), it is a flow. If it is only reachable from another flow, it is a step.

## Flow vs Cross-App Flow

| Property | Service-local flow | Cross-app flow |
|---|---|---|
| Owning service | exactly one | participates ≥ 2 |
| Triggering actor | service-internal (HTTP, Kafka consumer, cron, S3 event, gRPC method on this service) | external (browser, mobile, third-party API) entering through an api-gateway or equivalent boundary |
| File location | `test-plan/<repo>/<svc>/flows/<flow-id>.md` | `test-plan/cross-app/flows/<flow-id>.md` |
| Step format | terse imperative bullets | actor-prefixed: `<service> → <service>: <action>` |
| Internal mutations | shown in pseudocode steps | NEVER shown — boundary only |

**Heuristic:** if the test plan must reference two or more workspace services as participating actors, it is cross-app. Otherwise service-local.

## Branch vs Field Validation

A **branch** for test-plan purposes produces externally observable difference (different response code, different emitted message, different persisted state, different downstream call, OR documented absence of one).

Code branches that produce no externally observable difference (internal logging branches, format-only differences, performance optimizations) are NOT branches and do NOT require a NEGATIVE scenario.

| Code construct | Branch for test plan? |
|---|---|
| `if (email is invalid) return 400` | YES (different response) |
| `if (debug) log("verbose")` | NO (no external observability) |
| `if (cache hit) read from cache; else read from DB` | NO if response is identical; YES if response differs |
| `switch (kind) { case A: emit topicA; case B: emit topicB; }` | YES (different emission) |
| `try { ... } catch (e) { log(e); rethrow; }` | NO (rethrow is the same behavior) |
| `try { ... } catch (e) { return errorResponse; }` | YES (different response) |

**Field validation** is a special case of branching where each `@Valid` rule on a field is a branch. Per Rule 4, do NOT create one scenario per field rule. Create ONE representative NEGATIVE per validation surface (per controller, per consumer) that covers all field-level rejections en bloc.

## Entrypoint vs Step vs Internal Call

| Code location | Term |
|---|---|
| Method annotated `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` etc. | **entrypoint** of an HTTP flow |
| Method annotated `@KafkaListener` / `@MessageListener` etc. | **entrypoint** of a Kafka-consumer flow |
| Method annotated `@Scheduled` / `@Cron` etc. | **entrypoint** of a cron flow |
| `public` gRPC service method registered with a server | **entrypoint** of a gRPC flow |
| Method annotated S3 / SQS / DDB-stream event listener | **entrypoint** of an event flow |
| Call to a downstream service's HTTP API from within a flow | **step** in this flow + **entrypoint** of a different flow in that downstream service |
| Call to a private method of the same class | **internal call** — not visible in the test plan |
| Method invoked by framework lifecycle (e.g. constructor injection, `@PostConstruct`) | **lifecycle hook** — entrypoint candidate IF it produces externally observable effect; otherwise exclusion record |

## Mock vs Stub vs Real Dependency

| Setup | Term |
|---|---|
| Real database with controlled seed data | real dependency — `Mocks: none — pure e2e` |
| Real Kafka with controlled topic content | real dependency |
| Real downstream service in the workspace | real dependency |
| Third-party API replaced with a stub | **mock** — must name boundary + reason |
| Payment gateway replaced with a deterministic stub | **mock** — outside workspace |
| Clock fixed to a known wall-time | **mock** — nondeterminism replacement; must name reason ("deterministic time assertion") |
| Random ID generator replaced with deterministic generator | **mock** — same as clock |
| Workspace-internal service made unavailable to test external-dependency-unavailable scenario | **mock** with reason "external-service-unavailable required scenario" (per Scenario Policy) |
| Test fixture loaded from existing test file | NOT permitted (rule 5); preconditions described in prose |

## Observable Outcome vs Private State

Observable outcomes (all permitted as Expected entries):
- HTTP response (status + body + headers)
- Kafka message emitted on a topic (key + value + headers)
- gRPC response returned
- Database row written, updated, or deleted (queryable from outside the flow)
- File or S3 object written
- Scheduled job created in a job queue
- Downstream HTTP / gRPC call made
- The documented ABSENCE of any of the above ("no row created", "no message emitted")

Private state (forbidden as Expected entries):
- Internal counters, intermediate variables, caches
- Helper-function call counts
- Method invocations on private collaborators (unless they cross a boundary to a separate observable system)
- Log lines (unless they reach an observable log aggregator and the aggregator is part of the workspace under test)

**Heuristic:** "could a separate process running outside the flow observe this?" If yes, it's observable. If no, it's private.

## Unresolved Categories

When a refinement pass cannot mechanically fix a finding, it emits a Blocked entry. Categorize Blocked entries to help downstream triage:

| Category | Definition |
|---|---|
| `EVIDENCE-MISSING` | The artifact claims a behavior the pass cannot find in source. Either source is incomplete or the claim is wrong. |
| `BRANCH-AMBIGUOUS` | A code branch exists but the pass cannot determine whether it produces externally observable difference. Requires human review. |
| `ENTRY-POINT-UNCLEAR` | A potential entrypoint exists but its registration / activation mechanism is not statically determinable. Requires human review. |
| `EXTERNAL-CONTRACT-UNRESOLVED` | A cross-app seam points to an external service whose contract is not in the workspace and cannot be inferred from source. Requires either external contract spec or a "trust the integration" decision. |
| `RULEBOOK-CONFLICT` | A rule would require a fix that conflicts with another rule. Requires rulebook clarification. |

These categories live in the `## Blocked` section of refinement pass files and surface in `Result.md → Unresolved` if they survive the iteration budget.

## Scenario Tag Vocabulary

- `HAPPY` — the success path of the flow. Every flow has at least one.
- `NEGATIVE` — a failure / rejection / partial-state path. Every observable branch has at least one. External-service-unavailable scenarios for synchronous dependencies are tagged NEGATIVE.

No other tags. Specifically:
- `EDGE` — not used (treat as HAPPY or NEGATIVE depending on outcome).
- `PERFORMANCE` — out of scope (test plan is for behavior, not perf).
- `SECURITY` — out of scope unless the security check is itself a flow-level branch (e.g. 401 vs 200 IS a branch with observable difference).
