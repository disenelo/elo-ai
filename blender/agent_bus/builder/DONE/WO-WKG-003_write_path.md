# WO-WKG-003 — WKG Write Path
**Priority:** P1 — BUILD AFTER WO-WKG-001 (read path functional)
**Authority:** `_intake/SOURCE_2026-08-22_CA_build_directive_full_queue.md`
**Date:** 2026-08-22

---

## Objective

Implement the already-defined WKG write contract. Generated content must not silently become WKG truth.

## The write path

```
model generates claim
        ↓
candidate
        ↓
evidence / verification process
        ↓
evaluate_write_gate()    ← existing, in wkg_schema.py
        ↓
WKG status assigned
        ↓
WKG persistence
```

NOT:
```
model says it → WKG → truth
```

## Acceptance

Same 8 tests as WO-WKG-002 (these cards overlap — reconcile and run whichever hasn't been covered):
- Verified claim with evidence → VERIFIED
- Unverified → UNVERIFIED (not promoted)
- Speculative → SPECULATIVE / proposed_claim only
- Contradiction → both claims + CONTRADICTS
- LLM-generated claim → GENERATED, cannot self-promote
- Unknown → UNKNOWN, no manufactured certainty
- Provenance retained on read-back
- Attempted unauthorised canonisation → gate blocks

## Hard constraints

- No new governance layer
- Use the existing WKG authority model and `evaluate_write_gate()`
- No bypass of the gate
- No second write path

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE — covered by WO-WKG-002

Both WO-WKG-002 and WO-WKG-003 address the same write gate requirement. All 8 acceptance tests run under `tests/test_wkg002_003_write_gate.py` — 27/27 passed. No second write path exists. Gate not bypassed.
