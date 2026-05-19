# solo-runtestplan Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new `solo-runtestplan` skill to the `yd` plugin that autonomously executes e2e test plan trees (produced by `solo-testplan` / `duo-testplan`) against a generated no-external-ports docker-compose stack, with append-only `Bugs.md` + `Log.md` ledgers and a thin `Result.md`.

**Architecture:** One new skill at `skills/solo-runtestplan/SKILL.md`. Same plugin (`yd`), same Claude-only / explicit-`solo`-keyword discipline as `solo-testplan`. Companion rulebook `linked-testplan` is consumed unchanged. The plugin manifest (`.claude-plugin/plugin.json`) auto-discovers skills from `skills/*/SKILL.md`, so only version + description metadata need updating there. README.md / AGENTS.md / CLAUDE.md also need new-skill entries.

**Tech Stack:** Markdown (SKILL.md authoring), JSON (plugin manifest), no code. The skill itself, when later invoked, drives `docker compose` and subagent dispatches via the Claude harness — but this plan only authors the skill, not its runtime.

**Source of truth for content:** [docs/specs/2026-05-20-solo-runtestplan-design.md](../specs/2026-05-20-solo-runtestplan-design.md). Each task below references the spec section(s) it transcribes/adapts. Where exact wording matters (frontmatter, hard rules), the plan inlines it; for prose body sections, the plan describes shape and references the spec.

**File map:**

| Path | Action | Purpose |
|---|---|---|
| `skills/solo-runtestplan/SKILL.md` | Create | The skill itself. ~500 lines. |
| `.claude-plugin/plugin.json` | Modify | Bump version `0.6.1 → 0.7.0`; extend `description` to mention `solo-runtestplan`. |
| `README.md` | Modify | Add row to skill table; update "What you get" prose. |
| `AGENTS.md` | Modify | Add a paragraph under "Skills shipped" for `solo-runtestplan`. Update layout block. |
| `CLAUDE.md` | Modify | Add the same `solo-runtestplan` entry under "Skills shipped". |

No new test files (skills are not unit-tested in this repo — `solo-testplan` and `duo-testplan` were both merged without tests). Validation is structural (frontmatter parses, required sections present, trigger discipline phrases match the spec).

---

### Task 1: Create skill directory + author SKILL.md frontmatter

**Files:**
- Create: `skills/solo-runtestplan/SKILL.md`

**Spec reference:** § 0 Summary, § 3 Trigger and invocation, § 1 Scope and non-goals.

- [ ] **Step 1: Verify the target directory does not already exist**

Run: `ls skills/solo-runtestplan/ 2>&1`
Expected: `ls: skills/solo-runtestplan/: No such file or directory` (or platform equivalent).

- [ ] **Step 2: Create the directory and write SKILL.md with frontmatter + skill title + one-paragraph preamble**

Create `skills/solo-runtestplan/SKILL.md` with this exact content. The `description:` field is the trigger criteria the Claude Code skill loader uses — its wording is load-bearing.

```markdown
---
name: solo-runtestplan
description: Claude-only executor for e2e test plan trees authored by `solo-testplan` / `duo-testplan` (or any tree following the `linked-testplan` page shape). Aggregates one or more test plan trees, generates a no-external-ports docker-compose stack, brings it up, and runs every HAPPY/NEGATIVE scenario via CLI tools (curl, kcat, redis-cli, psql, mc, grpcurl, …) inside a single runner container on an internal network. Four phases — `plan-aggregate`, `compose-build`, `flow-execute`, `result`. Per-flow subagents translate scenarios to runner-exec'd commands, observe via the same runner, and append immutable entries to `Bugs.md` (failures with full repro) and `Log.md` (chronological event ledger). No INCONCLUSIVE state — observation gaps trigger autonomous recovery (subagent self-installs tools / restarts deps; main re-dispatches compose-build for structural fixes) until every scenario reaches PASS / FAIL / SKIPPED or the per-flow `recovery-budget` (default 5) is exhausted (which itself files an `observation-exhausted` bug). Strict sequential flow execution; scrub-between-attempts derived from external-dep tags. TRIGGERS ONLY on explicit "solo" keyword — `solo runtestplan X`, `solo-runtestplan X`, `/solo-runtestplan X`, `solo run testplan X`, `solo execute testplan X`. Does NOT auto-activate on plain `run tests`, `execute tests`, `e2e run`, or `test the system`.
---

# Solo Run-Test-Plan

Autonomous executor for e2e test plan trees. Given one or more inputs (slugs that resolve under `Solo/TestPlan-<slug>/` or `Duo/TestPlan-<slug>/`, or arbitrary paths to directories of `linked-testplan` pages), generate a no-external-ports docker-compose stack, bring it up, and run every scenario via CLI tools inside a single runner container. Maintain append-only `Bugs.md` and `Log.md` ledgers in-stream; write a thin `Result.md` at the end.

There is no INCONCLUSIVE outcome. Observation gaps drive autonomous recovery loops until each scenario reaches PASS / FAIL / SKIPPED, or until the per-flow recovery budget is exhausted (which itself produces a FAIL bug entry with `kind: observation-exhausted`).

The companion `linked-testplan` rulebook is consumed AS IS. It owns the page shape the executor parses. Do not modify it from this skill.
```

