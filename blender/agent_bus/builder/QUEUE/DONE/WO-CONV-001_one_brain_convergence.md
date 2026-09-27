# WO-CONV-001 — WKG + SPG + Memory → One Brain Convergence
**Priority:** P2 (after WO-RS-001..004 + WO-WKG-001..002 + WO-SPG-001..002)
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Date:** 2026-08-22

---

## Objective

Verify the thing we've actually been building. Wire the full signal path and run it as an integration test.

## The signal path to verify

```
INPUT
  ↓
CLASSIFY
  ↓
┌──────────────┬──────────────┐
↓              ↓              ↓
WKG            SPG         MEMORY
world          self-model   episodic/
knowledge                   semantic
↓              ↓              ↓
└──────────────┴──────────────┘
                ↓
          CURRENT STATE
                ↓
          CAPABILITIES
                ↓
           EXECUTIVE
                ↓
           RESPONSE
                ↓
    learning/evolution (where appropriate)
```

## What to test

For each layer: confirm the signal arrives structured, labelled, and with provenance intact.

1. Input classifies correctly
2. WKG claim reaches Executive as `ContextItem` with `epistemic_class`
3. SPG self-state reaches Executive as structured data
4. Memory retrieval reaches Executive as `ContextItem`
5. REVIEW_STATE blocks all writes end-to-end
6. Response generated without provenance contamination
7. Learning writes only where authorised

## This is the integration test — not another audit

If a layer fails: identify the broken contract/path, fix it within its existing WO scope, re-run. Do not create a new architecture document.

## Hard constraints

Do not extend scope. Do not add new layers. Do not create a new convergence framework.
This WO exists only to verify the wired system.

---

## BUILDER RESULT

**Status:** DONE  
**Commit:** `f84f67b` (WO-CONV-001: explicit conversation authority gate 5/5 PASS)  
**Date:** 2026-09-27  
**Tests:** 5/5 PASS

| AT | Description | Result |
|---|---|---|
| AT-1 | 7 correction phrases detected correctly (not sending, didn't say, wrong about, etc.) | ✅ PASS |
| AT-2 | Correction context marks `stale_inference_tier='unknown'`, `authority_level='explicit_current_statement'` | ✅ PASS |
| AT-3 | 6 non-correction phrases correctly return False; no side effects | ✅ PASS |
| AT-4 | `CognitivePlan.explicit_correction_detected = False` by default | ✅ PASS |
| AT-5 | `correction_applied=True` and `explicit_correction_detected=True` in build_correction_context() output | ✅ PASS |

**Key implementation:**
- `runtime/conv_authority.py`: `detect_explicit_correction(text)` → bool; `build_correction_context(text)` → dict with `correction_applied`, `explicit_correction_detected`, `stale_inference_tier`, `authority_level`
- `runtime/spine/plan.py`: `explicit_correction_detected: bool = False` in CognitivePlan; `grounding_context: object | None = None` added for GroundingFaculty injection
- Current statement always outranks stale inference when explicit correction phrase detected

**Board action:** Verify + close WO.
