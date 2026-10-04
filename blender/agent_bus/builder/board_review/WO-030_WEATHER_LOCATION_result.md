# WO-030 Weather Default Location — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — v2 + b tests pass (7/7 + 7/7); v1 tests are stale (old test module, retired)

---

## What was verified

Per WO-030 REOPENED spec (David 2026-08-03):
1. No-location weather query returns ask-sentinel ("where are you?"), never silently defaults to London.
2. "I'm in Hackney Wick" / "the studio is in Hackney Wick" detected + city saved to `user_location.json`.
3. Explicit city in query ("Paris") overrides saved location.
4. `user_location.json` city is not stale "Manchester".
5. wttr.in uses queried `{city}` not `nearest_area`.
6. `blender_state.json` `weather` key survives consecutive `_write()` calls (WO-030b/058b).

## ATs

**v2 (WO-030 main behaviour):**
- AT-1 ✅ no-location → ask-sentinel (not London weather)
- AT-2 ✅ 'I'm in Hackney Wick' → city='Hackney Wick'
- AT-3 ✅ 'the studio is in Hackney Wick' → city='Hackney Wick'
- AT-4 ✅ explicit city 'Paris' extracted, overrides saved
- AT-5 ✅ user_location.json city is 'Hackney Wick' (not Manchester)
- AT-6 ✅ wttr.in uses city, not nearest_area
- AT-7 ✅ compile clean

**b (weather publish to blender_state.json):**
- AT-0..AT-6 ✅ all 7 pass — weather key preserved, round-trip safe

**Note:** `test_wo030_weather_location.py` (v1) is stale — tests against `tool_router_test` module that no longer exists. Does not reflect current implementation. Replaced by v2 + b tests.

## Files

- `tools/tool_router.py` — location set detection, user_location.json persistence, ask-sentinel
- `blender_bridge/state_writer.py` — `_PRESERVE_KEYS` includes 'weather'
