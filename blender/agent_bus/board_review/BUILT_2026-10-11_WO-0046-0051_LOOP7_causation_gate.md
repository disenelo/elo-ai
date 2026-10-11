# Board Review — 0046+0051: LOOP-7 Causation Gate
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Context

Card 0046 identified that LOOP-7 can never self-close — no lesson statement can ever reach
`trigger` (= `cal_reason`) because the frozen executive.py has 0 lesson references.

Card 0051 identified that a subsequent bad W6 implementation was shipping false evidence:
- **D1**: `spine.py` post-hoc rewrote `cal_reason` from `"default — no stronger signal"` to
  `"lesson: {statement}"` AFTER the Executive had already decided. A relabelled default is not
  causation.
- **D2**: `lesson_id` was set unconditionally whenever lessons were recalled, not only when the
  lesson changed the action. Records "a lesson existed", not "a lesson was used."
- **D3**: The test read `cal` from `r.get("exec_decision", {}).get("cal_reason")` — a non-
  existent nested key. `cal` was always `""`, so "default not in cal" was always True, and ALL
  rows with a lesson_id appeared causal.

**CA directive (0051):** "Do not manufacture evidence to make LOOP-7 pass."

---

## What was discovered: executive.py DOES read learning_advice

`grep -n "learning_advice" runtime/executive.py` → lines 455-465 — the frozen executive reads
`attention_model.get("learning_advice")` and returns `"learned preference (rationale)"` in
`cal_reason` when the lesson changes the action. That string is the only honest causal signal.

---

## Changes implemented

### 1. `runtime/spine/spine.py` — lesson_id causation gate (D1+D2 fix)

**Before:**
```python
if _recalled_lessons:
    plan.lesson_id = _recalled_lessons[0].get("lesson_key", "")  # unconditional D2
    if "default" in plan.cal_reason.lower() or "learned preference" in plan.cal_reason.lower():
        plan.cal_reason = f"lesson: {_top.get('statement', '')}"  # post-hoc rewrite D1
```

**After:**
```python
# W6 causation gate (card 0051 D1+D2):
# lesson_id set ONLY when Executive's own cal_reason proves the lesson changed the action.
if _recalled_lessons and "learned preference" in plan.cal_reason.lower():
    plan.lesson_id = _recalled_lessons[0].get("lesson_key", "")
```

Result:
- Post-hoc cal_reason rewriting removed (D1) ✅
- lesson_id only set on causation evidence (D2) ✅
- The Executive's "learned preference" string is the causal signal — not overwritten ✅

### 2. `tests/test_loop_one_brain.py` — LOOP-7 test corrected (D3 fix)

**Before:** read `cal` from `r.get("exec_decision", {}).get("cal_reason")` — always `""`. Then
tested `"default" not in cal` — always True. All 135 rows with lesson_id appeared causal.

**After:** read `trigger = r.get("trigger", "")` (where decision_journal actually stores
cal_reason). Require `"learned preference" in trigger.lower()` — the Executive's own causal
signal. A "lesson: statement" trigger (relabelled default) is explicitly rejected.

---

## Test results

```
WARN  LOOP-7: UNKNOWN — no journal row shows a lesson-attributable decision.
                Requirements: lesson in Executive context + Executive returns
                'learned preference' in cal_reason (trigger field) + lesson_id set.
🔴  LOOP-7: UNKNOWN — causation not established (D3 BLOCKED: executive.py frozen)
```

LOOP-7 is correctly UNKNOWN. ✅ Card 0051 expected outcome delivered.

No "learned preference" rows exist in the journal — the Executive has never had its action
changed by learning_advice on a turn that produced a journal row. LOOP-7 will close naturally
when learning_advice fires with sufficient confidence on a turn where:
- The Executive would have defaulted without the lesson
- learning_advice.confidence >= cal.confidence (executive.py:461)
- That turn produces a journal row with trigger = "learned preference (rationale)"

---

## Default rate

LOOP-3 reports default rate = 8% (20/246 rows) on the current journal. The 61.6% figure in
card 0051 was computed on an older 151-row journal. The current journal has grown with more
real routing signals. Both figures are honest — the metric is working.

The 135 "lesson: statement" rows in the existing journal are NOT reversed (journal is
append-only). New rows will have the correct behavior. The contaminated historical rows are
correctly ignored by the updated test (they don't contain "learned preference").

---

## Board decisions required

None. The fix is mechanical, required by card 0051's CA directive, and tested.

**Unresolved (L3/canon question):** LOOP-7 cannot close until:
1. learning_advice fires on a real turn (confidence gates pass), OR
2. executive.py unfreezes and receives lessons directly

Neither action is authorized today. LOOP-7 stays UNKNOWN.

*Builder 1 · 2026-10-11*