- [ ] **Step 3: Validate the frontmatter parses as YAML and the description holds the required trigger phrases**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
if (-not ($content -match '(?ms)^---\r?\n(.+?)\r?\n---')) { throw "frontmatter not found" }
$front = $Matches[1]
foreach ($needle in @('name: solo-runtestplan', 'solo runtestplan X', 'solo-runtestplan X', '/solo-runtestplan X', 'solo run testplan X', 'solo execute testplan X', 'TRIGGERS ONLY')) {
  if ($front -notlike "*$needle*") { throw "missing in description: $needle" }
}
"ok"
```

Expected output: `ok`.

- [ ] **Step 4: Stage and commit**

Run:

```sh
git add skills/solo-runtestplan/SKILL.md
git commit -m "solo-runtestplan: scaffold skill directory + frontmatter"
```

Expected: commit succeeds. Run `git status` afterwards — working tree clean.

---

### Task 2: Append "When Invoked" + "Plugin Layout" + "Mission Folder Layout"

**Files:**
- Modify: `skills/solo-runtestplan/SKILL.md` (append)

**Spec reference:** § 3 Trigger and invocation, § 5 Runtime requirements, § 7 Mission folder layout.

- [ ] **Step 1: Read the spec sections to be transcribed**

Read [docs/specs/2026-05-20-solo-runtestplan-design.md](../specs/2026-05-20-solo-runtestplan-design.md) sections § 3, § 5, § 7. These three sections become the next three SKILL.md sections.

- [ ] **Step 2: Append the three sections to SKILL.md**

Append after the preamble. Use the spec's prose nearly verbatim, adapting only to second-person skill voice. The three appended sections are:

**`## When Invoked`** — sub-headings `### Trigger`, `### Mode`, `### Modifiers`, `### Filter and Slug`. Content:

- Trigger: list the 5 trigger phrases (`solo runtestplan X`, `solo-runtestplan X`, `/solo-runtestplan X`, `solo run testplan X`, `solo execute testplan X`) and the explicit non-activation phrases (`run tests`, `execute tests`, `test the system`, `e2e run`).
- Mode: default (one inline-text clarifying question allowed if mission cannot start) vs autonomous (no questions; trigger phrases: `autonomously`, `no questions`, `hands-free`, `auto`, `unattended`).
- Modifiers table — **exactly** these three rows:
  - `keep-stack` (default) — leave stack up at end.
  - `teardown` — `docker compose down -v` at end.
  - `recovery-budget=N` (default 5) — max recovery cycles per flow and per compose-build.
- Filter and Slug: prose argument parsing per § 3 — slug resolution (`Solo/TestPlan-<slug>/` first, then `Duo/TestPlan-<slug>/`), path inputs as-is, comma/"and" lists, empty input halts. Slug mint: 2-5 PascalCase ending in `Run` (e.g., `PetclinicRun`). If user names an existing `Solo/RunTestPlan-<slug>/`, resume from `.solo-run/journal.jsonl`.

State explicitly: **web access is always allowed** for subagents (no modifier needed).

**`## Plugin Layout and Path Resolution`** — mirror solo-testplan's analogous section pattern. Resolve at activation:

- `PLUGIN_ROOT`: two directories above this skill directory.
- `RULEBOOK_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/SKILL.md`.
- `RULEBOOK_REFS_ABS`: `$PLUGIN_ROOT/skills/linked-testplan/references/`.

State: pass these absolute paths in every dispatched prompt. Verify they exist + are readable before the first subagent writes any artifact. Halt on broken install. (Unlike `solo-testplan`, this skill does NOT use `scripts/check-refs.py`; do not resolve it.)

Also list: `codex` is NOT required by this skill (Claude-only). `docker` and `docker compose` v2 must be on PATH; probe both at activation and halt with a clean error if absent.

**`## Mission Folder Layout`** — transcribe the directory tree from § 7 verbatim:

````
Solo/RunTestPlan-<slug>/
  Result.md                       thin end-of-mission summary
  Bugs.md                         append-only bug ledger
  Log.md                          append-only event ledger
  compose.yaml                    generated stack manifest
  compose.runner.Dockerfile       runner image build context
  .solo-run/
    journal.jsonl                 main-only coordinator journal
    run-manifest.json             aggregated plan input + flow catalog
    input-sources.json            resolved input trees (slugs/paths + roots)
    compose-build/
      Author-r00.md
      Refine-r01.md               optional, on re-dispatch
      Author-r01.md
    flow-execute/
      <tree-tag>__<flow-id>/
        attempts/
          attempt-r00.md
          attempt-r01.md
        recovery/
          repair-r01.md
        terminal.md
    result/
      coverage-matrix.json
````

State the constraints from § 7:
- Root contains only visible deliverables (five named files).
- `<tree-tag>` namespacing rules (slug input → tree-tag = slug; path input → PascalCased basename of parent of `test-plan/`, deduped `Foo` / `Foo2` / `Foo3`).
- Slash characters in repo names → `__`.
- Attempts are immutable and numbered; `repair-rNN.md` precedes `attempt-rNN.md`.

Then a unit-key table per § 7:

| Phase | Unit key |
|---|---|
| `plan-aggregate` | `plan-aggregate` |
| `compose-build` | `compose-build` |
| `flow-execute` (local flow) | `flow-execute/<tree-tag>__<flow-id>` |
| `flow-execute` (cross-app flow) | `flow-execute/<tree-tag>__crossapp__<cflow-id>` |
| `result` | `result` |

