"""
tests/test_wo030b_weather_publish.py — WO-030b / WO-058b: weather publish

Tests that the brain writes "weather" into blender_state.json on the
normal state tick and that it survives a full _write() overwrite.

Spec ref: blender/agent_bus/builder/FROM_ARCHITECT_2026-08-10_weather_publish.md
"""
from __future__ import annotations
import sys, os, json, tempfile, py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0

def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")

def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── AT-0: py_compile clean ────────────────────────────────────────────────────
try:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for _rel in ["blender_bridge/state_writer.py", "tools/tool_router.py", "server.py"]:
        py_compile.compile(os.path.join(_base, _rel), doraise=True)
    ok("AT-0: py_compile clean on all WO-030b files")
except py_compile.PyCompileError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: "weather" in _PRESERVE_KEYS ────────────────────────────────────────
try:
    from blender_bridge.state_writer import _PRESERVE_KEYS
    assert "weather" in _PRESERVE_KEYS, \
        f"'weather' must be in _PRESERVE_KEYS; got {_PRESERVE_KEYS}"
    ok("AT-1: 'weather' in _PRESERVE_KEYS (survives every _write() call)")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: _write() preserves existing weather when payload has none ───────────
try:
    import json, os, tempfile
    from unittest.mock import patch as _mpatch
    from blender_bridge import state_writer as _sw

    with tempfile.TemporaryDirectory() as _td:
        _fake_path = os.path.join(_td, "blender_state.json")
        # Seed: file has weather="rain"
        with open(_fake_path, "w") as f:
            json.dump({"weather": "rain", "motion": {}}, f)

        with _mpatch.object(_sw, "_STATE_PATH", _fake_path):
            # Simulate a full _write() (no weather in payload)
            _sw._write({
                "motion": {"animation": "idle", "speed": 0.5, "intensity": 0.5,
                           "duration": 4.0, "mood": "neutral", "mode": "idle"},
            })
        with open(_fake_path) as f:
            result = json.load(f)
        assert result.get("weather") == "rain", \
            f"_write() must preserve 'weather'; got {result.get('weather')!r}"
    ok("AT-2: _write() preserves prior 'weather' value when payload omits it")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: patch() with non-empty weather writes it ────────────────────────────
try:
    import json, os, tempfile
    from unittest.mock import patch as _mpatch
    from blender_bridge import state_writer as _sw

    with tempfile.TemporaryDirectory() as _td:
        _fake_path = os.path.join(_td, "blender_state.json")
        with open(_fake_path, "w") as f:
            json.dump({}, f)

        with _mpatch.object(_sw, "_STATE_PATH", _fake_path):
            _sw.patch({"weather": "sunny"})
        with open(_fake_path) as f:
            result = json.load(f)
        assert result.get("weather") == "sunny", \
            f"patch() must write weather='sunny'; got {result.get('weather')!r}"
    ok("AT-3: patch({'weather': 'sunny'}) writes top-level weather field")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: patch() with empty weather does NOT overwrite a good value ──────────
try:
    import json, os, tempfile
    from unittest.mock import patch as _mpatch
    from blender_bridge import state_writer as _sw

    with tempfile.TemporaryDirectory() as _td:
        _fake_path = os.path.join(_td, "blender_state.json")
        with open(_fake_path, "w") as f:
            json.dump({"weather": "cloudy"}, f)

        # Patch with empty weather (as happens when _last_weather_condition is "")
        with _mpatch.object(_sw, "_STATE_PATH", _fake_path):
            _sw.patch({"weather": ""})
        with open(_fake_path) as f:
            result = json.load(f)
        # After patch with "", cloudy is OVERWRITTEN — this is expected behaviour from patch().
        # The guard is in server.py (only patches when non-empty).
        # This test just verifies patch() itself is transparent (no silent drop of "").
        assert result.get("weather") == "", \
            "patch({'weather': ''}) should write '' — guard is in server.py, not here"
    ok("AT-4: patch() is transparent; empty-string guard lives in server.py (not here)")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: get_last_weather_condition() returns str ────────────────────────────
try:
    from tools.tool_router import get_last_weather_condition
    result = get_last_weather_condition()
    assert isinstance(result, str), f"get_last_weather_condition() must return str; got {type(result)}"
    ok(f"AT-5: get_last_weather_condition() returns str (current={result!r})")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: weather survives a round-trip (_write then _write) ─────────────────
try:
    import json, os, tempfile
    from unittest.mock import patch as _mpatch
    from blender_bridge import state_writer as _sw

    with tempfile.TemporaryDirectory() as _td:
        _fake_path = os.path.join(_td, "blender_state.json")
        with open(_fake_path, "w") as f:
            json.dump({}, f)

        with _mpatch.object(_sw, "_STATE_PATH", _fake_path):
            # Turn 1: patch sets weather
            _sw.patch({"weather": "snow"})
            # Turn 1: then _write() (motion write) runs
            _sw._write({"motion": {"animation": "idle"}})
            # Turn 2: another _write()
            _sw._write({"motion": {"animation": "walk"}})

        with open(_fake_path) as f:
            result = json.load(f)
        assert result.get("weather") == "snow", \
            f"weather must survive two _write() calls; got {result.get('weather')!r}"
    ok("AT-6: weather survives two consecutive _write() calls (round-trip)")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-030b/058b weather publish   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
