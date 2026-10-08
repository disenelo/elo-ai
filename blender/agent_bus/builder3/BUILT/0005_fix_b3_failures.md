**WO:** FIX-B3-FAILURES · **Seat:** builder3 · **Priority:** P0
**Reserved?** no

## Goal
Fix Builder 3's confirmed code failures. Exact errors below.

## Fix 1 — `test_wo030_weather_location.py` — 12/14 FAILING (biggest failure in the suite)
**Errors:**
- `_DEFAULT_LOCATION constant missing` from tool_router_test
- `module 'tool_router_test' has no attribute '_user_location'`
- `module 'tool_router_test' has no attribute '_detect_followup'`
- `module 'tool_router_test' has no attribute '_LOCATION_SET_PATTERNS'`
- `module 'tool_router_test' has no attribute '_load_persisted_location'`
- `No module named 'memory'` (on Mac this should resolve — run first)

**File:** `tools/` — weather/location tool
**Fix:** The test imports `tool_router_test` and expects these attributes. They are missing. Add: `_DEFAULT_LOCATION`, `_user_location`, `_detect_followup`, `_LOCATION_SET_PATTERNS`, `_load_persisted_location` to the tool router module.

## Fix 2 — `test_wo_create_capability.py` — 1 failed
Run: `python3 tests/test_wo_create_capability.py` — read exact error, fix.

## Fix 3 — `test_wo122_route_capability_to_executor.py` — 1 failed
Run: `python3 tests/test_wo122_route_capability_to_executor.py` — read exact error, fix.

## After each fix: rerun the specific test. Confirm green.

## Files to touch
`tools/` (weather/location tool) · `capability_registry.py`

## Done when
All fixed and green. Committed. Move to BUILT/.

## Result
- commit: 97d7a35
- tests fixed (run 2026-10-08 under the server's python, /Users/Disenelo/miniconda3/bin/python, and system python3):
  - test_wo030_weather_location.py 14/14. The missing-attribute errors were already gone; the last failure was
    `ModuleNotFoundError: httpx` from accuweather_agent's top-level import. httpx is now optional.
  - test_wo_create_capability.py 6/6. AT-3: the draft notification now says "I've made a draft (<file>) — want to see it?"
  - test_wo122_route_capability_to_executor.py 5/5. RT-3 predates WO-CAP-COG-004, which strips a bare "the time".
    The test plan query is now "what time is it". No routing code changed; weather still doesn't fire.
  - Builder 3 suite + WO-058 + WO-030 under the server's python: 122 passed.
  - Note: under .venv/bin/python the Alexa tests error with `No module named 'cryptography'` (not installed in that venv). The server doesn't use .venv.

## Live turn needed
> Board reruns test suite and confirms pass rate moved toward 70%.
