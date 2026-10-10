**WO:** FIX-B1-FAILURES · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
Fix Builder 1's confirmed code failures. Exact errors below — no investigation needed, go straight to the fix.

## Fix 1 — `test_wo_relationship_style.py` — 4 failed
**Error:** `cannot import name '_derive_relationship_mode' from 'runtime.spine.relationship_faculty'`
**File:** `runtime/spine/relationship_faculty.py`
**Fix:** `_derive_relationship_mode` function is missing from this file. The test expects it. Add it or expose it.

## Fix 2 — `test_wo102_person_place_event.py` — 3 failed
**Error:** Nodes stored with `kind='fact'` instead of `kind='person'`/`kind='place'`/`kind='event'`
**Fix:** In the person/place/event writer — when writing a node of type person, place, or event, set `kind` to the entity type, not `'fact'`.

## Fix 3 — `test_drop_loop_0001.py` — 2 failed
**Error:** `No such file or directory: .../02_CATALOGUED/_processed.log`
**Fix:** The drop loop isn't writing `_processed.log` to the `02_CATALOGUED/` folder after processing. Add that write.

## Fix 4 — `test_0009_row1_identity.py` — 1 failed
Run: `python3 tests/test_0009_row1_identity.py` — read exact error, fix.

## Fix 5 — `test_0010_wo103_wave3.py` — PW-2 FAIL
**Error:** `_write() strips gaze` — gaze field being stripped on write
**File:** wherever `_write()` is defined in the wave 3 path
**Fix:** Preserve gaze field through `_write()`.

## Fix 6 — `test_canon_iv_ordering_invariants.py` — 2 failed
Run: `python3 tests/test_canon_iv_ordering_invariants.py` — read exact errors, fix.

## Fix 7 — `test_0020_ct0033_bypass_handlers.py`
**Error:** expected 53 `_bypass_journal` calls, found 55
**Fix:** Either 2 new bypass calls were added without updating the test count, or 2 spurious calls exist. Check `server.py` for recent `_bypass_journal` additions, remove spurious ones or update the expected count with justification.

## Fix 8 — `test_d3_lesson_reaches_executive.py`
**Error:** `executive.py` hash changed — expected `e401c11f`, got `9f55186d`
**Fix:** Update the expected hash in the test to `9f55186da3386234b065ccb1b0efeb98afa56d2f`. Verify the executive.py change was intentional first.

## After each fix: rerun the specific test. Confirm green. Then move to next.

## Files to touch
`runtime/spine/relationship_faculty.py` · person/place/event writer · drop loop processor · executive.py hash test · others per investigation

## Done when
All 8 fixed and green. Rerun full suite — report new pass count. Move to BUILT/.

## Result
- commit:
- tests fixed:
- new pass rate:

## Live turn needed
> Board reruns test suite and confirms pass rate moved toward 70%.
