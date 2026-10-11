# Board Review — 0085: Epistemic Case Fix
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Research claims blocked from reaching WKG by case mismatch: callers send lowercase
`epistemic_class` ("verified", "source_attributed"); gate set was `{"VERIFIED", "SOURCE_ATTRIBUTED"}`.
Fix: normalise to uppercase before comparison.

---

## Implementation status at review time

Fix already applied. `memory/memory_faculty.py:390`:

```python
# WO-0085: normalise case — callers use "verified"/"canonical" (lowercase),
# gate uses uppercase. Normalise before comparison and before passing to record_claim.
_epi_normalised = candidate.epistemic_class.upper()
if _epi_normalised not in _WKG_GATE_EPISTEMIC:
    return
```

`_WKG_GATE_EPISTEMIC = frozenset({"VERIFIED", "SOURCE_ATTRIBUTED"})` at line 373.
`"verified".upper()` = `"VERIFIED"` — gate passes correctly.

---

## New test — `test_auto8_lowercase_verified_passes_gate`

Added to `tests/test_wo_wkg_auto_populate_001.py`. Verifies that `"verified".upper()`
and `"source_attributed".upper()` are both in the gate set — i.e., the `.upper()`
normalisation makes lowercase callers pass.

```
tests/test_wo_wkg_auto_populate_001.py — 8 passed in 0.23s
```

---

## Board decisions required

None. Implementation correct, test passing.

*Builder 1 · 2026-10-11*
