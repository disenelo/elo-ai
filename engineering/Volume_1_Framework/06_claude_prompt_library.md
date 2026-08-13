# Volume 1 — Claude Prompt Library

These are the actual prompts. Copy, fill in `[BRACKETS]`, paste.

Every prompt begins with a role assignment and context brief. Every prompt ends with a specific deliverable. Claude is never asked to "do its best" — it is given exact output requirements.

---

## PROMPT 01 — Architecture Review

```
You are a Senior Architect reviewing Phase [N] of eLo OS before any implementation begins.

CONTEXT:
eLo OS is a persistent AI desktop companion with a strict architectural constant: One Brain, One Executive. The Executive Faculty (runtime/executive.py) is the only decision-maker. Every other faculty observes and contributes information. The Executive is permanently frozen — it must never be modified.

FREEZE_V1_LOCK: runtime/executive.py and prompts/ are permanently frozen.

YOUR TASK:
Review the Phase [N] design documents and the current codebase. Produce an Architecture Review Report — no code, no implementation decisions.

The report must cover:

1. PHASE OBJECTIVE
   What cognitive capability does this phase add? One paragraph.

2. ARCHITECTURE CONSTANTS CHECK
   For each of the six constants, state explicitly: COMPLIANT / VIOLATION / RISK
   - One Brain: does this phase add a second decision-maker?
   - One Executive: does this phase modify runtime/executive.py?
   - Faculties Observe: do new components produce observations, not decisions?
   - FREEZE_V1_LOCK: are frozen components untouched?
   - Silence is Valid: can every new component produce nothing?
   - Evidence Gates: has the prior phase passed validation?

3. EXISTING SYSTEM IMPACT
   Which existing files and components does this phase touch?
   What could break?

4. RISKS
   At least one risk must be identified. "No risks" is not an acceptable finding.

5. RECOMMENDATION
   PROCEED / REVISE / REJECT — with specific reasoning.

READ FIRST:
- engineering/README.md
- engineering/Volume_1_Framework/01_engineering_philosophy.md
- The prior phase's 11_handover.md
- [List any other specific files relevant to Phase N]

OUTPUT FORMAT: Markdown report. Headers as above. Cite specific files.
```

---

## PROMPT 02 — Current State Audit

```
You are a Diagnostics Engineer auditing the current state of eLo OS before Phase [N] implementation.

CONTEXT:
eLo OS is a persistent AI desktop companion. Phase [N] is [NAME]. You are not implementing anything — you are documenting the current state with complete honesty.

YOUR TASK:
Audit every file relevant to Phase [N]. Produce a Current State Audit table.

For each component, record:
- File path
- What it does
- Status: ✅ verified working / ⚠️ exists but untested / 🔴 broken or stub
- What evidence you have for the status (ran it, read it, inferred it)

HONESTY RULE:
If you did not run it, it cannot be ✅. If it exists but you only read it, it is ⚠️. If it's a stub or broken, it is 🔴. Do not mark ✅ for something you only read.

ALSO AUDIT:
- Test coverage: which components have unit tests?
- Documentation: which components have architecture docs?
- Integration: which components are wired into server.py / main.py vs. imported but unused?

READ FIRST:
- engineering/Phase_[N]_[Name]/01_review.md (if exists)
- All files relevant to Phase [N]
- tests/ directory

OUTPUT FORMAT: Markdown table. One row per component. Findings section at the end for anything notable.
```

---

## PROMPT 03 — Gap Analysis

```
You are a Systems Analyst identifying gaps before Phase [N] implementation.

CONTEXT:
Phase [N] is [NAME]. The objective is [OBJECTIVE]. The prior phase has been audited (see Current State Audit).

YOUR TASK:
Identify every gap between the current state and the Phase [N] objective.

For each gap, state:
1. WHAT IS MISSING — specific, not general ("_to_concepts() reads keyword dict; Phase 3 needs graph traversal" not "better NLU needed")
2. RESOLUTION — one of:
   - Deliverable in Phase [N] Step 05
   - Dependency on Phase [later] (name it)
   - Known limitation (out of scope)
   - Risk requiring mitigation (state the mitigation)
3. FROZEN COMPONENT IMPACT — if the gap touches runtime/executive.py or prompts/, flag it immediately

ALSO IDENTIFY:
- What Phase [N] must NOT change (frozen interfaces, established contracts)
- Dependencies on external systems (APIs, hardware, runtime conditions)

OUTPUT FORMAT: Markdown. One section per gap. Numbered. Summary table at the end.
```

---

## PROMPT 04 — Runtime Design

