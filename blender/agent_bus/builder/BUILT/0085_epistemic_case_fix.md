# WO-0085 — Epistemic Case Fix
**Seat:** Builder 1  
**Priority:** P1  
**Date:** 2026-10-11  
**Commit:** 14c9cbd

## What was built

Single-line fix at `runtime/wkg_faculty.py:342` — the `record_claim()` entry boundary:

```python
# Before
if epistemic_class not in _EPISTEMIC_CLASSES:
    raise ValueError(...)

# After
epistemic_class = epistemic_class.strip().upper()  # WO-0085
if epistemic_class not in _EPISTEMIC_CLASSES:
    raise ValueError(...)
```

Callers passing `"verified"`, `"source_attributed"` or any mixed-case variant now get normalised to canonical uppercase before the gate check. All downstream comparisons (`== "VERIFIED"`, `in _RELATIONSHIP_GATE_CLASSES`) receive canonical uppercase with no further changes.

## Tests

- 372 `wkg or epistemic` tests pass (no regressions)
- Manual verify: `record_claim(..., epistemic_class="verified")` → stores `"VERIFIED"`, no ValueError

*Builder 1 · 2026-10-11*
