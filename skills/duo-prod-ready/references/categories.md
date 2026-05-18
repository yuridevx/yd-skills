# Duo Prod Ready Category Rubric

Source: `Duo/Research-AiCodeProdProblems/Result.md`, Thread A - 26 production failure modes of AI-generated code.

Each entry has: name, description, why AI codegen produces it, detection signal, remediation principle, and 2026 evidence anchor.

## 1. Hallucinated APIs and nonexistent symbols

- Description: AI references imports, methods, decorators, reflection strings, or feature flags that are absent from the installed SDK/runtime. This causes import-time crashes, dead request paths, or latent runtime failures.
- Why: Autoregressive completion rewards plausible names from nearby ecosystems and does not verify the live registry or installed runtime.
- Detection signal: Resolve every new import and symbol against the lockfile, generated clients, type checker, runtime docs, and minimal import smoke tests.
- Remediation principle: Replace guessed symbols with verified local APIs. Regenerate clients only through the official generator. Remove paths whose dependencies cannot resolve.
- 2026 evidence anchor: arxiv 2604.09515, arxiv 2604.20202, Firetail vendor docs.

## 2. Hallucinated packages / dependency-confusion / slopsquatting

- Description: Generated imports reference packages that do not exist, creating an opportunity for attackers to register the names or for developers to install untrusted packages just to make builds pass.
- Why: The model blends naming conventions without authenticated package-index lookup; hallucinated names can recur across prompts.
- Detection signal: Validate every new dependency against an approved registry mirror. Scan install hooks for credential exfiltration. Flag any dependency introduced only because generated code needed it.
- Remediation principle: Prefer existing approved libraries and in-repo helpers. Require security review for any new dependency introduced to satisfy generated code.
- 2026 evidence anchor: arxiv 2501.19012, DevOps.com slopsquatting coverage, Trend Micro litellm PyPI breach 2026-03, Firetail vendor docs, arxiv 2604.20202.

## 3. Injection vulnerabilities

- Description: SQL, shell, LDAP, file-path, HTML, prompt, URL, or other injection caused by string concatenation with user-controlled values flowing into interpreters.
- Why: Training examples overrepresent concise happy-path snippets; the model optimizes local functionality before adversarial data flow.
- Detection signal: Search for string-built queries, commands, templates, regexes, and HTTP calls. Trace tainted inputs from requests, CLI, env, webhooks, queues, and DB rows into interpreter sinks.
- Remediation principle: Use parameterized APIs, structured builders, strict encoders, allowlisted commands, and framework-native escaping. Delete fallback helpers that silently revert to unsafe string construction.
- 2026 evidence anchor: arxiv 2604.05292, arxiv 2605.03952, Veracode 45 percent OWASP rate, CSA 2026 security debt report, Georgia Tech 35 CVEs March 2026.

## 4. Secrets and credentials in code

- Description: API keys, tokens, passwords, bearer headers, `.env` defaults, or copied production endpoints are committed in source, tests, docs, or examples.
- Why: Models synthesize complete runnable examples; secret-like values in context can propagate into durable files.
- Detection signal: Run secret scanners on diffs. Grep for `api_key`, `token`, `Authorization`, `password`, private-key delimiters, cloud account ids, and secret-like values in tests and docs.
- Remediation principle: Remove secrets from source and history when needed. Load credentials only from secret stores or runtime config. Keep sample values syntactically invalid.
- 2026 evidence anchor: arxiv 2604.05292, arxiv 2605.03952.

## 5. Broken authentication and authorization

- Description: Code checks only whether a user is logged in while missing tenant, role, resource ownership, scope, or object-level authorization. Admin paths may be reachable through direct API calls or alternate UI flows.
- Why: Local examples show simplified auth; the model does not infer domain-specific authorization invariants.
- Detection signal: For each changed endpoint, job, resolver, or command, identify the protected resource and required actor permission. Grep for direct repository calls bypassing policy middleware, missing policy objects, and default-allow policy branches.
- Remediation principle: Centralize authorization in existing policy middleware, deny by default, and add negative tests for cross-tenant and cross-role access.
- 2026 evidence anchor: arxiv 2604.05292, arxiv 2605.03952.

## 6. Insecure deserialization and dynamic evaluation

- Description: Code accepts serialized objects, YAML, pickle, XML, plugin names, or code strings and deserializes or evaluates them with broad trust.
- Why: Short examples use convenient deserializers without threat-modeling the trust boundary.
- Detection signal: Search for `pickle`, unsafe YAML loaders, XML parsers with entity expansion, reflection-based class loading, `eval`, `Function`, dynamic imports, and plugin loading from user-controlled paths.
- Remediation principle: Use safe parsers, explicit schemas, allowlists, signed payloads, and non-executable data formats. Remove dynamic-eval fallback paths.
- 2026 evidence anchor: arxiv 2604.05292, arxiv 2605.03952.

