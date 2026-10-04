# WO-079 The Moment / Situated Self Invariant — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 8/8 ATs pass; already implemented in prior session

---

## What was verified

`runtime/the_moment.py` + `server.py`:
- `compile()` returns well-formed dict with required fields
- `write()` creates `self/state/the_moment.json` with correct schema
- Epistemic tier tagging: `perch_fresh=True` → `surface_tier="verified"`; False → `"last-known"`
- `pose_acked=True` → `pose_tier="verified"`; False → `"last-known"`
- `situated_with_epistemic()` returns `[verified]/[last-known]/[live]` tags
- Never asserts unverified state as verified
- `write()` failure is silent — no exception propagated

## ATs

- AT-1 ✅ compile() returns well-formed dict with required fields
- AT-2 ✅ write() creates self/state/the_moment.json with correct schema
- AT-3 ✅ perch_fresh=True → surface_tier="verified"; False → "last-known"
- AT-4 ✅ pose_acked=True → pose_tier="verified"; False → "last-known"
- AT-5 ✅ situated_with_epistemic() returns [verified]/[last-known]/[live] tags
- AT-6 ✅ never asserts unverified state as verified
- AT-7 ✅ write() failure is silent — no exception propagated
- AT-8 ✅ py_compile clean on runtime/the_moment.py and server.py

**Run:** `python3 tests/test_wo079_the_moment.py` → **8/8 passed**
