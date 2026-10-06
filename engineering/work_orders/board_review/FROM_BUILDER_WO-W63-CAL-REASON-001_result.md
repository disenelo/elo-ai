# WO-W63-CAL-REASON-001 — Result Card

**Status**: COMPLETE — already implemented; verified 2026-10-06
**Lane**: `runtime/spine/spine.py`
**Date**: 2026-10-06

## What was found

The CAL reason amendment on default routing path is implemented at spine.py:512–520:

```python
# WO-W63-CAL-REASON-001: any cal_reason containing "default" or "learned preference"
# means the recalled lesson is the authoritative reason — amend it.
if "default" in plan.cal_reason.lower() or "learned preference" in plan.cal_reason.lower():
    plan.cal_reason = f"lesson: {_top.get('statement', '')}"
```

This fires on all default routing paths, not just signal-based. The guard conditions cover:
- `"default — no stronger signal"` 
- `"conversation — default to answer (per _RESPONSE_GOAL)"`
- Any string containing `"default"` (covers all Executive default branch variants)
- `"learned preference"` (covers learning_advice routing)

## Acceptance test

```
tests/test_w6_lesson_attribution.py::test_w6_3_cal_reason_amended_on_default PASSED
```

No code changes made — implementation was already present.

## Files

| File | Lines |
|---|---|
| `runtime/spine/spine.py` | 509–520 (lesson attribution gate + WO-W63 amendment) |