## 7. Over-broad exception handling that swallows real errors

- Description: `try/except Exception`, `catch (Throwable)`, empty catches, `except: pass`, or log-and-continue branches hide failed writes, partial migrations, missing permissions, corrupt external responses, and other real failures.
- Why: Models use broad catches as generic resilience without understanding the failure contract.
- Detection signal: Grep for broad catches, empty catches, generic `return None/false` after catch, and logging without rethrow at API, IO, DB, queue, transaction, and migration boundaries.
- Remediation principle: Catch only expected exceptions, preserve context, fail closed, propagate where appropriate, and add tests asserting failures are visible.
- 2026 evidence anchor: IEEE Spectrum 2026 silent failures coverage, arxiv 2604.05292, trading-system 78000 USD incident 2026-01.

## 8. Unjustified fallback branches that mask bugs

- Description: Silent fallback paths turn data corruption and integration failures into plausible but wrong output.
- Why: LLMs equate robustness with continuing execution and invent fallbacks to make examples pass without knowing the business invariant.
- Detection signal: Grep for `fallback`, `default`, `best effort`, `silent`, `ignore`, `empty`, alternate provider paths, and catches that return cached or stubbed data. Trace whether callers can distinguish degraded from correct results.
- Remediation principle: Fail visibly at authoritative boundaries and return typed errors. Keep fallback only for explicitly designed degraded modes with telemetry and tests.
- 2026 evidence anchor: arxiv 2604.05292, Augment Code 2026 failure-pattern report.

## 9. Fabricated, tautological, or mock-only tests

- Description: Tests mock a dependency to return X and assert X, mirror internal transformations, or use fixtures that cannot exist in production.
- Why: The model satisfies the surface request to "add tests" by generating isolated examples that confirm its own assumptions.
- Detection signal: Ask whether each test fails on a plausible bad implementation, exercises negative paths, uses real parsers where needed, and avoids mocking the unit under test.
- Remediation principle: Add at least one behavioral or black-box test per feature that does not mock primary inputs. Use mutation testing or property-based fuzzing where appropriate.
- 2026 evidence anchor: arxiv 2603.23613, arxiv 2602.08146, Springer Empirical Software Engineering 2026, dev.to tautological-test postmortem 2026.

## 10. Dead-code accumulation

- Description: Unused helpers, alternate implementations, orphan flags, and generated comments remain because AI changes are additive by default.
- Why: Completion is additive and agents avoid deletion unless prompted to prove reachability.
- Detection signal: Run language-native unused-symbol tools, coverage reports, import graphs, `git grep` for unreferenced functions/classes/flags, route registries, command registries, and feature-flag inventories.
- Remediation principle: Delete unreachable code in the same change that replaces it. Require user approval only when deletion changes a public contract or data path.
- 2026 evidence anchor: arxiv 2601.16839, arxiv 2603.28592, AlterSquare 2026 rescue report.

## 11. Near-duplicate functions / Conditional Monsters

- Description: Multiple similar implementations of the same business rule, or one bloated function with feature-flag branches handling unrelated concerns.
- Why: AI generates locally appropriate code without searching for existing implementations; attempts to merge by surface similarity can collapse unrelated business cases.
- Detection signal: Use AST clone detection, grep repeated function-name patterns, repeated error messages, validation strings, helpers added in the same diff, and high counts of `if isX` branches.
- Remediation principle: Consolidate to one canonical implementation. If business cases differ, split along the real business axis rather than feature flags.
- 2026 evidence anchor: GitClear duplication increase, AlterSquare duplicate-rate growth, arxiv 2601.16839.

## 12. Backward-compatibility shims that should not exist

- Description: Renamed-but-keep-old-name exports, deprecated-but-still-called paths, v1/v2 branches, alias maps, and compatibility layers for refactors that never converge.
- Why: The model is biased toward additive safe-looking changes and copies legitimate library migration patterns where no external contract exists.
- Detection signal: Grep for `deprecated`, `legacy`, `old_`, `v1`, `compat`, `shim`, dual parser paths, alias maps, and fallback config names. Ask whether a live external caller or migration contract requires them.
- Remediation principle: Pick one canonical path, delete the other, and fix call sites atomically. Backward compatibility is justified only at public API boundaries with external consumers.
- 2026 evidence anchor: arxiv 2601.16839, AlterSquare 2026 rescue report, project standing policy.

