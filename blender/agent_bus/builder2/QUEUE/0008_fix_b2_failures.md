**WO:** FIX-B2-FAILURES · **Seat:** builder2 · **Priority:** P0
**Reserved?** no

## Goal
Fix Builder 2's confirmed code failures. Exact errors below.

## Fix 1 — `test_wo032_backend_voice_drift.py` — 3 failed
**Errors:**
- `_openai_quota_exceeded not found in backend_router` — function missing from `backend_router.py`
- `quota flag guard not found in route() auto block` — guard not in the route() function
- `'Can't reach my thinking' string not found in server.py` — fallback string missing

**Files:** `runtime/backend_router.py` · `server.py`
**Fix:** Add `_openai_quota_exceeded` function to backend_router. Add quota flag guard in `route()`. Add `"Can't reach my thinking"` fallback string to server.py.
**Note:** backend_router.py is Builder 1 territory per FILE OWNERSHIP rules. Raise these 3 items to Builder 1 via outbox if you cannot touch that file. You CAN fix the server.py string.

## Fix 2 — `test_0012_wave4_verify_choose.py` — 1 failed
Run: `python3 tests/test_0012_wave4_verify_choose.py` — read exact error, fix.

## Fix 3 — `test_0017_autobiography_provenance.py` — 1 failed
Run: `python3 tests/test_0017_autobiography_provenance.py` — read exact error, fix.

## Fix 4 — `test_wo039_f4_cross_session_recall.py` — 1 failed
Run: `python3 tests/test_wo039_f4_cross_session_recall.py` — read exact error, fix.

## Fix 5 — `test_wo081_emergent_cognition.py` — 1 failed
Run: `python3 tests/test_wo081_emergent_cognition.py` — read exact error, fix.

## After each fix: rerun the specific test. Confirm green.

## Done when
All fixed and green. Committed. Move to BUILT/.

## Result
- commit:
- tests fixed:

## Live turn needed
> Board reruns test suite and confirms pass rate moved toward 70%.