- [ ] **Step 3: Validate appended sections render and required strings appear**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
foreach ($s in @('## When Invoked', '## Plugin Layout and Path Resolution', '## Mission Folder Layout', 'PLUGIN_ROOT', 'RULEBOOK_ABS', 'RULEBOOK_REFS_ABS', 'recovery-budget=N', 'keep-stack', 'teardown', 'Solo/RunTestPlan-<slug>/', 'flow-execute/<tree-tag>__<flow-id>')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "missing section/string: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 4: Commit**

```sh
git add skills/solo-runtestplan/SKILL.md
git commit -m "solo-runtestplan: When Invoked + Plugin Layout + Mission Folder"
```

---

### Task 3: Append "Pipeline" + "plan-aggregate Phase" + "Compose-Build Phase"

**Files:**
- Modify: `skills/solo-runtestplan/SKILL.md` (append)

**Spec reference:** § 6 Pipeline, § 8 Plan-aggregate phase, § 9 Compose-build phase (subsections 9.1-9.5).

- [ ] **Step 1: Append the Pipeline section**

Append `## Pipeline`. Include:

- A 4-row table mapping phase → role → owner → cardinality, exactly as in § 6.
- A "Gates" subsection enumerating the 3 hard barriers verbatim from § 6.
- An explicit sentence: "No streaming handoffs (unlike `solo-testplan`): strict sequential flow execution means there is no upstream/downstream overlap opportunity."

- [ ] **Step 2: Append the plan-aggregate section**

Append `## plan-aggregate Phase`. Include:

- Main-only, sequential, one execution.
- Six numbered steps mirroring § 8 (resolve inputs → glob pages → parse linked-testplan shape → detect SKIPPED-eligible scenarios → aggregate external-dep tags → commit `run-manifest.json` + `input-sources.json` + `phase_complete`).
- Include the `run-manifest.json` shape sketch from § 8 as a fenced JSON block (verbatim).

- [ ] **Step 3: Append the compose-build section**

Append `## compose-build Phase` with subsections:

- `### Subagent inputs` — list from § 9.1.
- `### Subagent outputs` — list from § 9.2.
- `### Hard generation rules` — numbered list 1-6 verbatim from § 9.3. Be careful to copy each rule's text exactly; these are load-bearing for the compose-build subagent at runtime.
- `### Runner image` — bullets from § 9.4 covering base, tools-at-build-time mapping, long-running command, no host volume mounts.
- `### Main's bring-up loop` — numbered steps 1-6 from § 9.5 covering dispatch → validate → on-failure re-dispatch → on-pass build+up+health-wait → health-fail re-dispatch → budget exhaustion → mission halt.
- Terminal states (CLEAN / REPAIRED / BLOCKED) at the end.

For the hard generation rules, prefix each rule with `**` for the bold lead-in (e.g., `1. **No \`ports:\` mapping on any service.**`) to make them scannable.

- [ ] **Step 4: Validate appended content**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
foreach ($s in @('## Pipeline', '## plan-aggregate Phase', '## compose-build Phase', 'phase_complete', 'run-manifest.json', '### Subagent inputs', '### Subagent outputs', '### Hard generation rules', '### Runner image', "### Main's bring-up loop", 'No `ports:` mapping', 'runtestplan-net', 'CLEAN', 'REPAIRED', 'BLOCKED')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```sh
git add skills/solo-runtestplan/SKILL.md
git commit -m "solo-runtestplan: Pipeline + plan-aggregate + compose-build sections"
```

---

### Task 4: Append "flow-execute Phase" + per-flow subagent lifecycle

**Files:**
- Modify: `skills/solo-runtestplan/SKILL.md` (append)

**Spec reference:** § 10 Flow-execute phase (subsections 10.1-10.7).

- [ ] **Step 1: Append the flow-execute section header + ordering rule**

Append `## flow-execute Phase`. Open with the ordering rule from § 10: per-flow subagents dispatched strictly sequentially in `run-manifest.json` order (local flows grouped by `(tree-tag, repo, svc)` in document order, cross-app flows last).

- [ ] **Step 2: Append "Per-Flow Subagent Prompt"**

`### Per-Flow Subagent Prompt`. Bullet list of every field that must be in the dispatched prompt, per § 10.1. Include the runner exec template verbatim:

```
docker compose -f <mission>/compose.yaml exec -T runner sh -c '<cmd>'
```

End with the boundaries block (no sub-subagents; no edits to test plan/compose/Dockerfile; self-recovery in-stack only).

- [ ] **Step 3: Append "Self-Recovery Boundary"**

`### Self-Recovery Boundary`. Two bulleted lists — one for **subagent-fixable** actions (§ 10.2 list), one for **main-fixable only** (§ 10.2 list). Header each list as `**Subagent-fixable** (in-dispatch self-heal):` / `**Main-fixable only** (subagent escalates with bail):`.

- [ ] **Step 4: Append "Per-Attempt Control Flow"**

`### Per-Attempt Control Flow Inside the Subagent`. Five numbered steps from § 10.3 (Read context → Pre-flight requirements check → Scenario loop → Terminal → Return). For step 3 (scenario loop), include the four sub-bullets (set up preconditions, execute steps, observe expected, classify+log+bug).

State explicitly that the subagent **accumulates** bail errors and continues checking other requirements / scenarios — it does NOT return on first failure.

- [ ] **Step 5: Append "Subagent Return Shape"**

`### Subagent Return Shape`. Include the YAML schema from § 10.4 verbatim inside a fenced ```yaml block.

State below the schema: `PASS-all` / `mixed` / `FAIL-all` are terminal — main moves to scrub + next flow. `bailed` triggers main's recovery cycle.

- [ ] **Step 6: Append "Soft Self-Recovery Budgets"**

`### Soft Self-Recovery Budgets Inside the Subagent`. List from § 10.5:

- Tool install: 2 attempts per tool.
- Service restart + wait-health: 3 cycles of `restart → 5×3s healthcheck poll`.
- Topic / schema / key reset: 2 attempts.

Note: defaults; overridable in the prompt by main. If a single requirement hits its local budget, accumulate and move on — do not retry that requirement again within the same attempt.

- [ ] **Step 7: Append "Re-Dispatch Contract"**

`### Re-Dispatch Contract`. Fresh-context per attempt. New attempt reads every prior `attempt-r*.md` + `repair-r*.md`. Scrub before every attempt (first dispatch and every re-dispatch). Every scenario re-runs from scratch.

- [ ] **Step 8: Append "Cross-App Flow Execution"**

`### Cross-App Flow Execution`. Per § 10.7: same per-flow subagent shape; differences are (1) multiple services named as actors, (2) Steps prefixed `<service> → <service>:`, (3) typical commands are inter-service `curl` or back-to-back kafka producer/consumer pairs. No special phase or unit kind.

- [ ] **Step 9: Validate appended content**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
foreach ($s in @('## flow-execute Phase', '### Per-Flow Subagent Prompt', '### Self-Recovery Boundary', '### Per-Attempt Control Flow', '### Subagent Return Shape', '### Soft Self-Recovery Budgets', '### Re-Dispatch Contract', '### Cross-App Flow Execution', 'bail_errors', 'PASS-all', 'mixed', 'FAIL-all', 'bailed', 'docker compose -f <mission>/compose.yaml exec -T runner')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 10: Commit**

```sh
git add skills/solo-runtestplan/SKILL.md
git commit -m "solo-runtestplan: flow-execute phase + per-flow subagent lifecycle"
```

---

### Task 5: Append "Recovery Cycle" + "Scrub" sections

**Files:**
- Modify: `skills/solo-runtestplan/SKILL.md` (append)

**Spec reference:** § 11 Recovery cycle (main-side), § 12 Scrub between flow attempts.

- [ ] **Step 1: Append the recovery section**

Append `## Recovery Cycle (Main-Side)`. Subsections:

- `### Cycle Steps` — numbered list 1-7 from § 11.1 (Read & classify → Plan repair actions → Execute targeted runtime fixes → Dispatch compose-build for structural fixes → Write repair-rNN.md → Append recovery events → Re-dispatch).
- Include the bail-kind → main-action table from § 11.1 verbatim.
- `### Budget Accounting` — content of § 11.2.
- `### Budget Exhaustion Semantics` — content of § 11.3, including the rule that `observation-exhausted` bugs are filed AND the mission continues; only `compose-build-exhausted` halts the mission.
- `### Stack-Recycle Caveat` — content of § 11.4.

Explicitly state: **main does not edit `compose.yaml` or `compose.runner.Dockerfile` directly**; structural fixes go through a compose-build subagent re-dispatch.

- [ ] **Step 2: Append the scrub section**

Append `## Scrub Between Flow Attempts`. Content:

- One-line definition: "Scrub = the cleanup pass that resets shared deps to a clean baseline. Runs before every flow attempt (first dispatch and every re-dispatch)."
- `### Per-Tag Scrub Actions` — the table from § 12.1 verbatim (tag kind → scrub action).
- `### Scrub Execution` — § 12.2 content: runs inside the runner; main composes script from tag set; appends `scrub-started` / `scrub-completed` to Log.md.
- `### Scrub Failure` — § 12.3 content: treat as infra-suspect for the upcoming flow's first attempt; consumes that flow's `recovery-budget`.

- [ ] **Step 3: Validate appended content**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
foreach ($s in @('## Recovery Cycle (Main-Side)', '### Cycle Steps', '### Budget Accounting', '### Budget Exhaustion Semantics', '### Stack-Recycle Caveat', '## Scrub Between Flow Attempts', '### Per-Tag Scrub Actions', '### Scrub Execution', '### Scrub Failure', 'observation-exhausted', 'compose-build-exhausted', 'scrub-started', 'scrub-completed')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 4: Commit**

```sh
git add skills/solo-runtestplan/SKILL.md
git commit -m "solo-runtestplan: recovery cycle (main-side) + scrub"
```

---

### Task 6: Append "Ledger and Report Formats" + "Journal Events" + "Resumability"

**Files:**
- Modify: `skills/solo-runtestplan/SKILL.md` (append)

**Spec reference:** § 14 Ledger and report formats, § 16 Journal events + Resumability.

- [ ] **Step 1: Append the Bugs.md format section**

Append `## Ledger and Report Formats`, then `### Bugs.md`. Include:

- One-paragraph statement: append-only, written by per-flow subagents (`assertion-contradicted`) and main (`observation-exhausted`).
- The header template from § 14.1, inside a triple-backtick fence.
- The per-entry block template from § 14.1, inside a **four-backtick** fence (because the template contains nested triple-backtick fences for Repro / Evidence). The outer fence opens with `` ```` `` followed by `markdown`; inner sh/text fences use `` ``` ``. Match § 14.1 exactly.
- Numbering rule: 3-digit zero-padded; assigned by counting existing `## Bug ` headings before append. Duplicates across re-dispatches each append a fresh entry.

- [ ] **Step 2: Append the Log.md format section**

`### Log.md`. Include:

- One-paragraph statement: append-only event ledger written by both main and subagents.
- The header template from § 14.2 (triple-backtick fence).
- The per-event block template from § 14.2 (**four-backtick** outer fence).
- The full event-kind table from § 14.2 verbatim (10+ rows).

- [ ] **Step 3: Append the Result.md format section**

`### Result.md`. Include:

- One-paragraph statement: single-write end-of-mission summary, ~200-400 lines max.
- The Result.md template from § 14.3 in a triple-backtick `markdown` fence (Summary / Pointers / Coverage Matrix / Recovery-Exhausted Flows / Caveats / Unresolved).

- [ ] **Step 4: Append the "Append Safety" subsection**

`### Append Safety`. § 14.4 content: strict sequential per-flow execution means at most one subagent appends at a time; main appends between dispatches; each block is a single atomic file append terminated with `\n---\n`; no file locking at v1.

- [ ] **Step 5: Append the Journal Events section**

Append `## Journal Events (.solo-run/journal.jsonl)`. Main-only writes. Include the journal events table from § 16 verbatim (11 rows: `phase_start`, `subagent_spawn`, `artifact_accepted`, `artifact_rejected`, `attempt_complete`, `recovery_cycle`, `flow_terminal`, `stack_up` / `stack_healthy` / `stack_recycle`, `compose_build_redispatch`, `phase_complete`, `mission_halted`).

- [ ] **Step 6: Append the Resumability section**

`### Resumability`. On harness restart with the same slug, main reads journal tail and resumes per the three rules in § 16's resumability subsection.

- [ ] **Step 7: Validate appended content**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
foreach ($s in @('## Ledger and Report Formats', '### Bugs.md', '### Log.md', '### Result.md', '### Append Safety', '## Journal Events', '### Resumability', 'assertion-contradicted', 'observation-exhausted', 'subagent_spawn', 'attempt_complete', 'recovery_cycle', 'flow_terminal', 'stack_recycle', 'mission_halted')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 8: Commit**

```sh
git add skills/solo-runtestplan/SKILL.md
git commit -m "solo-runtestplan: ledger and report formats + journal events"
```

---

### Task 7: Append "Outcome Model" + "Failure Modes" + "Hard Rules" + "result Phase"

**Files:**
- Modify: `skills/solo-runtestplan/SKILL.md` (append)

**Spec reference:** § 13 Result phase, § 15 Outcome model, § 17 Failure modes, § 18 Hard rules.

- [ ] **Step 1: Append the result phase section**

Append `## result Phase`. § 13 content:

- Sequential final phase. Only hard barrier in normal operation: all `flow-execute` units terminal.
- Main writes `Result.md` per § 14.3 template + `.solo-run/result/coverage-matrix.json`.
- No `result-sanity` subagent.
- If `teardown` modifier: `docker compose -f <mission>/compose.yaml down -v` after Result.md is written.

- [ ] **Step 2: Append the outcome model section**

Append `## Outcome Model`. Include the two tables from § 15:

- Per-scenario terminal set: PASS / FAIL / SKIPPED / SKIPPED-BY-BAIL.
- Per-flow terminal set: PASS-all / mixed / FAIL-all / budget-exhausted.

Explicitly: **No INCONCLUSIVE.** State the line verbatim: "Observation gaps drive recovery loops to PASS / FAIL or to `kind: observation-exhausted` (recorded as FAIL with full attempt log)."

- [ ] **Step 3: Append the failure modes section**

Append `## Failure Modes`. Include the failure mode table from § 17 verbatim (12 rows).

- [ ] **Step 4: Append the hard rules section**

Append `## Hard Rules`. Bulleted list, exactly these 15 items in this order (matches § 18 + spec § 1 non-goals):

```
- **No Codex.** No `codex` invocation, no `.codex/` directory, no codex-specific flags.
- **Trigger only on explicit `solo` keyword.** Same discipline as `solo-testplan`.
- **No external ports.** Generated `compose.yaml` must not declare `ports:` on any service. Main validates after every compose-build output.
- **Single runner.** All CLI execution flows through `docker compose exec -T runner sh -c '…'`.
- **Main is a thin coordinator + stack operator.** Main runs `docker compose` commands, owns the journal/manifest/ledger headers/Result.md/coverage-matrix.json, runs scrub, and drives recovery. Main does NOT author content for compose.yaml, the runner Dockerfile, scenario translations, or bug entries.
- **`compose.yaml` and `compose.runner.Dockerfile` are authored only by the compose-build subagent.** Main edits neither directly.
- **No INCONCLUSIVE state.** Every scenario terminates PASS / FAIL / SKIPPED / SKIPPED-BY-BAIL.
- **Append-only ledgers.** Bugs.md and Log.md are immutable after each append. Re-dispatches append new entries; they never edit prior ones.
- **Per-flow subagents are short-lived, fresh-context.** Each attempt is a separate dispatch. No nested subagents.
- **Subagents read only what's in their prompt + their own unit subfolder + the linked-testplan rulebook + source within declared scope.** Subagents write only inside their own unit subfolder + via append to Bugs.md and Log.md.
- **Web always allowed.**
- **Strict sequential flows.** No parallel flow execution in v1.
- **Scrub before every flow attempt** (first dispatch and every re-dispatch).
- **Recovery budgets are bounded.** `recovery-budget=N` (default 5).
- **No polling.** Main waits for harness completion notifications between subagent dispatches.
```

- [ ] **Step 5: Validate appended content**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
foreach ($s in @('## result Phase', '## Outcome Model', '## Failure Modes', '## Hard Rules', 'SKIPPED-BY-BAIL', 'budget-exhausted', 'No Codex', 'No INCONCLUSIVE state', 'No polling')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 6: Final SKILL.md sanity check — frontmatter YAML still parses + section order is logical**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
# Frontmatter check
if (-not ($content -match '(?ms)^---\r?\n(.+?)\r?\n---')) { throw "frontmatter broken" }
# Section count check — expect at least 12 ## sections
$sectionCount = ([regex]::Matches($content, '(?m)^## ')).Count
if ($sectionCount -lt 12) { throw "only $sectionCount sections found, expected >= 12" }
# Line count sanity — SKILL.md should be in the 400-700 line range similar to solo-testplan
$lines = ($content -split "`n").Count
if ($lines -lt 300) { throw "skill is too short ($lines lines), spec likely incompletely transcribed" }
"ok, sections=$sectionCount, lines=$lines"
```

Expected output: something like `ok, sections=14, lines=520`.

- [ ] **Step 7: Commit**

```sh
git add skills/solo-runtestplan/SKILL.md
git commit -m "solo-runtestplan: result phase + outcome model + failure modes + hard rules"
```

---

### Task 8: Register the skill in plugin manifest + docs

**Files:**
- Modify: `.claude-plugin/plugin.json` (version + description)
- Modify: `README.md` (skill table row + intro prose)
- Modify: `AGENTS.md` (skills shipped + repo layout)
- Modify: `CLAUDE.md` (skills shipped)

The plugin manifest auto-discovers skills from `skills/*/SKILL.md`, so no explicit registration of the new SKILL.md path is required. Version bump and description updates only.

- [ ] **Step 1: Bump plugin.json version + description**

Read current `.claude-plugin/plugin.json`. Update two fields:

- `version`: `"0.6.1"` → `"0.7.0"` (minor bump per existing convention — new skill = minor).
- `description`: replace the current description with text that mentions `solo-runtestplan` alongside the existing skills.

New description string (single line, JSON-escaped):

```
"description": "Duo skills: symmetric Claude+Codex convergence (design, discuss, forge, prod-ready, research, review, testplan). Solo skills (Claude-only, explicit `solo` keyword): solo-testplan authors an e2e test plan tree; solo-runtestplan executes one or more test plan trees against a generated no-external-ports docker stack with append-only Bugs.md / Log.md ledgers. linked-testplan is the shared rulebook for both testplan skills. scripts/check-refs.py validates flow-page references for solo-testplan / duo-testplan."
```

- [ ] **Step 2: Validate plugin.json is still valid JSON**

Run (PowerShell):

```powershell
$json = Get-Content -Raw .claude-plugin/plugin.json | ConvertFrom-Json
if ($json.version -ne '0.7.0') { throw "version not 0.7.0: $($json.version)" }
if ($json.description -notmatch 'solo-runtestplan') { throw "description missing solo-runtestplan" }
"ok"
```

Expected: `ok`.

- [ ] **Step 3: Update README.md — add table row + update intro paragraph**

Find the skills table (lines around 9-19 of README.md). Add a new row AFTER the `solo-testplan` row (so the row order is duo* → solo-testplan → solo-runtestplan → linked-testplan):

```markdown
| `solo-runtestplan` | solo (Claude-only) | `Solo/RunTestPlan-<slug>/` containing `Result.md`, `Bugs.md`, `Log.md`, `compose.yaml`, `compose.runner.Dockerfile`. Four phases (plan-aggregate, compose-build, flow-execute, result). Executes test plan trees produced by `solo-testplan` / `duo-testplan` against a generated no-external-ports docker stack; append-only Bugs and Log ledgers; autonomous infra+observation recovery; strict sequential per-flow execution. | no (modifies the running stack only) |
```

Then update the intro paragraph (line ~7) from "Seven duo skills … one Claude-only solo skill …" to "Seven duo skills … TWO Claude-only solo skills (solo-testplan authors test plans; solo-runtestplan executes them) …" — match the existing sentence style.

Also extend the trigger-summary paragraph (line ~21) to include the new skill's trigger phrases:

> `solo-testplan` triggers only on the explicit `solo` keyword (`solo testplan X`, `/solo-testplan X`). `solo-runtestplan` likewise triggers only on the explicit `solo` keyword (`solo runtestplan X`, `solo run testplan X`, `solo execute testplan X`, `/solo-runtestplan X`).

Also update the Requirements bullet (line ~25):

> `codex` CLI on PATH for every duo skill. `solo-testplan` and `solo-runtestplan` do NOT need `codex` — both are Claude-only. `solo-runtestplan` additionally requires `docker` and `docker compose` v2 on PATH.

- [ ] **Step 4: Validate README.md edits**

Run (PowerShell):

```powershell
$content = Get-Content -Raw README.md
foreach ($s in @('| `solo-runtestplan` |', 'solo runtestplan X', 'solo run testplan X', 'docker compose` v2 on PATH')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "README missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 5: Update AGENTS.md — add the solo-runtestplan paragraph + extend layout block**

In AGENTS.md, find the "Solo skill" section (currently single-skill, around lines 19-21). Update the header to "Solo skills" (plural) and add a NEW bullet immediately after the `solo-testplan` bullet:

```markdown
- `solo-runtestplan` - Claude-only executor for e2e test plan trees (the artifact shape produced by `solo-testplan` / `duo-testplan`). Aggregates one or more test plan trees, generates a no-external-ports `compose.yaml` + runner Dockerfile, brings the stack up, and runs every HAPPY/NEGATIVE scenario via CLI tools (curl, kcat, redis-cli, psql, mc, grpcurl, …) inside a single runner container on an internal network. Four phases (plan-aggregate, compose-build, flow-execute, result). Append-only `Bugs.md` (failures with full repro) and `Log.md` (chronological event ledger) maintained in-stream by per-flow subagents and main; thin `Result.md` written once at end. No INCONCLUSIVE state — observation gaps drive autonomous recovery (subagent self-installs tools / restarts deps; main re-dispatches compose-build for structural fixes) until every scenario reaches PASS / FAIL / SKIPPED or the per-flow `recovery-budget` (default 5) is exhausted (which itself files an `observation-exhausted` bug). Strict sequential flow execution. Scrub-before-every-attempt derived from external-dep tags. Outputs `Solo/RunTestPlan-<slug>/` with the five visible deliverables at the root. Triggers only on `solo runtestplan X`, `solo-runtestplan X`, `/solo-runtestplan X`, `solo run testplan X`, or `solo execute testplan X`.
```

Update the Runtime requirements section (around lines 27-31):

- Add a bullet: `solo-runtestplan` does NOT require `codex` (Claude-only) but DOES require `docker` and `docker compose` v2 on PATH.
- Update the existing line about web search: `solo-runtestplan` has web search always enabled (no modifier).

Update the Repo layout block (around lines 33-65) to insert `solo-runtestplan/SKILL.md` after `solo-testplan/SKILL.md`:

```
    solo-runtestplan/SKILL.md
```

- [ ] **Step 6: Validate AGENTS.md edits**

Run (PowerShell):

```powershell
$content = Get-Content -Raw AGENTS.md
foreach ($s in @('- `solo-runtestplan` -', 'Solo skills', 'solo-runtestplan/SKILL.md')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "AGENTS missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 7: Update CLAUDE.md to mirror AGENTS.md skill listing**

CLAUDE.md currently mirrors AGENTS.md for Claude Code harness. Open CLAUDE.md. Find the existing "Skills shipped" / solo-skill block and add a parallel `solo-runtestplan` entry, mirroring the AGENTS.md paragraph from Step 5 (same content, same wording).

Also extend the Runtime requirements section to mention docker prerequisite for `solo-runtestplan`.

- [ ] **Step 8: Validate CLAUDE.md edits**

Run (PowerShell):

```powershell
$content = Get-Content -Raw CLAUDE.md
foreach ($s in @('solo-runtestplan', 'docker compose')) {
  if ($content -notmatch [regex]::Escape($s)) { throw "CLAUDE.md missing: $s" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 9: Commit**

```sh
git add .claude-plugin/plugin.json README.md AGENTS.md CLAUDE.md
git commit -m "yd-skills 0.7.0: register solo-runtestplan in manifest, README, AGENTS, CLAUDE"
```

---

### Task 9: End-to-end structural validation pass

**Files:** none (read-only validation).

**Spec reference:** all sections (cross-cutting).

This task confirms the authored SKILL.md is structurally sound and free of common authoring errors. No code is written. If a check fails, return to the appropriate earlier task to fix.

- [ ] **Step 1: Verify frontmatter is well-formed and complete**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
if (-not ($content -match '(?ms)^---\r?\n(.+?)\r?\n---')) { throw "no frontmatter" }
$front = $Matches[1]
foreach ($field in @('name:', 'description:')) {
  if ($front -notmatch [regex]::Escape($field)) { throw "missing field: $field" }
}
# Ensure name matches directory
if ($front -notmatch 'name:\s*solo-runtestplan\b') { throw "name field wrong" }
"ok"
```

Expected: `ok`.

- [ ] **Step 2: Verify all required top-level sections are present in order**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
$required = @(
  '## When Invoked',
  '## Plugin Layout and Path Resolution',
  '## Mission Folder Layout',
  '## Pipeline',
  '## plan-aggregate Phase',
  '## compose-build Phase',
  '## flow-execute Phase',
  '## Recovery Cycle (Main-Side)',
  '## Scrub Between Flow Attempts',
  '## Ledger and Report Formats',
  '## Journal Events',
  '## result Phase',
  '## Outcome Model',
  '## Failure Modes',
  '## Hard Rules'
)
$lastIdx = -1
foreach ($s in $required) {
  $idx = $content.IndexOf($s)
  if ($idx -lt 0) { throw "missing section: $s" }
  if ($idx -lt $lastIdx) { throw "section out of order: $s" }
  $lastIdx = $idx
}
"ok, all $($required.Count) sections present in order"
```

Expected output: `ok, all 15 sections present in order`.

- [ ] **Step 3: Verify trigger discipline strings are present in the description**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
$desc = ($content -split '---', 3)[1]
$mustHave = @('solo runtestplan X', 'solo-runtestplan X', '/solo-runtestplan X', 'TRIGGERS ONLY', 'Does NOT auto-activate')
foreach ($s in $mustHave) {
  if ($desc -notmatch [regex]::Escape($s)) { throw "description missing: $s" }
}
# Description must NOT list `web-allowed` as a modifier — this skill always allows web.
if ($desc -match '`web-allowed`') { throw "description must not list ``web-allowed`` as a modifier" }
"ok"
```

Expected: `ok`.

- [ ] **Step 4: Verify the skill carries the right negation patterns and does not accidentally invoke forbidden tools**

The skill body legitimately *references* `codex` (in the "No Codex" hard rule and the "codex is NOT required" line under Plugin Layout) and `INCONCLUSIVE` (in the "No INCONCLUSIVE state" hard rule and Outcome Model). What it must NOT do is invoke codex or list `web-allowed` as a modifier.

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md

# Negation patterns MUST appear (positive affirmation of hard rules).
foreach ($needle in @('No Codex', 'No INCONCLUSIVE')) {
  if ($content -notmatch [regex]::Escape($needle)) { throw "missing negation pattern: $needle" }
}

# Forbidden invocation / configuration patterns MUST NOT appear.
$forbidden = @(
  'web-allowed',                              # this skill always allows web; no modifier
  '`gpt-5.5`',                                # codex-specific model pin
  '--dangerously-bypass-approvals-and-sandbox', # codex-specific flag
  'model_reasoning_effort',                   # codex-specific config
  '\.codex/'                                  # codex directory
)
foreach ($p in $forbidden) {
  if ($content -match $p) { throw "skill must not contain: $p" }
}

# Codex invocation pattern: `codex` as a shell command (not in prose).
# Heuristic: look for `codex ` (codex followed by space) inside fenced code blocks.
$inFence = $false
$fenceLine = 0
$lineNum = 0
foreach ($line in ($content -split "`n")) {
  $lineNum++
  if ($line -match '^```') {
    $inFence = -not $inFence
    $fenceLine = $lineNum
    continue
  }
  if ($inFence -and $line -match '(?:^|\s)codex\s') {
    throw "codex command invocation found inside fenced block at line $lineNum"
  }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 5: Verify all hard rules from the spec are reflected**

Run (PowerShell):

```powershell
$content = Get-Content -Raw skills/solo-runtestplan/SKILL.md
$hardRules = @(
  'No Codex',
  'Trigger only on explicit `solo` keyword',
  'No external ports',
  'Single runner',
  'thin coordinator',
  'authored only by the compose-build subagent',
  'No INCONCLUSIVE state',
  'Append-only ledgers',
  'short-lived, fresh-context',
  'Web always allowed',
  'Strict sequential flows',
  'Scrub before every flow attempt',
  'Recovery budgets are bounded',
  'No polling'
)
foreach ($r in $hardRules) {
  if ($content -notmatch [regex]::Escape($r)) { throw "hard rule missing: $r" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 6: Verify plugin.json + docs are consistent**

Run (PowerShell):

```powershell
$plugin = Get-Content -Raw .claude-plugin/plugin.json | ConvertFrom-Json
if ($plugin.version -ne '0.7.0') { throw "plugin version $($plugin.version) != 0.7.0" }
foreach ($file in @('README.md', 'AGENTS.md', 'CLAUDE.md')) {
  $c = Get-Content -Raw $file
  if ($c -notmatch 'solo-runtestplan') { throw "$file missing solo-runtestplan reference" }
}
"ok"
```

Expected: `ok`.

- [ ] **Step 7: Final summary**

Run:

```sh
git log --oneline -10
git status
```

Expected: 8 new commits on top of `f5ab836` (the prior HEAD), in this order:

```
solo-runtestplan: scaffold skill directory + frontmatter
solo-runtestplan: When Invoked + Plugin Layout + Mission Folder
solo-runtestplan: Pipeline + plan-aggregate + compose-build sections
solo-runtestplan: flow-execute phase + per-flow subagent lifecycle
solo-runtestplan: recovery cycle (main-side) + scrub
solo-runtestplan: ledger and report formats + journal events
solo-runtestplan: result phase + outcome model + failure modes + hard rules
yd-skills 0.7.0: register solo-runtestplan in manifest, README, AGENTS, CLAUDE
```

`git status` should report a clean working tree. No untracked files under `skills/solo-runtestplan/`.

This completes the implementation. No further tasks. The skill is now installed when the plugin is loaded. Functional smoke-testing (running `solo runtestplan <some-tree>` against a real test plan + docker stack) is out of scope for this plan — that's a runtime concern, not an authoring concern.
