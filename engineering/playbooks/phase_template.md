# Phase Playbook Template — [Work Package Name]

**Work Package:** WP_[X] — [Name]
**Status:** FOUNDATION / IN PROGRESS / COMPLETE / FROZEN
**Owner:** David Charles / DISENELO
**Started:**
**Frozen:**

> Copy this file to `engineering/work_packages/WP_[X]_[Name]/` and work through each section in order.
> Do not skip sections. Do not begin implementation before sections 1–4 are complete.

---

## Section 1 — Architecture Review

**Role:** Senior Architecture Engineer
**Input:** All existing architecture documents, prior phase freeze docs
**Output:** Review report with verdict

**Purpose:** Read everything before touching anything. Produce an honest picture of what exists, what works, what is broken.

**Claude prompt:**

```
You are acting as the Senior Architecture Engineer for eLo OS.

Your task is NOT to implement anything.

Your task is to review the current state of [component/faculty name] and produce an Architecture Review.

Read:
- docs/architecture/[relevant].md
- engineering/work_packages/[prior WP]/freeze.md
- The relevant runtime code in runtime/ and tools/

Produce the following:
1. What currently exists (be specific — files, functions, interfaces)
2. What is working (evidence, not assumption)
3. What is broken or untested
4. One Brain Principle check — trace every data path to the Executive
5. Architectural risks
6. Interaction with every other faculty
7. Gap analysis — what is missing for this phase
8. Recommended next step

Do not write code. Do not propose solutions. Describe what is there.
Fill in engineering/templates/architecture_review.md.
```

**Checklist:**
- [ ] All architecture documents read
- [ ] Prior freeze documents read
- [ ] Runtime code reviewed
- [ ] One Brain data flow traced
- [ ] Risks identified
- [ ] Review verdict recorded in `architecture_review.md`

---

## Section 2 — Current State Audit

**Role:** Diagnostics Engineer
**Input:** Architecture Review, runtime environment
**Output:** Diagnostics report

**Purpose:** Go beyond documents. Run the system. Observe what it actually does.

**Claude prompt:**

```
You are acting as the Diagnostics Engineer for eLo OS.

Run [work package name] through the diagnostic protocol.

1. Start the eLo OS server
2. Run the health check sequence from engineering/templates/diagnostics.md
3. Run 10 conversation turns targeting the behaviour under review
4. Log every anomaly
5. Identify root causes

Do not fix anything yet. Record what you observe.
Fill in engineering/templates/diagnostics.md.
```

**Checklist:**
- [ ] Server health confirmed
- [ ] Backend active
- [ ] Vision loop checked (if relevant)
- [ ] 10+ conversation turns logged
- [ ] Anomalies recorded

---

## Section 3 — Gap Analysis

**Role:** Senior Architecture Engineer
**Input:** Architecture Review, Diagnostics
**Output:** Ordered list of gaps with priorities

**Purpose:** Translate observations into a specific list of what this work package must deliver.

**What to produce:**

| Gap | Priority | Blocks |
|---|---|---|
| | CRITICAL / HIGH / NORMAL | |

**Acceptance:** Every gap has a priority. Every CRITICAL gap has a resolution path before implementation begins.

---

## Section 4 — Architecture Design

**Role:** Senior Architecture Engineer
**Input:** Gap Analysis
**Output:** Exact runtime design — data flow, interfaces, contracts

**Purpose:** Design before code. Every interface and contract must be documented before Step 5 begins.

**Claude prompt:**

```
You are acting as the Senior Architecture Engineer for eLo OS.

Design the architecture for [component name].

Produce:
1. Runtime flow diagram (text-based — input → component → output → Executive)
2. Exact interface for each new component (inputs, outputs, invariants)
3. What changes to existing files (nothing in FREEZE_V1_LOCK)
4. What is explicitly not changing

Invariants that must hold:
- This component never decides. It observes.
- Empty input → empty output. No fallback unless explicitly specified.
- Never raises. All failures are silent and logged.
- FREEZE_V1_LOCK: runtime/executive.py and prompts/ are never modified.
```

**Checklist:**
- [ ] Runtime flow documented
- [ ] Every interface has exact input/output spec
- [ ] Nothing in FREEZE_V1_LOCK is touched
- [ ] Design reviewed before moving to implementation

