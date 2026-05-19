# Page Shape — Worked Examples

Concrete examples of the per-flow page shape defined in `linked-testplan/SKILL.md`. Use these as templates when authoring; check against them when refining.

## Service-Local Flow: HTTP POST

```markdown
# post-owners

## Flow under test
Trigger: HTTP POST /owners
Entry: src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java:54
Brief: Creates a new owner from request body; persists to MySQL; returns 201 with the created owner.

## Scenarios

### Scenario: creates new owner with all required fields · HAPPY
- Preconditions:
  - Seeded state: owner table empty for the unique-email constraint
  - Inbound event: POST /owners with body `{firstName, lastName, address, city, telephone, email}` all present and well-formed
  - Feature flag / config: none
  - External dependency state: MySQL reachable
- Steps:
  1. Send POST /owners with the request body
  2. Read the persisted row by id from the Location header
- Expected:
  - Response 201 with body matching the request plus generated id
  - Owner row exists in MySQL with all fields matching the request
  - Location header set to /owners/{id}
- Mocks: none — pure e2e
- Code refs: src/main/java/.../OwnerController.java:54, src/main/java/.../OwnerRepository.java:18

### Scenario: rejects owner with invalid email · NEGATIVE
- Branch covered: src/main/java/.../OwnerController.java:62 — @Valid fails for malformed email
- Preconditions:
  - Seeded state: owner table empty
  - Inbound event: POST /owners with email `not-an-email`, all other fields valid
- Steps:
  1. Send POST /owners with the malformed-email body
- Expected:
  - Response 400 with validation error in body
  - No owner row created in MySQL
- Mocks: none — pure e2e
- Code refs: src/main/java/.../OwnerController.java:62

### Scenario: rejects duplicate email · NEGATIVE
- Branch covered: src/main/java/.../OwnerRepository.java:23 — unique-constraint violation
- Preconditions:
  - Seeded state: existing owner row with email `ada@example.com`
  - Inbound event: POST /owners with email `ada@example.com`, other fields valid
- Steps:
  1. Send POST /owners with the duplicate-email body
- Expected:
  - Response 409 conflict
  - No new owner row created in MySQL
  - Original owner row unchanged
- Mocks: none — pure e2e
- Code refs: src/main/java/.../OwnerRepository.java:23
```

Note:
- Rule 19 satisfied — scenario names scoped (`creates new owner with all required fields`, not `happy path`).
- Rule 13 satisfied — every NEGATIVE has a `Branch covered:` line with `file:line`.
- Rule 4 satisfied — one representative NEGATIVE for validation (not one per field).

## Service-Local Flow: Kafka Consumer

```markdown
# consume-petclinic-owner-updated

## Flow under test
Trigger: Kafka topic `petclinic.owner.updated`
Entry: src/main/java/.../OwnerUpdateConsumer.java:31
Brief: Consumes owner-update events from Kafka; updates the local cached projection in Redis; emits an analytics event downstream.

## Scenarios

### Scenario: updates cached projection on valid event · HAPPY
- Preconditions:
  - Seeded state: Redis has stale `owner:{id}` key from prior projection
  - Inbound event: Kafka message on `petclinic.owner.updated` with owner-id, updated fields, version > cached version
  - External dependency state: Redis reachable; downstream analytics topic available
- Steps:
  1. Publish the Kafka message to the topic
  2. Wait for consumer offset to advance past the message
  3. Read `owner:{id}` from Redis
  4. Read latest message on the analytics topic
- Expected:
  - Redis `owner:{id}` reflects the updated fields and the new version
  - Analytics topic has a message of kind `owner-projection-updated` with the same id
- Mocks: none — pure e2e
- Code refs: src/main/java/.../OwnerUpdateConsumer.java:31, src/main/java/.../OwnerProjection.java:18

### Scenario: ignores stale version · NEGATIVE
- Branch covered: src/main/java/.../OwnerUpdateConsumer.java:48 — incoming version <= cached version
- Preconditions:
  - Seeded state: Redis has `owner:{id}` at version 5
  - Inbound event: Kafka message with version 3
- Steps:
  1. Publish the stale Kafka message
  2. Wait for consumer offset to advance
- Expected:
  - Redis `owner:{id}` unchanged (still version 5)
  - No message emitted to analytics topic
- Mocks: none — pure e2e
- Code refs: src/main/java/.../OwnerUpdateConsumer.java:48
```

## Service-Local Flow: Cron

