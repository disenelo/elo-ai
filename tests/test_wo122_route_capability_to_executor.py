"""
tests/test_wo122_route_capability_to_executor.py

WO-122 Row 14 ROUTE — capability → executor routing, gated by Executive.

Card 0010_WO-122_ROUTE_capability_to_executor.md:
    Executive picks a capability (plan.capabilities). Router used to re-decide
    by keyword. Two deciders is the fault, not the fallback.

The disconnection test: blank plan.capabilities on a weather query must NOT
fire the weather agent. If the router behaves identically, Executive's choice
is being ignored — card not done.

Tests:
    RT-1  Executive selects nothing → weather agent does NOT fire
          (disconnection test — the row)
    RT-2  Executive selects weather → weather executor runs
    RT-3  Executive selects time (not weather) on weather-worded query →
          weather does NOT fire even though keyword would match
    RT-4  Unknown capability → loud log, no dispatch, no keyword fallback
    RT-5  Direct intercepts (nav/lore/system) still fire without plan

Run: python3 tests/test_wo122_route_capability_to_executor.py
"""
import sys
sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


import tools.tool_router as tr
from tools.tool_router import enrich_from_plan


class _AgentSwap:
    """Swap _AGENTS entries for the duration of a test, restore after."""
    def __init__(self, **replacements):
        self.replacements = replacements
        self.originals = {}
    def __enter__(self):
        for k, v in self.replacements.items():
            self.originals[k] = tr._AGENTS.get(k)
            tr._AGENTS[k] = v
        return self
    def __exit__(self, *_):
        for k, orig in self.originals.items():
            if orig is None:
                tr._AGENTS.pop(k, None)
            else:
                tr._AGENTS[k] = orig


# Sentinel for "should not be called"
class _AgentCalled(Exception):
    pass


print("\nRT-1: Executive selected nothing → weather agent does NOT fire (DISCONNECTION)")
try:
    def _weather_forbidden(q):
        raise _AgentCalled(f"weather agent must NOT run when Executive selected nothing, got {q!r}")

    with _AgentSwap(weather=_weather_forbidden):
        query = "what's the weather in London"
        enriched, agent = enrich_from_plan(query, [])

    if enriched == query and agent is None:
        ok("RT-1 — blank plan.capabilities → dispatch changed (weather did NOT fire)")
    else:
        fail("RT-1", f"expected (raw, None); got enriched={enriched!r} agent={agent!r}")
except _AgentCalled as e:
    fail("RT-1", f"weather agent DID fire despite Executive selecting nothing: {e}")
except Exception as e:
    fail("RT-1", repr(e))


print("\nRT-2: Executive selected weather → weather executor runs")
try:
    def _weather_stub(q):
        return f"Weather in London: Sunny, 22C, feels like 20C."

    with _AgentSwap(weather=_weather_stub):
        query = "what's the weather"
        enriched, agent = enrich_from_plan(query, [("weather", "weather London")])

    if "Weather in London" in enriched and agent == "weather":
        ok(f"RT-2 — Executive-selected weather ran → agent={agent!r}")
    else:
        fail("RT-2", f"weather did not fire — enriched={enriched[:80]!r} agent={agent!r}")
except Exception as e:
    fail("RT-2", repr(e))


print("\nRT-3: Executive selected time (not weather) on weather query → weather rejected")
try:
    def _weather_forbidden(q):
        raise _AgentCalled(f"weather must NOT fire when Executive picked time, got {q!r}")
    def _time_stub(q):
        return "It's 15:00."

    with _AgentSwap(weather=_weather_forbidden, time=_time_stub):
        # Weather-worded query; Executive picked time only.
        query = "what's the weather in London"
        # Plan query must carry time-of-day intent: WO-CAP-COG-004 (2026-09-20)
        # strips a bare "the time", which this 2026-08-19 test predates.
        enriched, agent = enrich_from_plan(query, [("time", "what time is it")])

    if "15:00" in enriched and agent == "time":
        ok("RT-3 — only Executive's choice (time) ran; weather-keyword did NOT trigger weather")
    else:
        fail("RT-3", f"unexpected: enriched={enriched[:120]!r} agent={agent!r}")
except _AgentCalled as e:
    fail("RT-3", f"weather DID fire despite Executive picking time: {e}")
except Exception as e:
    fail("RT-3", repr(e))


print("\nRT-4: Unknown capability → loud log, no dispatch, no keyword fallback")
try:
    # Capture logs to verify LOUD signal
    import io
    log_buf = io.StringIO()
    handler = logging.StreamHandler(log_buf)
    handler.setLevel(logging.WARNING)
    _tr_logger = logging.getLogger("tools.tool_router")
    _tr_logger.addHandler(handler)
    _tr_logger.setLevel(logging.WARNING)

    def _weather_forbidden(q):
        raise _AgentCalled(f"weather must NOT fire on unknown-capability path, got {q!r}")

    try:
        with _AgentSwap(weather=_weather_forbidden):
            query = "what's the weather in London"
            enriched, agent = enrich_from_plan(query, [("nonexistent_capability", "x")])
    finally:
        _tr_logger.removeHandler(handler)

    log_output = log_buf.getvalue()
    if enriched == query and agent is None and "UNKNOWN capability" in log_output:
        ok("RT-4 — unknown capability logged loudly; no dispatch; no keyword fallback")
    elif enriched != query:
        fail("RT-4", f"unknown capability triggered dispatch: enriched={enriched[:120]!r}")
    elif "UNKNOWN capability" not in log_output:
        fail("RT-4", f"no loud log for unknown capability; log={log_output!r}")
    else:
        fail("RT-4", f"unexpected: enriched={enriched!r} agent={agent!r} log={log_output!r}")
except _AgentCalled as e:
    fail("RT-4", f"weather fired despite unknown capability: {e}")
except Exception as e:
    fail("RT-4", repr(e))


print("\nRT-5: Direct intercepts (lore) still fire without plan capabilities")
try:
    query = "what is K-7"
    enriched, agent = enrich_from_plan(query, [])
    if agent == "lore" and "K-7" in enriched:
        ok(f"RT-5 — direct intercept (lore) fired despite empty plan → agent={agent!r}")
    else:
        fail("RT-5", f"lore intercept did not fire: enriched={enriched[:120]!r} agent={agent!r}")
except Exception as e:
    fail("RT-5", repr(e))


print(f"\n{'='*60}")
print(f"WO-122 Row 14 ROUTE — capability→executor gating: {PASS} passed, {FAIL} failed")
print()
print("Row verified by this test:")
print("  14 ROUTE — plan.capabilities gates dispatch; keyword re-decision removed")
print("             (unknown/rejected capabilities cannot run silently)")
if FAIL:
    sys.exit(1)