```
You are a Runtime Architect designing the exact data flow for Phase [N] of eLo OS.

CONTEXT:
Phase [N] is [NAME]. The gaps have been analysed. You are designing how data flows — not implementing it.

YOUR TASK:
Produce a Runtime Design document covering:

1. DATA FLOW
   ASCII diagram or step-by-step description of the complete data path.
   Start from inputs (user speech, stream observation, sensor data, etc.)
   End at the Executive's g_ctx.
   Name every intermediate object and its type.

2. INTERFACES
   For every new function or class, state:
   - Signature (name, parameters with types, return type)
   - What it consumes
   - What it produces
   - What it does when it fails (specific error behaviour, not "handle gracefully")

3. THREAD SAFETY
   Which components run in threads?
   What state do they share?
   What protects that state (lock, queue, atomic)?

4. PERFORMANCE CHARACTERISTICS
   Frequency (how often does this run?)
   Latency (how long should it take?)
   Resource cost (CPU, memory, API calls)

5. CONSTRAINTS
   What must remain unchanged from prior phases?
   What can the next phase change without breaking this phase?

OUTPUT FORMAT: Markdown. Sections as above. No implementation — design only.
```

---

## PROMPT 05 — Implementation

```
You are an Implementation Engineer building Phase [N] of eLo OS.

CONTEXT:
Phase [N] is [NAME]. The Runtime Design is complete (see 04_runtime_design.md). You are implementing exactly what the Runtime Design specifies — no more, no less.

RULES (no exceptions):
1. Implement only what the Runtime Design specifies
2. Do not refactor prior phases unless the Gap Analysis explicitly requires it
3. Do not modify runtime/executive.py or prompts/ — FREEZE_V1_LOCK
4. Every new function has a single, testable responsibility
5. No fallback behaviour unless the Gap Analysis specifies it — empty = nothing happens

BEFORE WRITING ANY CODE:
Read the Runtime Design (04_runtime_design.md) completely.
Read the prior phase handover (prior phase 11_handover.md) for what must not break.
Read the relevant existing files to understand what already exists.

IMPLEMENTATION ORDER:
1. Data classes and types first
2. Core logic functions
3. Integration with existing systems (g_ctx injection, server.py wiring)
4. Configuration (env vars, config files)

After implementation, state explicitly:
- What was built (file → function → what it does)
- What was NOT built (gaps deferred to later phases)
- Any deviations from the Runtime Design and why
```

---

## PROMPT 06 — Unit Tests

```
You are a Test Engineer writing unit tests for Phase [N] of eLo OS.

CONTEXT:
Phase [N] is [NAME]. The implementation is complete. You are writing tests for individual components in isolation.

RULES:
- Tests must run without starting the server
- Tests must run without connecting to external APIs
- Tests must not depend on blender_state.json existing on disk
- Each test has one clear assertion

FOR EACH NEW COMPONENT, WRITE TESTS FOR:
1. Happy path — expected input → expected output
2. Edge cases listed in the Runtime Design
3. Error paths — what happens when input is invalid or a dependency fails
4. Boundary conditions — empty sets, None values, zero counts

TEST STRUCTURE:
Each test: setup → action → assertion → teardown (if needed)

OUTPUT: Working Python test code. Compatible with the existing tests/ directory structure.
Run them. Report pass/fail.
```

---

## PROMPT 07 — Conversation Tests

```
You are a Conversation Validator. Your job is to talk to eLo and break eLo.

CONTEXT:
Phase [N] is [NAME]. eLo OS is running (python server.py). You are testing whether eLo's conversational behaviour matches what Phase [N] specified.

FOR EACH TEST SCENARIO:
1. State the scenario (what context exists, what David says)
2. State what eLo SHOULD do (specific expected behaviour)
3. Run the test — talk to eLo
4. Record what eLo ACTUALLY did (quote the response)
5. Judge: PASS / FAIL / UNEXPECTED (unexpected is not a pass)

TEST CATEGORIES FOR PHASE [N]:
[Phase-specific scenarios go here — see each phase's 07_conversation_tests.md]

SILENCE TEST:
Send a message that should NOT trigger Phase [N] behaviour.
Confirm eLo does not exhibit Phase [N] behaviour.
An unexpected observation/response is a FAIL.

REGRESSION TEST:
Use conversation scenarios from prior frozen phases.
Confirm they still work correctly.

OUTPUT: Test results table. Actual eLo responses quoted. Pass/fail for each.
```

---

## PROMPT 08 — Stress Tests

```
You are a Stress Test Engineer running endurance and edge-case tests on eLo OS after Phase [N] implementation.

CONTEXT:
Phase [N] is [NAME]. eLo OS is running. You are testing system stability under pressure.

STANDARD STRESS SCENARIOS (run all):

1. LONG SESSION — run eLo for 2 hours with real work (coding, designing, writing).
   Observe: memory stable? CPU stable? Any crashes? Any runaway loops?
   Record: attention patterns over time, any unexpected escalation

2. RAPID SWITCHING — switch the frontmost app every 30 seconds for 15 minutes.
   Observe: do vision stream tokens change correctly? Any lag? Any stale state?

3. API FAILURE INJECTION — disable the primary LLM backend mid-session.
   Observe: does eLo fall back gracefully? Does it recover when the backend returns?

4. EMPTY STREAMS — configure all streams to return empty sets.
   Observe: does the Connection Surface produce nothing? No errors?

5. CONCURRENT STREAMS — trigger multiple stream updates simultaneously.
   Observe: thread safety holds? No race conditions?

[Phase-specific scenarios go here — see each phase's 08_stress_tests.md]

OUTPUT: Findings report. What held. What degraded. What failed. Memory/CPU readings if available.
```

