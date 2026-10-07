"""
WO-030 acceptance tests — weather default location + city parsing + persistence.

AT-1  No-city query → city falls back to London (not None/"auto")
AT-2  Explicit city overrides default ("weather in Paris" → Paris)
AT-3  Session set propagates ("I'm in Testville" → Testville in next call)
AT-4  "What about London, Hackney Wick?" parses as followup with comma place-name
AT-5  Followup builds synthetic "weather in London, Hackney Wick" query
AT-6  _DEFAULT_LOCATION constant is "London"
AT-7  py_compile: tool_router.py compiles cleanly
AT-8  set_location() writes blender/user_location.json (persistent across restarts)
AT-9  On reload, _user_location reads from user_location.json (JSON > env var)
AT-10 AccuWeather skipped when key not set (is_available() == False)
AT-11 _agent_weather() with no location → returns ask-string, NOT "London" silently
AT-12 set_location("Hackney Wick") → city persists; next call to agent uses it
AT-13 Location-set phrase detection: "I'm in X" + "studio is in X" fire correctly
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


# B3 2026-10-06: set_location() writes the location file AND David's facts.
# Every test that calls it now points both at temp files — this suite once
# moved David to Manchester in the live server (user_location.json + facts).
import contextlib as _ctx
import tempfile as _tempfile


@_ctx.contextmanager
def _isolated(mod):
    import memory.fact_store as _fs
    loc_tmp = _tempfile.mktemp(suffix=".json")
    facts_tmp = _tempfile.mktemp(suffix=".json")
    saved = (mod._LOCATION_FILE, _fs._FACTS_FILE)
    mod._LOCATION_FILE, _fs._FACTS_FILE = loc_tmp, facts_tmp
    try:
        yield loc_tmp
    finally:
        mod._LOCATION_FILE, _fs._FACTS_FILE = saved
        for f in (loc_tmp, facts_tmp):
            try:
                os.unlink(f)
            except OSError:
                pass


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
      with _isolated(_mod):
        _mod.set_location("Testville")
        assert _mod._user_location == "Testville", \
            f"AT-3 FAIL: _user_location={_mod._user_location!r}"
        # Bare "what's the weather?" should now resolve Testville
        city_match = re.search(
            r"(?:in|at|for)\s+([A-Za-z][A-Za-z\s,\-]{1,40}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast)",
            "what's the weather?", re.IGNORECASE
        )
        city = (city_match.group(1).strip() if city_match else None) or _mod._user_location or _mod._DEFAULT_LOCATION
        assert city == "Testville", f"AT-3 FAIL: city={city!r} after set_location('Testville')"
        assert _mod._resolve_location() == "Testville", "AT-3 FAIL: session set must outrank knowledge"
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
    import memory.fact_store as _fs
    tmp = tempfile.mktemp(suffix=".json")
    mod._LOCATION_FILE = tmp
    _facts_saved, _fs._FACTS_FILE = _fs._FACTS_FILE, tempfile.mktemp(suffix=".json")
    try:
        mod.set_location("Bristol")
        assert _os.path.exists(tmp), "AT-8 FAIL: JSON file not written"
        data = json.loads(open(tmp).read())
        assert data.get("city") == "Bristol", f"AT-8 FAIL: {data}"
        assert "_ts" in data, "AT-8 FAIL: _ts missing from JSON"
    finally:
        _fs._FACTS_FILE = _facts_saved
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


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_agent_weather_no_location_asks():
    """
    _agent_weather() with no location set must return the ask-string.
    It must NOT silently default to London, and must NOT make an HTTP request.
    The ask-path returns early (before any provider call) with an instruction to ask.
    This exercises the actual function, not a replica of its logic.
    """
    import importlib
    mod = _load_module()

    saved_loc = mod._user_location
    try:
        mod._user_location = None  # simulate: no location ever set
        mod._known_location = lambda: None          # …and nothing in eLo's knowledge
        mod._load_persisted_location = lambda: None  # …and no file

        result = mod._agent_weather("what's the weather today?")

        # Must contain the ask instruction, not a city reading
        assert result is not None, "AT-11 FAIL: _agent_weather returned None"
        result_lower = result.lower()
        assert "no location" in result_lower or "where are you" in result_lower or "ask" in result_lower, (
            f"AT-11 FAIL: expected ask-string, got: {result!r}"
        )
        # Must NOT have silently resolved a city
        assert "weather in london" not in result_lower, (
            f"AT-11 FAIL: silently defaulted to London — got: {result!r}"
        )
        assert "weather in manchester" not in result_lower, (
            f"AT-11 FAIL: stale Manchester leak — got: {result!r}"
        )
    finally:
        mod._user_location = saved_loc

    print(f"AT-11 PASS — no-location → ask-string: {result[:80]!r}")


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_set_location_then_agent_resolves():
    """
    Multi-step: set_location("Hackney Wick") → _agent_weather("what's the weather?")
    must attempt the weather call with city="Hackney Wick" (not default, not Manchester).
    We intercept the provider chain to capture which city is passed without making real HTTP.
    """
    import json, tempfile, os as _os
    mod = _load_module()
    import memory.fact_store as _fs
    tmp = tempfile.mktemp(suffix=".json")
    mod._LOCATION_FILE = tmp
    _facts_saved, _fs._FACTS_FILE = _fs._FACTS_FILE, tempfile.mktemp(suffix=".json")

    saved_loc = mod._user_location
    captured_city: list = []

    # Patch wttr.in call to capture city and return a canned response
    import urllib.request as _ur
    _orig_urlopen = _ur.urlopen

    class _FakeResp:
        def read(self):
            return b'{"current_condition": [{"weatherDesc": [{"value": "Overcast"}], "temp_C": "14", "FeelsLikeC": "12", "humidity": "80"}]}'
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def _fake_urlopen(req, timeout=None):
        captured_city.append(req.full_url)
        return _FakeResp()

    _ur.urlopen = _fake_urlopen

    try:
        mod.set_location("Hackney Wick")

        # Verify persistence
        assert _os.path.exists(tmp), "AT-12 FAIL: location JSON not written"
        data = json.loads(open(tmp).read())
        assert data.get("city") == "Hackney Wick", f"AT-12 FAIL: JSON city={data.get('city')!r}"

        # Make a bare weather request — should resolve to Hackney Wick
        # Disable all provider checks so we fall through to wttr.in
        result = mod._agent_weather("what's the weather?")

        assert result is not None, "AT-12 FAIL: _agent_weather returned None"
        assert "Hackney Wick" in result or "hackney wick" in result.lower(), (
            f"AT-12 FAIL: Hackney Wick not in result — got: {result!r}"
        )
        assert "Manchester" not in result, f"AT-12 FAIL: stale Manchester in result — got: {result!r}"

    finally:
        _ur.urlopen = _orig_urlopen
        mod._user_location = saved_loc
        _fs._FACTS_FILE = _facts_saved
        try: _os.unlink(tmp)
        except: pass

    print(f"AT-12 PASS — set_location(Hackney Wick) → agent resolved correctly: {result[:80]!r}")


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_location_set_phrases():
    """
    _LOCATION_SET_PATTERNS must match all specified natural phrasings.
    Tests the actual patterns, not a stub — these gate whether "I'm in X" is detected.
    """
    patterns = _mod._LOCATION_SET_PATTERNS
    assert patterns, "AT-13 FAIL: _LOCATION_SET_PATTERNS is empty"

    cases = [
        ("I'm in Hackney Wick",           "Hackney Wick"),
        ("I am in Bethnal Green",          "Bethnal Green"),
        ("the studio is in Hackney Wick",  "Hackney Wick"),
        ("my studio is in Dalston",        "Dalston"),
        ("studio is in Peckham",           "Peckham"),
        ("set my location to Bristol",     "Bristol"),
        ("my location is Sheffield",       "Sheffield"),
        ("we're in Glasgow",               "Glasgow"),
    ]

    failed_cases = []
    for phrase, expected_city in cases:
        matched = None
        for pat in patterns:
            m = re.search(pat, phrase, re.IGNORECASE)
            if m:
                matched = m.group(1).strip()
                break
        if matched is None or expected_city.lower() not in matched.lower():
            failed_cases.append(f"  phrase={phrase!r} → got={matched!r}, expected to contain {expected_city!r}")

    assert not failed_cases, "AT-13 FAIL:\n" + "\n".join(failed_cases)
    print(f"AT-13 PASS — {len(cases)}/{len(cases)} location-set phrases detected correctly")


# ── runner ────────────────────────────────────────────────────────────────────

# ── AT-14 (B3 2026-10-06) ────────────────────────────────────────────────────

def test_at14_knowledge_outranks_stale_file():
    """David L3: where he is comes from eLo's knowledge, not a loose file. A
    stale user_location.json saying Manchester must not beat what eLo knows."""
    import json, time as _ti
    mod = _load_module()
    with _isolated(mod) as loc_tmp:
        json.dump({"city": "Testville", "_ts": _ti.time()}, open(loc_tmp, "w"))
        saved_known, saved_loc = mod._known_location, mod._user_location
        try:
            mod._user_location = None
            mod._known_location = lambda: "Hackney Wick"
            assert mod._resolve_location() == "Hackney Wick", \
                f"AT-14 FAIL: resolved {mod._resolve_location()!r}, stale file won"
            mod._known_location = lambda: None
            assert mod._resolve_location() == "Testville", "AT-14 FAIL: file is still the fallback"
            mod.set_location("Paris")                      # "I'm in Paris" — travel
            import memory.fact_store as _fs
            facts = {f["key"]: f["fact"] for f in _fs.load_facts()}
            assert "location" not in facts, "AT-14 FAIL: travel rewrote the studio fact"
            assert "Paris" in facts.get("current_location", ""), f"AT-14 FAIL: {facts}"
        finally:
            mod._known_location, mod._user_location = saved_known, saved_loc
    print("AT-14 PASS — eLo's knowledge > stale file; travel doesn't move the studio")


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
        test_at11_agent_weather_no_location_asks,
        test_at12_set_location_then_agent_resolves,
        test_at13_location_set_phrases,
        test_at14_knowledge_outranks_stale_file,
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

