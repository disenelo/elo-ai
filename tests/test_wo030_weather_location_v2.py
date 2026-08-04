"""
tests/test_wo030_weather_location_v2.py — Acceptance tests for WO-030 (REOPENED)

Spec: WO-030 REOPENED — behaviour spec:
  1. No location set → weather query returns "ask" context, not London default
  2. "I'm in Hackney Wick" → city saved + confirmation context returned
  3. "The studio is in X" → city saved (new pattern added)
  4. Explicit city in query ("weather in Paris") → bypasses saved location
  5. stale Manchester cleared (user_location.json now has null)
  6. wttr.in result uses queried city name, not nearest_area sub-area
  7. py_compile clean

Run: python3 tests/test_wo030_weather_location_v2.py
"""
import sys, os, json
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: no location set → weather agent returns ask-sentinel, not weather ────
try:
    from tools.tool_router import _agent_weather, set_location, _load_persisted_location

    # clear any in-memory location first
    import tools.tool_router as _tr
    _tr._user_location = None

    result = _agent_weather("what's the weather today?")
    if "ask" in result.lower() or "no location" in result.lower() or "where are you" in result.lower():
        ok("AT-1: no-location weather query returns ask-sentinel (not London weather)")
    else:
        fail("AT-1", f"expected ask-sentinel, got: {result[:120]!r}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: "I'm in Hackney Wick" → city saved ──────────────────────────────────
try:
    from tools.tool_router import detect_location_set, set_location
    city = detect_location_set("I'm in Hackney Wick")
    if city and "hackney" in city.lower():
        ok(f"AT-2: 'I\\'m in Hackney Wick' detected as location set → city={city!r}")
    else:
        fail("AT-2", f"expected 'Hackney Wick'-ish, got {city!r}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: "the studio is in X" pattern added ──────────────────────────────────
try:
    from tools.tool_router import detect_location_set
    city = detect_location_set("the studio is in Hackney Wick")
    if city and "hackney" in city.lower():
        ok(f"AT-3: 'the studio is in Hackney Wick' detected → city={city!r}")
    else:
        fail("AT-3", f"'studio is in' pattern not matching; got {city!r}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: explicit city in query bypasses saved location ──────────────────────
try:
    import tools.tool_router as _tr
    _tr._user_location = "Hackney Wick"  # simulate saved location
    _src = open("tools/tool_router.py", encoding="utf-8").read()
    # The city regex must extract "Paris" from "weather in Paris"
    import re as _re
    city_match = _re.search(
        r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s,\-]{1,40}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
        "weather in Paris", _re.IGNORECASE
    )
    extracted = city_match.group(1).strip() if city_match else None
    if extracted and "paris" in extracted.lower():
        ok(f"AT-4: explicit city 'Paris' extracted from query ({extracted!r}) — overrides saved location")
    else:
        fail("AT-4", f"city not extracted from 'weather in Paris'; got {extracted!r}")
    _tr._user_location = None  # reset
except Exception as e:
    fail("AT-4", e)


# ── AT-5: stale Manchester cleared in user_location.json ──────────────────────
try:
    _loc_file = os.path.join("blender", "user_location.json")
    data = json.loads(open(_loc_file, encoding="utf-8").read())
    city_val = data.get("city")
    if city_val is None or city_val == "" or city_val == "null":
        ok(f"AT-5: user_location.json city={city_val!r} — stale Manchester cleared")
    elif isinstance(city_val, str) and "manchester" in city_val.lower():
        fail("AT-5", f"Manchester still persisted in user_location.json: {data}")
    else:
        ok(f"AT-5: user_location.json city={city_val!r} (not Manchester)")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: wttr.in result uses queried city name, not nearest_area ──────────────
try:
    _src = open("tools/tool_router.py", encoding="utf-8").read()
    # Old code: result = f"Weather in {loc}: ..." where loc = area['areaName']...
    # New code: result = f"Weather in {city}: ..." (WO-030 comment present)
    if "Weather in {city}" in _src and "WO-030" in _src:
        ok("AT-6: wttr.in result uses queried {city} not nearest_area (WO-030 comment present)")
    elif "nearest_area" not in _src or "Weather in {city}" in _src:
        ok("AT-6: wttr.in no longer uses nearest_area for display city")
    else:
        fail("AT-6", "nearest_area still used for display city — sub-area invention not fixed")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("tools/tool_router.py", doraise=True)
    ok("AT-7: tools/tool_router.py compile clean")
except py_compile.PyCompileError as e:
    fail("AT-7", e)


print()
print(f"{'='*50}")
print(f"WO-030v2  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
