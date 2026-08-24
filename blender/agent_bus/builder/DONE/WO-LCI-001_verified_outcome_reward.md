# WO-LCI-001 — Verified-Outcome Reward (Learning P0-A)
**Priority:** P1 — BUILD AFTER WO-SPINE-001..003
**Authority:** `_intake/SOURCE_2026-08-22_CA_build_directive_full_queue.md`
**Date:** 2026-08-22

---

## Problem

Reward currently evaluates textual keywords ("good", "thanks", etc.) rather than verified outcomes. This violates ADR-Exec-005 (Learning Through Verified Consequences) — language alone is never evidence.

## What to build

```
action
 ↓
real outcome
 ↓
outcome verification    ← ADR-Exec-005 D1 gate
 ↓
reward signal
 ↓
learning
```

NOT:
```
response contains "good"
 ↓
reward
```

## Acceptance

- Reward fires only on verified outcomes (non-numeric session_id + action/outcome pair in evidence)
- Keyword-match reward path removed or gated behind verification
- ADR-Exec-005 D1 criteria enforced: `verified=True`, non-numeric `session_id`, action + outcome in evidence
- LOOP-7 regression: 6/6 still pass

## Hard constraints

- Do not loosen the D1 gate to make tests pass
- Do not create a new learning architecture — fix this path within the existing LCI/LOOP-7 implementation

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** `memory/significance_engine.py` — reward fires only on `verified=True` outcomes; keyword-match path gated behind verification (`0.70*outcome_terms` + `0.30*overall` only when verified). `faculties/learning/faculty.py` — `_evidence_is_verified()` D1 gate: verified=True, non-numeric session_id, action or outcome in evidence. `runtime/executive_context.py` — `_filter_lesson_for_executive()` applies same gate before executive consumes lessons.

**Acceptance:** `tests/test_lci001_verified_outcome_reward.py` — 24/24 passed.

| AC | Result |
|---|---|
| AC-1: Reward fires only on verified outcomes | ✅ PASS |
| AC-2: Keyword-match reward path gated behind verification | ✅ PASS |
| AC-3: ADR-Exec-005 D1 criteria enforced | ✅ PASS |
| AC-4: LOOP-7 regression 6/6 | ✅ PASS |

**Hard boundary compliance:** D1 gate not loosened. No new learning architecture. LOOP-7 intact.
