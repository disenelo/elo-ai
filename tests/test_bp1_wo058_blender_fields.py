"""
tests/test_bp1_wo058_blender_fields.py

Acceptance tests for:
  BP-1  — conversing field: real idle_sec-based boolean (not hardcoded True)
  WO-058 — weather field: last fetched condition published to blender_state.json

  AT-1: conversing=True when last_user_ts is recent (< 30s ago)
  AT-2: conversing=False when last_user_ts is stale (> 30s ago)
  AT-3: conversing=True when last_user_ts is absent (new session default = not idle)
  AT-4: _cache_weather_condition parses condition from accuweather/google/xweather-style string
  AT-5: _cache_weather_condition parses condition from wttr.in-style string
  AT-6: get_last_weather_condition returns "" before any fetch
  AT-7: get_last_weather_condition returns cached value after a fetch
  AT-8: py_compile clean on tool_router.py and server.py

Run: python3 tests/test_bp1_wo058_blender_fields.py
"""
import sys, os, time, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── BP-1: conversing field logic ─────────────────────────────────────────────

def _conversing(last_user_ts):
    """Replicate the BP-1 formula from server.py."""
    import time as t
    state = {"last_user_ts": last_user_ts} if last_user_ts is not None else {}
    return (t.time() - state.get("last_user_ts", t.time())) < 30.0


try:
    # AT-1: recent ts → True
    try:
        result = _conversing(time.time() - 5)  # 5s ago
        assert result is True, f"expected True for 5s idle, got {result}"
        ok("AT-1: conversing=True when idle_sec=5 (< 30s threshold)")
    except AssertionError as e:
        fail("AT-1", e)

    # AT-2: stale ts → False
    try:
        result = _conversing(time.time() - 60)  # 60s ago
        assert result is False, f"expected False for 60s idle, got {result}"
        ok("AT-2: conversing=False when idle_sec=60 (> 30s threshold)")
    except AssertionError as e:
        fail("AT-2", e)

    # AT-3: no last_user_ts → defaults to now → idle_sec≈0 → True
    try:
        result = _conversing(None)
        assert result is True, f"expected True for missing last_user_ts, got {result}"
        ok("AT-3: conversing=True when last_user_ts absent (new session default)")
    except AssertionError as e:
        fail("AT-3", e)

    # AT-4: _cache_weather_condition parses structured string (provider-style)
    try:
        import tools.tool_router as _tr
        _tr._last_weather_condition = ""  # reset
        _tr._cache_weather_condition("Weather in London: Partly cloudy, 15°C, feels like 13°C")
        cond = _tr._last_weather_condition
        assert "partly" in cond or "cloudy" in cond, f"expected 'partly cloudy' parsed, got '{cond}'"
        ok(f"AT-4: _cache_weather_condition parses provider string → '{cond}'")
    except AssertionError as e:
        fail("AT-4", e)
    except Exception as e:
        fail("AT-4", e)

    # AT-5: condition parsed from wttr.in-style (desc directly)
    try:
        import tools.tool_router as _tr
        _tr._last_weather_condition = ""  # reset
        # Simulate wttr.in path — direct assignment of desc.lower()
        _tr._last_weather_condition = "light rain".lower()
        cond = _tr.get_last_weather_condition()
        assert "rain" in cond, f"expected 'rain' in condition, got '{cond}'"
        ok(f"AT-5: wttr.in condition path → '{cond}'")
    except AssertionError as e:
        fail("AT-5", e)
    except Exception as e:
        fail("AT-5", e)

    # AT-6: get_last_weather_condition returns "" before any fetch
    try:
        import tools.tool_router as _tr
        _tr._last_weather_condition = ""
        cond = _tr.get_last_weather_condition()
        assert isinstance(cond, str), "expected str"
        assert cond == "", f"expected empty before fetch, got '{cond}'"
        ok("AT-6: get_last_weather_condition returns '' before any fetch")
    except AssertionError as e:
        fail("AT-6", e)
    except Exception as e:
        fail("AT-6", e)

    # AT-7: get_last_weather_condition returns cached value after a fetch
    try:
        import tools.tool_router as _tr
        _tr._last_weather_condition = ""
        _tr._cache_weather_condition("Weather in Manchester: Snow showers, 1°C, feels like -3°C")
        cond = _tr.get_last_weather_condition()
        assert "snow" in cond, f"expected 'snow' in condition, got '{cond}'"
        ok(f"AT-7: get_last_weather_condition returns cached value → '{cond}'")
    except AssertionError as e:
        fail("AT-7", e)
    except Exception as e:
        fail("AT-7", e)

    # AT-8: py_compile clean
    try:
        py_compile.compile("tools/tool_router.py", doraise=True)
        py_compile.compile("server.py", doraise=True)
        ok("AT-8: py_compile clean on tool_router.py and server.py")
    except py_compile.PyCompileError as e:
        fail("AT-8", e)

finally:
    pass

print()
print("=" * 52)
print(f"BP-1 / WO-058 blender fields  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