---

## Section 5 — Implementation Plan

**Role:** Runtime Engineer / Systems Integrator
**Input:** Architecture Design
**Output:** Ordered implementation sequence

**Purpose:** Translate architecture into a specific sequence of discrete, testable steps.

Fill in `engineering/templates/implementation_plan.md`.

**Checklist:**
- [ ] Each step is discrete and independently testable
- [ ] File list is complete
- [ ] Rollback plan is documented
- [ ] Implementation plan reviewed before coding begins

---

## Section 6 — Implementation

**Role:** Runtime Engineer
**Input:** Implementation Plan
**Output:** Working code

**Rules:**
- One step at a time. Confirm each step before the next.
- No scope creep. Build exactly what is in the plan.
- No error handling for cases that cannot happen.
- No fallback behaviour unless the spec requires it.
- If blocked, document the blocker and surface it — do not work around it silently.

---

## Section 7 — Code Review

**Role:** Senior Architecture Engineer
**Input:** Completed implementation
**Output:** Review report

**Claude prompt:**

```
You are acting as the Senior Architecture Engineer reviewing implementation for [work package name].

Review the following files: [list files]

Check:
1. Does every new component observe only — never decide?
2. Is the Executive the sole decision-maker?
3. Is silence valid output?
4. Are there any silent fallbacks that should not exist?
5. Is FREEZE_V1_LOCK respected?
6. Is there any scope creep beyond the implementation plan?

Produce a code review report. PASS or FAIL with specific line references for any failure.
```

---

## Section 8 — Unit Tests

**Role:** Regression Engineer
**Input:** Implementation
**Output:** Passing test suite

**Location:** `tests/test_[component_name].py`

**Minimum coverage:**
- Happy path
- Empty input → no output
- Malformed input → silent failure, logged
- Integration with Executive (mocked)

---

## Section 9 — Conversation Validation

**Role:** Conversation Reviewer
**Input:** Running system
**Output:** Conversation test report

**Claude prompt:**

```
You are acting as the Conversation Reviewer for eLo OS.

Run a 20-turn conversation with eLo covering:
- Greetings and farewells
- Work discussion (eLo-Planet game, robot, book)
- Emotional content
- Tool invocations relevant to this work package
- Edge cases specific to [component name]

After each turn record: input, output, backend, anomalies.
Produce a pass/fail report against the acceptance criteria in the implementation plan.
```

---

## Section 10 — Desktop and Embodiment Validation

**Role:** Presence Reviewer / Desktop Reviewer
**Input:** Running system + DISENELO Presence app
**Output:** Embodiment validation report

Check:
- [ ] Avatar responds correctly to this phase's behaviour
- [ ] blender_state.json is updated correctly
- [ ] No embodiment fires when there is no input
- [ ] Voice (TTS) fires on first bubble only

---

## Section 11 — Regression Testing

**Role:** Regression Engineer
**Input:** Running system
**Output:** Regression report

Fill in `engineering/templates/regression.md`.

Every prior frozen phase regression test must pass. Zero tolerance.

---

## Section 12 — Stress Testing

**Role:** Regression Engineer / Diagnostics Engineer
**Input:** Running system
**Output:** Stress test report

**Minimum stress protocol:**
- 45-minute continuous conversation session
- Repeated identical inputs (loop guard test)
- Rapid-fire inputs (queue test)
- Tool invocations under load
- Absent desktop (no active app)
- Vision disabled

Record any degradation, memory growth, or behavioural drift.

---

## Section 13 — Freeze Decision

**Role:** Release Engineer
**Input:** All prior section results
**Output:** Freeze document signed or rejected

Fill in `engineering/templates/freeze.md`.

No phase may be frozen unless all criteria in the freeze template are met.

---

## Section 14 — Documentation Update

**Role:** Release Engineer
**Input:** Freeze decision
**Output:** Updated architecture documents

- Update `docs/architecture/[relevant].md` to reflect what was built
- Update `engineering/README.md` Phase Sequence table
- Do not rewrite history — append superseded notes

---

## Section 15 — Handover

**Role:** Systems Integrator
**Input:** Frozen phase
**Output:** Handover document

Fill in `engineering/templates/handover.md`.

The next work package does not begin until handover is complete.
