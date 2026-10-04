"""
tests/test_lights_wiring.py — §8 Lights runtime wiring acceptance tests

Spec: BUILD_STATUS §8 — dispatch_lights() wired into active runtime (tool_router.py _direct_intercepts)

AT-1: 'turn the lights off' → lights intercept fires, 'lights' executor returned
AT-2: 'dim the lights' → lights intercept fires with scene='dim'
AT-3: 'focus mode lights' → lights intercept fires with scene='focus'
AT-4: 'calm scene' → lights intercept fires with scene='calm'
AT-5: 'dispatch_lights("set_scene", {"scene": "calm"})' with no env returns graceful failure
AT-6: py_compile clean on tool_router.py and lights_agent.py
"""
import sys
import os
import py_compile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PASS = 0
FAIL = 0


def ok(n):
    global PASS; PASS += 1; print(f"  ✅ {n}")


def fail(n, r):
    global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: 'turn the lights off' fires lights intercept ───────────────────────
try:
    from tools.tool_router import _direct_intercepts
    result = _direct_intercepts("turn the lights off")
    if result is not None and result[1] == "lights":
        ok("AT-1: 'turn the lights off' → lights intercept fires")
    else:
        fail("AT-1", f"expected ('...', 'lights'), got {result}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: 'dim the lights' → scene='dim' ─────────────────────────────────────
try:
    from tools.tool_router import _direct_intercepts
    result = _direct_intercepts("dim the lights")
    if result is not None and result[1] == "lights" and "dim" in result[0].lower():
        ok("AT-2: 'dim the lights' → lights intercept with scene=dim")
    else:
        fail("AT-2", f"expected lights+dim, got {result}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: 'focus mode lights' → scene='focus' ────────────────────────────────
try:
    from tools.tool_router import _direct_intercepts
    result = _direct_intercepts("focus mode lights")
    if result is not None and result[1] == "lights" and "focus" in result[0].lower():
        ok("AT-3: 'focus mode lights' → lights intercept with scene=focus")
    else:
        fail("AT-3", f"expected lights+focus, got {result}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: 'calm lights' → scene='calm' ───────────────────────────────────────
try:
    from tools.tool_router import _direct_intercepts
    result = _direct_intercepts("calm mode lights")
    if result is not None and result[1] == "lights" and "calm" in result[0].lower():
        ok("AT-4: 'calm mode lights' → lights intercept with scene=calm")
    else:
        fail("AT-4", f"expected lights+calm, got {result}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: dispatch_lights graceful failure without env ───────────────────────
try:
    from capabilities.lights_agent import dispatch_lights
    result = dispatch_lights("set_scene", {"scene": "calm"})
    if not result.get("success") and "not set" in (result.get("error") or ""):
        ok("AT-5: dispatch_lights without HUE env → graceful failure (not set)")
    else:
        fail("AT-5", f"expected graceful failure, got {result}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ────────────────────────────────────────────────────
try:
    py_compile.compile("tools/tool_router.py", doraise=True)
    py_compile.compile("capabilities/lights_agent.py", doraise=True)
    ok("AT-6: py_compile clean on tool_router.py and lights_agent.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 60)
print(f"§8 Lights wiring   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
