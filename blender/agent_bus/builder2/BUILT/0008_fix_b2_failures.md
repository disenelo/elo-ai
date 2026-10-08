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
- commit: none needed — **all five were already green when the card was opened**
- tests fixed: 0 (0 were broken)

Ran all five directly, as the card specifies, before changing anything:

    test_wo032_backend_voice_drift      exit 0   "WO-032  6 passed  0 failed"
    test_0012_wave4_verify_choose       exit 0
    test_0017_autobiography_provenance  exit 0
    test_wo039_f4_cross_session_recall  exit 0
    test_wo081_emergent_cognition       exit 0

Checked the three named symptoms directly rather than trusting exit codes:

    `_openai_quota_exceeded` in backend_router.py   present
    `"Can't reach my thinking"` in server.py        present
    quota guard in route()                          present (AT-2 asserts it)

Fixed by Builder 1 in `daaf7d1` (card 0069 — "remove permanent OpenAI snub,
60s cooldown mirrors Groq") and `13ef597`. backend_router.py is their lane,
which the card itself flags, so this was never Builder 2 work to do — only to
confirm.

**Worth knowing for the Board's pass-rate measure:** all five are
script-style, and `tests/conftest.py` deliberately skips script-style files
during pytest collection (they `sys.exit()` at module level and would cause
INTERNALERROR). So `pytest tests/` has never counted them, passing or
failing. A pass-rate measured by pytest alone will not move when these are
fixed, and did not drop when they broke.

## Live turn needed
None — this card is test maintenance, not behaviour. Nothing for David to
observe.

The Board's "rerun the suite, confirm pass rate moved toward 70%" cannot be
satisfied by these five: pytest does not collect them. To count them the
runner needs to invoke each as a script, or they need converting to pytest
functions. Flagged rather than silently left.

## Live turn needed
> Board reruns test suite and confirms pass rate moved toward 70%.
