"""
tests/test_wo018_capability_gate.py — Acceptance tests for WO-018

Spec: DISPATCH_BOARD §WO-018
Make tool_router.enrich() check registry.all_enabled() before dispatching any
agent, so a capability disabled in the registry can't fire via router patterns.

6 tests:
    AT-1  disabled capability → not dispatched (normal intent path)
    AT-2  enabled capability → dispatched normally
    AT-3  pipeline path → disabled capability skipped, enabled one runs
    AT-4  follow-up path → disabled capability not re-run
    AT-5  registry unavailable → fail-open (agent still runs)
    AT-6  _ROUTER_TO_CAP_ID covers all _AGENTS keys

Run: python3 tests/test_wo018_capability_gate.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


import tools.tool_router as _tr
import runtime.capabilities.registry as _reg


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_cap(cap_id, enabled=True):
    """Minimal Capability-like object for mocking all_enabled()."""
    class _C:
        id = cap_id
    return _C()


def _pipeline_fallthrough(_input):
    """Mock pipeline that returns nothing, so enrich falls through to intent."""
    return {}


def _gate_no_pending():
    return False


# ── AT-1: disabled capability → not dispatched (normal intent path) ───────────

_weather_calls_1 = []

def _fake_weather_1(q):
    _weather_calls_1.append(q)
    return "London: sunny"

_real_weather = _tr._AGENTS.get("weather")
_real_detect  = _tr._detect_intent

# Patch: pipeline falls through, detect_intent returns "weather", "weather" disabled
_tr._AGENTS["weather"] = _fake_weather_1

import runtime.router.pipeline as _pipeline_mod
_real_pipeline_run = _pipeline_mod.run
_pipeline_mod.run = _pipeline_fallthrough

import runtime.router.execution_gate as _gate_mod
_real_has_pending = _gate_mod.has_pending
_gate_mod.has_pending = _gate_no_pending

_reg.all_enabled = lambda: [_make_cap("time"), _make_cap("calculator")]  # weather NOT enabled
_tr._detect_intent = lambda _: "weather"

result_1 = _tr.enrich("what's the weather")

# Restore
_tr._AGENTS["weather"] = _real_weather
_pipeline_mod.run     = _real_pipeline_run
_gate_mod.has_pending = _real_has_pending
_tr._detect_intent    = _real_detect
_reg.all_enabled      = _reg.__dict__.get("_real_all_enabled", _reg.all_enabled)

try:
    assert len(_weather_calls_1) == 0, f"weather agent called despite being disabled: {_weather_calls_1}"
    assert result_1[0] == "what's the weather", f"input should pass through unmodified: {result_1[0]!r}"
    assert result_1[1] is None, f"agent name should be None: {result_1[1]!r}"
    ok("AT-1: disabled capability skipped — normal intent path")
except AssertionError as e: fail("AT-1", e)


# ── AT-2: enabled capability → dispatched normally ────────────────────────────

_weather_calls_2 = []

def _fake_weather_2(q):
    _weather_calls_2.append(q)
    return "London: cloudy"

_real_weather = _tr._AGENTS.get("weather")

_tr._AGENTS["weather"] = _fake_weather_2
_pipeline_mod.run     = _pipeline_fallthrough
_gate_mod.has_pending = _gate_no_pending
_reg.all_enabled      = lambda: [_make_cap("weather"), _make_cap("time")]  # weather enabled
_tr._detect_intent    = lambda _: "weather"

result_2 = _tr.enrich("what's the weather")

_tr._AGENTS["weather"] = _real_weather
_pipeline_mod.run     = _real_pipeline_run
_gate_mod.has_pending = _real_has_pending
_tr._detect_intent    = _real_detect
_reg.all_enabled      = _reg.__dict__.get("_real_all_enabled", _reg.all_enabled)

try:
    assert len(_weather_calls_2) == 1, f"weather agent should have been called once: {_weather_calls_2}"
    assert "CONTEXT" in result_2[0], f"enriched context expected: {result_2[0]!r}"
    assert result_2[1] == "weather", f"agent name should be 'weather': {result_2[1]!r}"
    ok("AT-2: enabled capability dispatched normally")
except AssertionError as e: fail("AT-2", e)


# ── AT-3: pipeline path → disabled capability skipped, enabled one runs ───────

_news_calls_3    = []
_weather_calls_3 = []

def _fake_news_3(q):
    _news_calls_3.append(q)
    return "Top news here"

def _fake_weather_3(q):
    _weather_calls_3.append(q)
    return "London: sunny"

_real_news    = _tr._AGENTS.get("news")
_real_weather = _tr._AGENTS.get("weather")

_tr._AGENTS["news"]    = _fake_news_3
_tr._AGENTS["weather"] = _fake_weather_3
_gate_mod.has_pending  = _gate_no_pending

# news disabled, weather enabled
_reg.all_enabled = lambda: [_make_cap("weather")]

# Pipeline selects both news AND weather
_pipeline_mod.run = lambda _: {"agents": [("news", ""), ("weather", "london")]}

result_3 = _tr.enrich("news and weather please")

_tr._AGENTS["news"]    = _real_news
_tr._AGENTS["weather"] = _real_weather
_pipeline_mod.run      = _real_pipeline_run
_gate_mod.has_pending  = _real_has_pending
_reg.all_enabled       = _reg.__dict__.get("_real_all_enabled", _reg.all_enabled)

try:
    assert len(_news_calls_3)    == 0, f"news called despite disabled: {_news_calls_3}"
    assert len(_weather_calls_3) == 1, f"weather should have run once: {_weather_calls_3}"
    ok("AT-3: pipeline path — disabled agent skipped, enabled one runs")
except AssertionError as e: fail("AT-3", e)


# ── AT-4: follow-up path → disabled capability not re-run ────────────────────

_weather_calls_4 = []

def _fake_weather_4(q):
    _weather_calls_4.append(q)
    return "Paris: rainy"

_real_weather       = _tr._AGENTS.get("weather")
_real_last_agent    = _tr._last_agent
_real_last_arg      = _tr._last_arg
_real_detect_fu     = _tr._detect_followup

_tr._AGENTS["weather"] = _fake_weather_4
_tr._last_agent        = "weather"
_tr._last_arg          = "london"
_tr._detect_followup   = lambda _: "paris"
_gate_mod.has_pending  = _gate_no_pending
_reg.all_enabled       = lambda: [_make_cap("time")]  # weather NOT enabled

# pipeline returns nothing so follow-up block is reached
_pipeline_mod.run = lambda _: {}

result_4 = _tr.enrich("what about paris")

_tr._AGENTS["weather"] = _real_weather
_tr._last_agent        = _real_last_agent
_tr._last_arg          = _real_last_arg
_tr._detect_followup   = _real_detect_fu
_pipeline_mod.run      = _real_pipeline_run
_gate_mod.has_pending  = _real_has_pending
_reg.all_enabled       = _reg.__dict__.get("_real_all_enabled", _reg.all_enabled)

try:
    assert len(_weather_calls_4) == 0, f"weather called despite disabled: {_weather_calls_4}"
    ok("AT-4: follow-up path — disabled capability not re-run")
except AssertionError as e: fail("AT-4", e)


# ── AT-5: registry unavailable → fail-open (agent still runs) ────────────────

_weather_calls_5 = []

def _fake_weather_5(q):
    _weather_calls_5.append(q)
    return "Tokyo: clear"

_real_weather = _tr._AGENTS.get("weather")

_tr._AGENTS["weather"] = _fake_weather_5
_pipeline_mod.run     = _pipeline_fallthrough
_gate_mod.has_pending = _gate_no_pending
_reg.all_enabled      = lambda: (_ for _ in ()).throw(RuntimeError("registry exploded"))
_tr._detect_intent    = lambda _: "weather"

result_5 = _tr.enrich("weather please")

_tr._AGENTS["weather"] = _real_weather
_pipeline_mod.run      = _real_pipeline_run
_gate_mod.has_pending  = _real_has_pending
_tr._detect_intent     = _real_detect
_reg.all_enabled       = _reg.__dict__.get("_real_all_enabled", _reg.all_enabled)

try:
    assert len(_weather_calls_5) == 1, f"weather should have run (fail-open): {_weather_calls_5}"
    ok("AT-5: registry unavailable → fail-open, agent still runs")
except AssertionError as e: fail("AT-5", e)


# ── AT-6: _ROUTER_TO_CAP_ID covers all _AGENTS keys ─────────────────────────

_missing = [k for k in _tr._AGENTS if k not in _tr._ROUTER_TO_CAP_ID]

try:
    assert not _missing, f"_AGENTS keys not in _ROUTER_TO_CAP_ID: {_missing}"
    ok(f"AT-6: _ROUTER_TO_CAP_ID covers all {len(_tr._AGENTS)} _AGENTS keys")
except AssertionError as e: fail("AT-6", e)


print(f"\nResult: {PASS}/6 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