---

## PROMPT 09 — Regression

```
You are a Regression Engineer. Your job is to confirm that Phase [N] has not broken anything that worked before.

CONTEXT:
Phase [N] is [NAME]. You have the complete test suites for all prior frozen phases.

YOUR TASK:
Run every test from prior frozen phases against the current eLo OS state.

FOR EACH PRIOR PHASE TEST:
1. Run the test
2. Record the result: PASS / FAIL / DEGRADED
3. If FAIL or DEGRADED: identify the specific component that changed and caused the regression

REGRESSION BLOCKS FREEZE.
If any prior phase test fails, the freeze is blocked. The regression must be resolved before re-attempting.

OUTPUT: Regression report table. One row per prior phase test. Pass/fail. Any failures with root cause.
```

---

## PROMPT 10 — Freeze Review

```
You are the Engineering Lead reviewing Phase [N] for freeze approval.

CONTEXT:
Phase [N] is [NAME]. All lifecycle steps (01–09) are complete. You are deciding whether to freeze.

CHECKLIST (all must be checked):
- [ ] Architecture Review completed and PROCEED recommended
- [ ] Current State Audit documented
- [ ] Gap Analysis complete — all gaps resolved or deferred with named phases
- [ ] Runtime Design produced and matches implementation
- [ ] Implementation complete and matches Runtime Design
- [ ] Unit tests: all pass
- [ ] Conversation tests: happy path + regression pass
- [ ] Stress tests: 2-hour session stable
- [ ] Regression: all prior phase tests pass
- [ ] 11_handover.md drafted

REVIEW EACH ITEM:
For each, state: CONFIRMED / NOT CONFIRMED / EXCEPTION (with explanation)

DECISION:
FROZEN / CONDITIONAL (list exceptions) / REJECTED (return to step N) / ROLLBACK

If FROZEN or CONDITIONAL — state what the phase's freeze locks:
- Which interfaces are now immutable
- What the regression baseline is for future phases

OUTPUT: Freeze decision document. Date. Decision. Reasoning.
```

---

## PROMPT 11 — Handover

```
You are a Handover Engineer writing the Phase [N] handover document for the next phase.

CONTEXT:
Phase [N] is FROZEN. You are writing for a future Claude instance or human contributor who has never seen this phase. They need to understand it cold in 10 minutes.

WRITE:
1. WHAT THIS PHASE BUILT — functional description (what eLo can now do), not code listing
2. FILES CHANGED — table: file path / status / what changed
3. RUNTIME INTERFACES — exact function signatures the next phase will consume
4. WHAT THE NEXT PHASE MUST NOT BREAK — specific behaviours as contracts
5. KNOWN ISSUES — honest table of any remaining gaps
6. GOTCHAS — the non-obvious things that cost hours if unknown

TONE: Briefing, not specification. 10-minute read. If the reader needs internals, they read the code.

Include the freeze decision: FROZEN / CONDITIONAL (with exception list).
```

---

## PROMPT — Architecture Constants Checker

Use this as a quick standalone check at any point during a phase.

```
You are an Architecture Constants Checker for eLo OS.

Review the proposed change/implementation described below against the six eLo OS Architecture Constants.

PROPOSED CHANGE:
[Describe the change or paste the relevant code]

CHECK EACH CONSTANT:
1. One Brain — does this add a decision-making path that bypasses the Executive?
2. One Executive — does this modify runtime/executive.py?
3. Faculties Observe — do new components produce observations, not decisions?
4. FREEZE_V1_LOCK — are runtime/executive.py and prompts/ untouched?
5. Silence is Valid — can this component produce nothing without error?
6. Evidence Gates — is this being implemented before prior phase validation? (Flag if yes.)

OUTPUT: COMPLIANT / VIOLATION / RISK for each constant. If any VIOLATION — stop. Do not proceed.
```

---

## PROMPT — Presence Test (Phase 2.5 Onward)

```
You are conducting a Presence Evaluation of eLo OS Desktop Buddy.

This is not a technical test. It is a subjective observation.

SETUP:
- eLo OS running (python server.py)
- Desktop Buddy visible on screen
- Do 30 minutes of real work — coding, designing, writing, researching
- Do not interact with eLo directly during this time
- After 30 minutes, answer the questions below

QUESTIONS:
1. Did Desktop Buddy feel like someone sharing the space? (Yes distinctly / Kind of / Not yet / No)
2. Did any Desktop Buddy behaviour feel surprising or off? If so, what?
3. Did Desktop Buddy's presence ever feel intrusive? If so, when?
4. Did Desktop Buddy's presence ever feel meaningful? If so, when?
5. Would you describe it as a companion or a widget?

OUTPUT: Your honest answers. No scoring. This is qualitative data.
```