## 13. Premature or wrong abstractions

- Description: Interfaces with one implementation, pass-through wrappers, factories without a second use case, and abstractions that hide critical operational details.
- Why: The model imitates textbook OO and design-pattern examples and optimizes for clean-looking code over minimal moving parts.
- Detection signal: Find abstract bases or interfaces used once, wrappers around single library calls with no behavior, tests exercising only wrappers, and abstractions whose call sites still branch on concrete type.
- Remediation principle: Inline the wrapper, delete the interface, and introduce abstraction only when two or more stable concrete use cases need the same behavior.
- 2026 evidence anchor: ai-infra-link 2026 ride-sharing incident, arxiv 2601.16839, Springer Empirical Software Engineering 2026.

## 14. Defensive validation at internal boundaries

- Description: Null checks, type guards, and argument validation inside private functions whose callers already maintain the invariant.
- Why: The model cannot track caller invariants and defensively codes every parameter from public-library training patterns.
- Detection signal: Look for validation of private types or arguments that come exclusively from trusted internal call sites, and identical validation duplicated across internal boundaries.
- Remediation principle: Validate at external trust boundaries, trust internal callers, and let invariant violations fail loudly.
- 2026 evidence anchor: Project standing policy and 2026 maintainability literature reinforcing arxiv 2601.16839.

## 15. Missing error handling at REAL boundaries

- Description: External IO, network, FFI, untrusted-input deserialization, or service calls lack timeout, retry policy, error mapping, or circuit breaker.
- Why: The model assumes happy paths and does not reliably distinguish trust boundaries.
- Detection signal: Search external operations without explicit timeout, retry, circuit-breaker, or error-mapping policy, and untrusted deserialization without schema validation.
- Remediation principle: Enforce the project-wide rule that every trust-boundary call has an explicit error policy.
- 2026 evidence anchor: arxiv 2602.08146, arxiv 2604.05292, silent-failure-hunter rubric.

## 16. Tight coupling and poor file cohesion

- Description: Large files combine UI, persistence, payment, API, storage, and unrelated domains; imports become deeply nested and modules become god modules.
- Why: AI appends to high-context local files instead of evaluating cohesion across the codebase.
- Detection signal: Count top-level domain concepts per file, inspect afferent/efferent coupling, and flag files importing from many domains.
- Remediation principle: Split by cohesive responsibility. A file should have one clear reason to change.
- 2026 evidence anchor: AlterSquare 2026 rescue report, arxiv 2601.16839, Springer Empirical Software Engineering 2026.

## 17. Leaky abstractions

- Description: Helpers or services expose internal DB models, raw HTTP clients, SDK-specific exceptions, config names, serialization details, or persistence fields to callers that should see a domain interface.
- Why: The model copies convenient lower-level objects across layers rather than deriving intended boundaries.
- Detection signal: Look for DTO/entity mixing, raw response propagation, SDK exceptions in domain code, database fields in UI code, and callers checking implementation-specific flags.
- Remediation principle: Use narrow domain return types and errors, keep adapters at boundaries, and remove pass-through abstractions that hide nothing.
- 2026 evidence anchor: arxiv 2601.16839.

## 18. Configuration sprawl

- Description: Magic numbers or strings are inline, one-off environment variables appear for single use cases, constants are duplicated, and defaults conflict across modules.
- Why: AI generates locally and often misses existing config modules or registries.
- Detection signal: Use duplicate-constant detectors, grep ad-hoc `os.getenv(...)` outside centralized config, and scan for repeated magic literals.
- Remediation principle: Use a single canonical config module per service, validate env schema at startup, and remove inline magic.
- 2026 evidence anchor: arxiv 2601.16839, AlterSquare 2026 rescue report, agent-sprawl 2026 patterns.

## 19. Observability gaps

- Description: Critical paths lack structured logging, correlation ids, metrics, or tracing; logs omit relevant state; error paths are invisible.
- Why: AI generates happy-path code and does not surface observability unless prompted.
- Detection signal: Check critical-path functions for structured logs, error logs with correlation id, metrics on retry/failure, and print/console-only logging in server code.
- Remediation principle: Enforce the project logging schema, correlation ids at request entry, and metric plus log at every retry and failure boundary.
- 2026 evidence anchor: arxiv 2604.09409, silent-failure-hunter rule, Microsoft Security observability blog 2026.

## 20. Race conditions in concurrent code