```markdown
# cron-cleanup-stale-sessions

## Flow under test
Trigger: cron schedule `0 */15 * * * *` (every 15 minutes)
Entry: src/main/java/.../SessionCleanupJob.java:22
Brief: Scans sessions table for entries older than 24h; deletes them; logs count to metrics.

## Scenarios

### Scenario: deletes stale sessions, leaves fresh sessions · HAPPY
- Preconditions:
  - Seeded state: sessions table with 3 rows created 25h ago (stale) and 2 rows created 1h ago (fresh)
  - External dependency state: metrics endpoint reachable; clock fixed at a known wall-time
- Steps:
  1. Trigger the cron job (manually or wait for schedule)
  2. Read sessions table
  3. Read metrics endpoint for the `sessions.deleted` counter
- Expected:
  - Sessions table contains only the 2 fresh rows
  - Metrics counter `sessions.deleted` incremented by 3
- Mocks: clock fixed at 2026-01-01T12:00:00Z (deterministic time assertions for the 24h threshold)
- Code refs: src/main/java/.../SessionCleanupJob.java:22, src/main/java/.../SessionRepository.java:41

### Scenario: handles zero stale sessions · HAPPY
- Preconditions:
  - Seeded state: sessions table with only fresh rows
- Steps:
  1. Trigger the cron job
- Expected:
  - Sessions table unchanged
  - Metrics counter `sessions.deleted` not incremented (or incremented by 0)
- Mocks: clock fixed at known wall-time
- Code refs: src/main/java/.../SessionCleanupJob.java:22

### Scenario: continues after delete failure for a single row · NEGATIVE
- Branch covered: src/main/java/.../SessionCleanupJob.java:38 — catch block around per-row delete
- Preconditions:
  - Seeded state: sessions table with 3 stale rows, one with a constraint that triggers a delete failure (e.g. FK from sessions_audit to one of them)
- Steps:
  1. Trigger the cron job
  2. Read sessions table
  3. Read metrics endpoint
- Expected:
  - The 2 deletable stale rows are deleted; the constrained row remains
  - Metrics counter `sessions.deleted` incremented by 2
  - Metrics counter `sessions.cleanup.errors` incremented by 1
- Mocks: clock fixed
- Code refs: src/main/java/.../SessionCleanupJob.java:38
```

## Cross-App Flow

```markdown
# crossapp-view-owner-profile

## Flow under test
Trigger: HTTP GET /api/customer/owners/{id} (browser-initiated through api-gateway)
Entry: api-gateway/routes/owners.js:14
Brief: api-gateway aggregates customers-service (owner + pets) with visits-service (visit history per pet) into one response.

## Scenarios

### Scenario: returns owner with pets and visit history · HAPPY
- Preconditions:
  - Seeded state: customers-service has owner `{id: 42, name: "Ada"}` with pets `[{id: 1}, {id: 2}]`; visits-service has visits `[{petId: 1, date: ...}, {petId: 2, date: ...}]`
  - Inbound event: GET /api/customer/owners/42 from browser
  - External dependency state: customers-service and visits-service both reachable through service discovery
- Steps:
  1. browser → api-gateway: GET /api/customer/owners/42
  2. api-gateway → customers-service: GET /owners/42
  3. customers-service → api-gateway: OwnerSummaryResponse {owner, pets}
  4. api-gateway → visits-service: GET /pets/visits?petId=1&petId=2
  5. visits-service → api-gateway: Visit[]
  6. api-gateway → browser: { owner, visitsByPetId }
- Expected:
  - browser receives 200 with the aggregated body
  - body.owner matches the customers-service projection
  - body.visitsByPetId is keyed by pet id with the visits array per key
- Mocks: none — pure e2e
- Code refs: api-gateway/routes/owners.js:14, customers-service/.../OwnerController.java:78, visits-service/.../VisitController.java:32

### Scenario: returns owner without visits when visits-service unavailable · NEGATIVE
- Branch covered: api-gateway/routes/owners.js:29 — catch block around visits-service call
- Preconditions:
  - Seeded state: customers-service has owner `{id: 42}` with pets
  - External dependency state: customers-service reachable; visits-service returning 503 (or timing out beyond the configured threshold)
- Steps:
  1. browser → api-gateway: GET /api/customer/owners/42
  2. api-gateway → customers-service: GET /owners/42
  3. customers-service → api-gateway: OwnerSummaryResponse
  4. api-gateway → visits-service: GET /pets/visits?... (fails)
  5. api-gateway → browser: { owner, visitsByPetId: {}, partial: true }
- Expected:
  - browser receives 200 (or 206 if the implementation uses partial-content)
  - body.owner present
  - body.visitsByPetId empty
  - body.partial flag set
- Mocks: visits-service stubbed to return 503 (simulating outage; not an actual outside-workspace mock — this is the "external-service-unavailable" required scenario)
- Code refs: api-gateway/routes/owners.js:29
```

Note on the cross-app mock: visits-service is not a workspace-external actor, but the unavailable-state scenario requires injecting failure. Document the boundary and reason. Mock policy permits this for the "external-service-unavailable" required scenario (see SKILL.md Scenario Policy).

## Edge cases

### Flow with no branches

A flow with no externally observable branches (e.g. a pure idempotent GET /health endpoint) gets ONE HAPPY scenario. Rule 3 does not force a NEGATIVE if no branch produces observable difference. Document `Brief: ... — no externally observable branches` for clarity.

### Flow with a synchronous external dependency

Per Scenario Policy: required to have one NEGATIVE per external dependency for the unavailable/timeout case, even if the only branch in code is the catch block.

### Flow whose entry point is not externally observable

Some entry points (internal worker constructors, framework lifecycle hooks, library callbacks) do not produce externally observable behavior independent of another flow. These get an exclusion record in `Result.md` (NOT a flow file) with rationale:

```
## Exclusions
- src/.../WarmupRunner.java:12 — runs on application startup, no external trigger, idempotent cache warmup. Not externally observable independent of subsequent request flows.
```

Rule 12 requires every entrypoint to map to a flow OR an exclusion. No orphans.

### Empty Unresolved section

Per Rule 21: omit the `## Unresolved` section entirely if there are no unresolved items. Do not write `## Unresolved\n- None` as boilerplate.
