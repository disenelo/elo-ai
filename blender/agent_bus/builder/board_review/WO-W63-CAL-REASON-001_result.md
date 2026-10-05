# WO-W63-CAL-REASON-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Status:** COMPLETE — test passes in current HEAD, result card written 2026-10-05

---

## Gap closed

`spine.py` CAL reason amendment block only fired on signal-based routing, not on the default path. When Executive returned default routing reason AND a lesson was recalled, `plan.cal_reason` was not amended to `"lesson: <statement>"`.

---

## Current state (verified 2026-10-05)

`test_w6_lesson_attribution.py::test_w6_3_cal_reason_amended_on_default` — **PASSES** in current HEAD.

The amendment block was previously fixed and is already in `runtime/spine/spine.py` (~line 405-415): if `_learning_advice` has a matching `lesson_key` AND `plan.cal_reason` is the default value → amend to `"lesson: {statement}"`. This now fires on the default routing path.

---

## Acceptance

✅ `test_w6_3_cal_reason_amended_on_default` PASSES  
✅ 44,606-lesson ledger attribution fires on default path