- Description: Async, threaded, or parallel code mutates shared maps, caches, temp files, transactions, UI state, or retry counters without locks, atomicity, idempotency, or cancellation handling.
- Why: Single-threaded snippets dominate training data and the model rarely simulates interleavings.
- Detection signal: Search new async tasks, goroutines, promises, thread pools, and parallel streams for shared mutable state, cache writes, transaction boundaries, and missing stress tests.
- Remediation principle: Use existing concurrency primitives, isolate state, make retries idempotent, and prefer single-owner queues over shared mutation.
- 2026 evidence anchor: ai-infra-link 2026 ride-sharing race-condition incident, IEEE Spectrum 2026, arxiv 2604.05292.

## 21. Resource leaks

- Description: Files, sockets, DB cursors, HTTP responses, subprocesses, timers, subscriptions, browser pages, or GPU handles are opened without deterministic close/cancel/dispose.
- Why: Short generated examples omit lifecycle management, especially around errors and early returns.
- Detection signal: Grep for open/connect/subscribe/timer/client/spawn/stream patterns and check close/dispose symmetry, including error paths.
- Remediation principle: Use language idioms for scoped resources such as `using`, `defer`, and context managers. Close in `finally` when no scoped idiom exists.
- 2026 evidence anchor: arxiv 2604.05292, Endor Labs 2026 vulnerability catalog.

## 22. Performance regressions hidden in O(n^2) / N+1 patterns

- Description: Nested loops over the same collection, repeated IO inside hot loops, sync-in-async, chatty calls, missing pagination, unbounded results, and ORM N+1 queries.
- Why: The model generates the working solution with the smallest semantic distance, not the cheapest production behavior.
- Detection signal: Run complexity scans, hot-loop IO checks, ORM N+1 detectors, and benchmarks sized to production cardinality.
- Remediation principle: Profile under representative load and replace patterns with batched, indexed, paginated, streamed, or cached equivalents.
- 2026 evidence anchor: CodeRabbit 2026 1.7x issue-rate report, arxiv 2601.16839.

## 23. Type-system escape-hatch abuse

- Description: `any`, `Object`, `unknown as`, non-null assertions, `# type: ignore`, `@ts-ignore`, or permissive generics erase intent without justification.
- Why: The model is trained to compile clean and uses escape hatches when precise typing requires more reasoning.
- Detection signal: Grep for type escape hatches and track their ratio per file. Require justification comments for genuinely dynamic boundaries.
- Remediation principle: Replace with precise types. Narrow dynamic data at the boundary and propagate precise types inward.
- 2026 evidence anchor: arxiv 2601.16839, Springer Empirical Software Engineering 2026.

## 24. WHAT-comments and comment rot

- Description: Comments restate obvious code, reference removed code, describe wrong behavior, contain unresolved AI TODOs, or produce long generated docstrings for trivial functions.
- Why: The model produces explanatory prose by default and cannot validate comment truth against current code.
- Detection signal: Identify comments whose deletion would not reduce understanding, comments referencing missing symbols/files, TODOs older than 30 days, and comments contradicting code.
- Remediation principle: Default to no comment. Keep only concise WHY-comments for non-obvious constraints and invariants.
- 2026 evidence anchor: arxiv 2601.07786, Springer Empirical Software Engineering 2026.

## 25. Unreproducible / environment-specific builds

- Description: Generated code relies on local files, machine-specific paths, unpinned packages, implicit tools, unstated services, or platform-only behavior that CI/production cannot reproduce.
- Why: The model infers setup from local context snippets without checking CI images, lockfiles, deployment manifests, or clean checkout behavior.
- Detection signal: Run clean checkout/CI build, inspect new tool invocations, lockfile changes, absolute paths, undocumented env vars, and tests that require local services.
- Remediation principle: Pin dependencies, document required services in existing config, and treat CI as the reproducibility authority.
- 2026 evidence anchor: arxiv 2604.20202, Firetail dependency docs.

## 26. Boilerplate cognitive debt + AI-induced merge churn

- Description: Large generated wrappers or glue code become human-owned before being understood; the same areas are repeatedly rewritten across sessions; AI-created TODOs accumulate.
- Why: AI generation speed exceeds human comprehension speed and the model lacks durable memory of prior decisions.
- Detection signal: Compare lines-per-commit with owner understanding, inspect churn metrics, grep TODO/HACK/FIXME in AI-authored commits, and ask whether the code would fit in a much smaller hand-written design.
- Remediation principle: Delete what is not load-bearing, require explanation before merging, and close AI-introduced TODOs in the same PR or treat them as blockers.
- 2026 evidence anchor: porkicoder 2026 AI coding paradox essay, arxiv 2601.07786, arxiv 2603.28592, MIT Technology Review 2026.
