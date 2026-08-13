# Volume 1 — Development Lifecycle

The 12-step process, with acceptance criteria for each step.

---

## Step 01 — Architecture Review

**Role:** Senior Architect. Read-only. No code.

**Input:** Entire project. All prior phase handovers. Current architecture docs.

**Output:** A report covering:
- What this phase adds to the cognitive stack
- What principles it must not violate
- What existing systems it touches
- What risks it introduces
- Whether the design is coherent

**Acceptance criteria:**
- Report references specific files and components, not generalities
- All 6 Architecture Constants checked explicitly
- At least one risk identified (if none, the review is incomplete)
- No implementation decisions made

**Reject if:** The review recommends implementation without completing all checks.

---

## Step 02 — Current State Audit

**Role:** Diagnostics Engineer. Read-only. No code.

**Input:** All files relevant to this phase. `tests/`. `architecture/`. Prior phase handover.

**Output:** A table of:
- What exists (file → what it does → working or not)
- What is wired vs. stubbed
- What is tested vs. untested
- What is documented vs. assumed

**Acceptance criteria:**
- Every claim is verified against actual file state, not memory
- ✅ / ⚠️ / 🔴 markers used honestly — ⚠️ means not tested, not "probably works"
- Stubs are listed as 🔴, not omitted

---

## Step 03 — Gap Analysis

**Role:** Systems Analyst.

**Input:** Current State Audit. Phase objectives. Prior phase handover.

**Output:**
- What this phase needs that doesn't exist yet
- What this phase needs that exists but needs modification
- What this phase must NOT change (frozen components, established contracts)
- Dependencies on other phases

**Acceptance criteria:**
- Every gap maps to a specific deliverable in Step 05 (Implementation)
- Gaps in frozen components flagged explicitly
- No gap is described as "probably fine" — either it's solved or it's a risk

---

## Step 04 — Runtime Design

**Role:** Runtime Architect.

**Input:** Gap Analysis. Architecture Review. All relevant source files.

**Output:**
- Exact data flow diagram (text-based ASCII or description)
- Every interface: what goes in, what comes out, what type
- Thread safety considerations
- Error paths (what happens when a component fails)
- Performance characteristics (latency, frequency, resource cost)

**Acceptance criteria:**
- Data flow is traceable end-to-end without reading code
- Every interface is specified with types, not descriptions
- Error paths are explicit — not "handle gracefully"

---

## Step 05 — Implementation

**Role:** Implementation Engineer.

**Input:** Runtime Design. Gap Analysis. All prior phase code.

**Output:** Working code committed to the project.

**Rules:**
- Implement exactly what the Runtime Design specifies — nothing more
- No refactoring of prior phases unless explicitly in the Gap Analysis
- Every new function has a single, testable responsibility
- No features added beyond the phase scope

**Acceptance criteria:**
- Code implements the Runtime Design exactly
- No modifications to FREEZE_V1_LOCK components
- All new functions are testable in isolation

---

## Step 06 — Unit Tests

**Role:** Test Engineer.

**Input:** Implementation. Runtime Design.

**Output:** Passing unit tests for every new component.

**What to test:**
- Each function with a single input → expected output
- Edge cases defined in the Runtime Design
- Error paths return expected values (not exceptions)
- Thread safety where relevant

**Acceptance criteria:**
- All unit tests pass
- Edge cases have dedicated tests (not "it probably handles it")
- Tests run without starting the server or connecting to external APIs

---

## Step 07 — Conversation Tests

**Role:** Conversation Validator. Talk to eLo. Try to break eLo.

**Input:** Running eLo OS. Conversation test scripts from this phase's playbook.

**Output:** Pass/fail for each test case, with the actual eLo response recorded.

**Test categories:**
- Happy path: the expected interaction works as designed
- Stress path: push the system with edge-case inputs
- Regression path: prior phase conversations still work correctly
- Silence path: verify eLo stays quiet when it should

**Acceptance criteria:**
- All happy path tests pass
- All regression tests pass
- Silence paths produce no spurious output
- Any stress path failure is documented as a known limitation or a bug

---

## Step 08 — Stress Tests

**Role:** Stress Test Engineer.

**Input:** Running eLo OS. Test protocols from this phase's playbook.

**Output:** Findings report — what degraded, what held, what failed.

**Standard stress scenarios:**
- Long session (2+ hours, continuous)
- Rapid input changes (app switching every 30 seconds)
- API failure injection (kill one backend, observe fallback)
- Empty stream scenario (all streams return nothing)
- Concurrent stream updates (multiple streams firing simultaneously)

**Acceptance criteria:**
- System remains stable over 2-hour session (no crashes, no runaway loops)
- Graceful degradation: failure of one component doesn't cascade
- Memory usage is stable (no unbounded growth)

---

## Step 09 — Regression

**Role:** Regression Engineer.

**Input:** All prior phase test suites. Running eLo OS.

**Output:** Pass/fail for all prior phase tests. Any regressions documented.

**Acceptance criteria:**
- All Phase 0 and Phase 1 tests pass
- All frozen phase conversation tests pass
- Any regression blocks the freeze until resolved

---

## Step 10 — Freeze Decision

**Role:** Engineering Lead (David Charles).

**Input:** All prior steps completed. Findings documented.

**Decision:** FROZEN / CONDITIONAL / REJECTED / ROLLBACK

- **FROZEN** — all acceptance criteria met. Phase is complete. Architecture is locked.
- **CONDITIONAL** — one or more minor gaps. Freeze proceeds with named exceptions that must be resolved in next phase.
- **REJECTED** — fundamental problem with the phase. Return to Step 03 (Gap Analysis).
- **ROLLBACK** — implementation introduced a regression. Revert to prior phase state. Investigate.

**What a freeze locks:**
- The phase's runtime interfaces
- The phase's documented behaviour
- The phase's test baseline

---

## Step 11 — Architecture Update

**Role:** Documentation Engineer.

**Input:** Completed implementation. Freeze decision.

**Output:**
- Updated architecture docs reflecting what was actually built (not what was designed)
- Updated phase sequence status in `engineering/README.md`
- Any superseded architecture notes marked with date

---

## Step 12 — Handover

**Role:** Handover Engineer.

**Input:** Everything from this phase.

**Output:** `11_handover.md` — a document the next phase can read cold and understand:
- What this phase built
- What interfaces the next phase will consume
- What the next phase must not break
- What known issues remain (if any)
- What the next phase should watch out for
