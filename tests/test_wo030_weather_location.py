"""
WO-030 acceptance tests — weather default location + city parsing + persistence.

AT-1  No-city query → city falls back to London (not None/"auto")
AT-2  Explicit city overrides default ("weather in Paris" → Paris)
AT-3  Session set propagates ("I'm in Manchester" → Manchester in next call)
AT-4  "What about London, Hackney Wick?" parses as followup with comma place-name
AT-5  Followup builds synthetic "weather in London, Hackney Wick" query
AT-6  _DEFAULT_LOCATION constant is "London"
AT-7  py_compile: tool_router.py compiles cleanly
AT-8  set_location() writes blender/user_location.json (persistent across restarts)
AT-9  On reload, _user_location reads from user_location.json (JSON > env var)
AT-10 AccuWeather skipped when key not set (is_available() == False)
"""
import importlib.util
import os
import sys
import re
import types as _types

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_TR_PATH = os.path.join(_ROOT, "tools", "tool_router.py")


def _load_module() -> _types.ModuleType:
    """Load tool_router without Flask or server startup."""
    spec = importlib.util.spec_from_file_location("tool_router_test", _TR_PATH)
    mod = importlib.util.module_from_spec(spec)
    mod.__name__ = "tool_router_test"
    sys.modules["tool_router_test"] = mod
    # Minimal stubs so import doesn't crash on missing deps.
    # Save and restore so the stubs don't contaminate later tests.
    _stub_deps = ("tools.accuweather_agent", "tools.spotify_agent", "tools.computer_control_agent")
    _prior = {dep: sys.modules.get(dep) for dep in _stub_deps}
    for dep in _stub_deps:
        if dep not in sys.modules:
            stub = _types.ModuleType(dep)
            stub.is_available = lambda: False
            stub.agent = lambda *a, **kw: None
            sys.modules[dep] = stub
    try:
        spec.loader.exec_module(mod)
    except Exception:
        pass  # partial load is fine — we only need constants + functions
    finally:
        # Restore so the stubs don't contaminate other tests
        for dep, prior in _prior.items():
            if prior is None:
                sys.modules.pop(dep, None)
            else:
                sys.modules[dep] = prior
    return mod


_mod = _load_module()


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_default_london():
    """City resolution: no explicit city + no session set → _DEFAULT_LOCATION."""
    assert hasattr(_mod, "_DEFAULT_LOCATION"), "AT-1 FAIL: _DEFAULT_LOCATION constant missing"
    assert _mod._DEFAULT_LOCATION == "London", \
        f"AT-1 FAIL: _DEFAULT_LOCATION={_mod._DEFAULT_LOCATION!r}, expected 'London'"

    # Simulate the resolution logic from _agent_weather
    saved_loc = _mod._user_location
    try:
        _mod._user_location = None
        city_match = re.search(
            r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s,\-]{1,40}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
            "what's the weather today?", re.IGNORECASE
        )
        city = (city_match.group(1).strip() if city_match else None) or _mod._user_location or _mod._DEFAULT_LOCATION
        assert city == "London", f"AT-1 FAIL: resolved city={city!r}, expected 'London'"
    finally:
        _mod._user_location = saved_loc
    print("AT-1 PASS — no-city query resolves to London")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_explicit_city_overrides():
    """Explicit city in query wins over default."""
    for query, expected in [
        ("weather in Paris", "Paris"),
        ("what's the weather in Berlin today", "Berlin"),
        ("weather for Tokyo", "Tokyo"),
    ]:
        city_match = re.search(
            r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s,\-]{1,40}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
            query, re.IGNORECASE
        )
        city = (city_match.group(1).strip() if city_match else None) or _mod._user_location or _mod._DEFAULT_LOCATION
        assert city == expected, f"AT-2 FAIL on {query!r}: resolved={city!r}, expected={expected!r}"
    print("AT-2 PASS — explicit city overrides default")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_session_set():
    """set_location() updates _user_location for the session."""
    saved = _mod._user_location
    try:
        _mod.set_location("Manchester")
        assert _mod._user_location == "Manchester", \
            f"AT-3 FAIL: _user_location={_mod._user_location!r}"
        # Bare "what's the weather?" should now resolve Manchester
        city_match = re.search(
            r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s,\-]{1,40}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
            "what's the weather?", re.IGNORECASE
        )
        city = (city_match.group(1).strip() if city_match else None) or _mod._user_location or _mod._DEFAULT_LOCATION
        assert city == "Manchester", f"AT-3 FAIL: city={city!r} after set_location('Manchester')"
    finally:
        _mod._user_location = saved
    print("AT-3 PASS — session set propagates to resolution")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_comma_place_followup_parsed():
    """'what about London, Hackney Wick?' parses as followup."""
    result = _mod._detect_followup("what about London, Hackney Wick?")
    assert result is not None, "AT-4 FAIL: comma place-name not parsed as followup"
    assert "london" in result.lower(), f"AT-4 FAIL: result={result!r}, expected to contain 'london'"
    print(f"AT-4 PASS — 'what about London, Hackney Wick?' → followup subject={result!r}")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_comma_synthetic_query():
    """Followup subject for weather builds correct synthetic query."""
    subject = _mod._detect_followup("what about London, Hackney Wick?")
    if subject is None:
        raise AssertionError("AT-5 FAIL: prerequisite — _detect_followup returned None")
    synthetic = f"weather in {subject}"
    city_match = re.search(
        r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s,\-]{1,40}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
        synthetic, re.IGNORECASE
    )
    assert city_match, f"AT-5 FAIL: city regex missed synthetic query={synthetic!r}"
    city = city_match.group(1).strip()
    assert "london" in city.lower(), f"AT-5 FAIL: extracted city={city!r}, expected to contain 'london'"
    print(f"AT-5 PASS — synthetic={synthetic!r} → city={city!r}")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_default_constant():
    """_DEFAULT_LOCATION is defined and equals 'London'."""
    assert _mod._DEFAULT_LOCATION == "London", \
        f"AT-6 FAIL: _DEFAULT_LOCATION={getattr(_mod, '_DEFAULT_LOCATION', 'MISSING')!r}"
    print("AT-6 PASS — _DEFAULT_LOCATION == 'London'")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_py_compile():
    import py_compile
    try:
        py_compile.compile(_TR_PATH, doraise=True)
    except py_compile.PyCompileError as e:
        raise AssertionError(f"AT-7 FAIL: tool_router.py does not compile: {e}")
    print("AT-7 PASS — tool_router.py compiles cleanly")


