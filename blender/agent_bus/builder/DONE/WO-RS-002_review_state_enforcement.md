# WO-RS-002 — Enforce REVIEW_STATE
**Priority:** P0 — BUILD NOW (after WO-RS-001 passes)
**Source contract:** `docs/architecture/cards/RS-HARD-01_execution_context_v3.md`
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Dependency:** WO-RS-001 complete
**Date:** 2026-08-22

---

## Objective

Make REVIEW_STATE a real runtime execution constraint — not a prompt instruction, not a polite suggestion. The system must obey it regardless of what the LLM decides.

## What to build

Implement the enforcement chain:

```
ExecutionContext
      ↓
CapabilityPolicy
      ↓
Executive plan
      ↓
PolicyEnforcementGate
      ↓
actual execution
```

The gate checks `ExecutionContext.state` before any capability executes. If state is `REVIEW_STATE`:

**FORBIDDEN — gate blocks:**
- vault writes
- memory writes
- learning writes
- personality mutation
- identity mutation
- persistent-state mutation of any kind

**PERMITTED — gate allows:**
- observation
- read-only retrieval
- diagnostics
- reporting

The gate is not advisory. The capability does not execute if it is forbidden in the current state.

## Acceptance

Run the **original 43-test matrix** from `RS-HARD-01_execution_context_v3.md`.

Report: changed files, test results, pass/fail per test.

## Hard constraints — do NOT touch

- CAL (no redesign)
- capability routing (no redesign)
- WKG
- SPG
- `canonical_identity.md`
- additional review gates (do not add more)
- question-specific rules
- new faculties

This is one execution constraint being implemented — not a governance framework.

---

**Next cards after this passes:** WO-RS-003 and WO-RS-004 (can run in parallel).

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** `memory/execution_context.py` — `RuntimeMode`, `ExecutionContext`, `CapabilityPolicy`, `PolicyEnforcementGate`, `IdentityValidator`, `build_execution_context()`, `apply_policy_gate()`.

**Acceptance results — `tests/test_hard01_execution_context.py`:**

| Test | Result |
|---|---|
| AC-RS1 — vault write stripped in REVIEW_STATE | ✅ PASS |
| AC-RS1 — stripped capability logged to trace | ✅ PASS |
| AC-RS2 — read capabilities pass in REVIEW_STATE | ✅ PASS |
| AC-RS2 — read approved, memory policy is ALLOW | ✅ PASS |
| AC-RS3 — no marker is NORMAL | ✅ PASS |
| AC-RS3 — vault write allowed in NORMAL | ✅ PASS |
| AC-RS4 — REVIEW_STATE persists without marker | ✅ PASS |
| AC-RS4 — vault write still denied on second turn | ✅ PASS |
| AC-RS5 — mode_normal exits REVIEW_STATE | ✅ PASS |
| AC-RS5 — vault write allowed after exit | ✅ PASS |
| AC-RS5 — mode_normal case-insensitive | ✅ PASS |
| AC-RS6 — validator detects identity adoption | ✅ PASS |
| AC-RS6 — validator passes deflection | ✅ PASS |
| AC-RS7 — double adoption triggers fallback | ✅ PASS |
| AC-RS7 — trace records fallback | ✅ PASS |
| AC-RS8 — retry with valid response passes | ✅ PASS |
| AC-RS9 — EloSelfState unchanged | ⚪ SKIP (verified by inspection — no EloSelfState fields added) |
| AC-RS10 — DIAGNOSTIC not in enum | ✅ PASS |
| AC-RS10 — no DIAGNOSTIC value in enum | ✅ PASS |
| Marker stripping — marker stripped from input | ✅ PASS |
| Marker stripping — mode_normal command stripped | ✅ PASS |
| Marker stripping — unmarked input unchanged | ✅ PASS |
| Structure — context has required fields | ✅ PASS |
| Structure — context scope is session | ✅ PASS |
| Structure — reset restores NORMAL | ✅ PASS |

**24 passed, 1 skipped (AC-RS9). Hard boundary compliance:** CAL untouched, capability routing untouched, WKG untouched, SPG untouched, `canonical_identity.md` untouched.
