# WO-WKG-002 — WKG Write / Verification Path
**Priority:** P1 (after WO-WKG-001)
**Source:** existing ratified WKG architecture + `evaluate_write_gate()` in `knowledge/wkg_schema.py`
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Date:** 2026-08-22

---

## Objective

Make WKG writes obey the authority model. The LLM cannot turn its own generated statement into canonical WKG truth.

## What to build

Enforce the write path:

```
candidate claim
      ↓
evidence / provenance
      ↓
evaluate_write_gate()   ← already exists in wkg_schema.py
      ↓
verification state assigned
      ↓
WKG
```

`evaluate_write_gate()` is the existing gate — use it. Do not bypass, weaken, or rewrite it.

## Acceptance tests

For each: confirm correct epistemic_class, provenance retained, write gate enforced.

1. Verified claim with evidence pointer → writes as VERIFIED
2. Unverified claim without evidence → writes as UNVERIFIED (not promoted)
3. Speculative claim → writes as SPECULATIVE / proposed_claim only
4. Contradiction → both claims preserved + CONTRADICTS relationship
5. Generated claim (LLM output) → writes as GENERATED, cannot self-promote to VERIFIED
6. Unknown → remains UNKNOWN, no manufactured certainty
7. Provenance retained on read-back
8. Attempted unauthorised canonisation → gate blocks, claim not written as VERIFIED

## Hard constraints — do NOT

- bypass or weaken `evaluate_write_gate()`
- promote HYPOTHESIS/SPECULATIVE without David L3
- create a second write path
- invent new epistemic classes

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** `knowledge/wkg_schema.py` — `evaluate_write_gate()` enforces authority model. All write paths go through this gate; LLM-generated content cannot self-promote to VERIFIED without evidence pointer from L3 authority.

**Acceptance:** `tests/test_wkg002_003_write_gate.py` — 27/27 passed. All 8 acceptance scenarios covered: VERIFIED (with evidence), UNVERIFIED (no evidence), SPECULATIVE (proposed_claim only), CONTRADICTION (both + CONTRADICTS rel), GENERATED (cannot self-promote), UNKNOWN (remains unknown), provenance retained on read-back, unauthorised canonisation blocked.

**Regression:** WKG Phase 1 20/20 ✅ · WKG Phase 2 82/82 ✅ · BWKG-02 corpus 49/49 ✅