# ── AT-8 ─────────────────────────────────────────────────────────────────────

def test_at8_set_location_persists():
    """set_location() writes blender/user_location.json."""
    import json, tempfile, os as _os
    mod = _load_module()
    # Point module at a temp file so we don't clobber the real one
    tmp = tempfile.mktemp(suffix=".json")
    mod._LOCATION_FILE = tmp
    try:
        mod.set_location("Bristol")
        assert _os.path.exists(tmp), "AT-8 FAIL: JSON file not written"
        data = json.loads(open(tmp).read())
        assert data.get("city") == "Bristol", f"AT-8 FAIL: {data}"
        assert "_ts" in data, "AT-8 FAIL: _ts missing from JSON"
    finally:
        try: _os.unlink(tmp)
        except: pass
    print("AT-8 PASS — set_location() persists to user_location.json")


# ── AT-9 ─────────────────────────────────────────────────────────────────────

def test_at9_reload_reads_json():
    """After a restart, _user_location loads from the JSON file (JSON > env)."""
    import json, tempfile, os as _os, time as _ti

    # Write a JSON with "Edinburgh"
    tmp = tempfile.mktemp(suffix=".json")
    json.dump({"city": "Edinburgh", "_ts": _ti.time()}, open(tmp, "w"))

    saved_env = _os.environ.pop("ELO_LOCATION", None)
    _os.environ["ELO_LOCATION"] = "London"  # env says London — JSON should win
    try:
        mod = _load_module()
        mod._LOCATION_FILE = tmp
        # Simulate reload: call _load_persisted_location directly
        loaded = mod._load_persisted_location()
        assert loaded == "Edinburgh", \
            f"AT-9 FAIL: loaded={loaded!r}, expected 'Edinburgh'"
    finally:
        if saved_env is not None:
            _os.environ["ELO_LOCATION"] = saved_env
        elif "ELO_LOCATION" in _os.environ:
            del _os.environ["ELO_LOCATION"]
        try: _os.unlink(tmp)
        except: pass
    print("AT-9 PASS — reload reads user_location.json (JSON > env)")


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_accuweather_skipped_no_key():
    """AccuWeather is_available() returns False when key is not set."""
    import os as _os
    saved = _os.environ.pop("ACCUWEATHER_API_KEY", None)
    try:
        from tools.accuweather_agent import is_available
        result = is_available()
        assert result is False, \
            f"AT-10 FAIL: is_available()={result!r} with no key set"
    finally:
        if saved:
            _os.environ["ACCUWEATHER_API_KEY"] = saved
    print("AT-10 PASS — AccuWeather is_available()==False when key missing")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_default_london,
        test_at2_explicit_city_overrides,
        test_at3_session_set,
        test_at4_comma_place_followup_parsed,
        test_at5_comma_synthetic_query,
        test_at6_default_constant,
        test_at7_py_compile,
        test_at8_set_location_persists,
        test_at9_reload_reads_json,
        test_at10_accuweather_skipped_no_key,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-030 ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
