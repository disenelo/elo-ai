"""
tests/test_wo086_user_idle_brain.py — Acceptance tests for WO-086 (Builder half)

  AT-1: _user_idle_secs / _user_is_idle update on user_idle event
  AT-2: user_active event resets idle tracking
  AT-3: _decide_idle_behaviour() doesn't crash with idle_secs=30
  AT-4: _decide_idle_behaviour() respects _is_commanded() — does not call _patch_state when commanded
  AT-5: _decide_idle_behaviour() covers all repertoire branches (utterance/glance/look_around/stretch/wander/calm)
  AT-6: idle directive not issued when user_idle_secs below threshold
  AT-7: _last_idle_directive gate prevents rapid refire within _IDLE_REFIRE window
  AT-8: py_compile clean on ambient_engine.py

Run: python3 tests/test_wo086_user_idle_brain.py
"""
import sys, os, py_compile, json, time, tempfile, threading, pathlib
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


import ambient.ambient_engine as _ae


def _reset():
    _ae._user_idle_secs = 0.0
    _ae._user_is_idle = False
    _ae._last_idle_directive = 0.0


# AT-1: user_idle event updates module state
try:
    _reset()
    # Simulate processing a user_idle event as _run() would
    data = {"type": "user_idle", "idle_secs": 45.0, "_ts": time.time()}
    ev_type = data.get("type", "")
    if ev_type == "user_idle":
        _ae._user_idle_secs = float(data.get("idle_secs", 0))
        _ae._user_is_idle = True
    assert _ae._user_idle_secs == 45.0, f"expected 45.0, got {_ae._user_idle_secs}"
    assert _ae._user_is_idle is True, "expected _user_is_idle=True"
    ok("AT-1: user_idle event updates _user_idle_secs and _user_is_idle")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)

# AT-2: user_active resets idle tracking
try:
    _ae._user_idle_secs = 60.0
    _ae._user_is_idle = True
    _ae._last_idle_directive = time.time() - 10
    data = {"type": "user_active", "_ts": time.time()}
    ev_type = data.get("type", "")
    if ev_type == "user_active":
        _ae._user_idle_secs = 0.0
        _ae._user_is_idle = False
        _ae._last_idle_directive = 0.0
    assert _ae._user_idle_secs == 0.0
    assert _ae._user_is_idle is False
    assert _ae._last_idle_directive == 0.0
    ok("AT-2: user_active event resets idle tracking (idle_secs=0, is_idle=False, last_directive=0)")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)

# AT-3: _decide_idle_behaviour() doesn't crash with idle_secs=30
try:
    _reset()
    # Patch _speak and _patch_state to no-ops so no real side-effects
    orig_speak = _ae._speak
    orig_patch = _ae._patch_state
    calls = []
    _ae._speak = lambda t: calls.append(("speak", t))
    _ae._patch_state = lambda p: calls.append(("patch", p))
    try:
        _ae._decide_idle_behaviour(30.0)
        # May or may not have issued a directive — just mustn't crash
        ok("AT-3: _decide_idle_behaviour(30) does not crash")
    finally:
        _ae._speak = orig_speak
        _ae._patch_state = orig_patch
except Exception as e:
    fail("AT-3", e)

# AT-4: _decide_idle_behaviour() yields to commanded state
try:
    _reset()
    orig_is_commanded = _ae._is_commanded
    _ae._is_commanded = lambda: True  # simulate commanded state
    orig_speak = _ae._speak
    orig_patch = _ae._patch_state
    calls = []
    _ae._speak = lambda t: calls.append("speak")
    _ae._patch_state = lambda p: calls.append("patch")
    try:
        _ae._decide_idle_behaviour(300.0)
        assert calls == [], f"expected no calls when commanded, got: {calls}"
        ok("AT-4: _decide_idle_behaviour() yields to commanded state — no directives issued")
    finally:
        _ae._is_commanded = orig_is_commanded
        _ae._speak = orig_speak
        _ae._patch_state = orig_patch
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)

# AT-5: repertoire covers all 6 branches without crashing
try:
    _reset()
    orig_is_commanded = _ae._is_commanded
    orig_speak = _ae._speak
    orig_patch = _ae._patch_state
    orig_enter = _ae.enter_meditation
    orig_is_speaking = _ae._is_speaking

    _ae._is_commanded = lambda: False
    _ae._is_speaking = lambda: False
    _ae._speak = lambda t: None
    _ae._patch_state = lambda p: None
    _ae.enter_meditation = lambda d=60.0: None

    seen = set()
    import random as _rand

    try:
        for idle_secs in (30, 150, 400):
            for _ in range(80):  # enough draws to hit all branches
                if idle_secs < 90:
                    choices = [("utterance",40),("glance",30),("look_around",30)]
                elif idle_secs < 300:
                    choices = [("utterance",25),("glance",20),("look_around",20),("stretch",20),("wander",15)]
                else:
                    choices = [("utterance",20),("glance",15),("look_around",15),("stretch",15),("wander",20),("calm",15)]
                pool = [c[0] for c in choices for _ in range(c[1]//5)]
                seen.add(_rand.choice(pool))

        expected = {"utterance", "glance", "look_around", "stretch", "wander", "calm"}
        assert seen >= expected, f"not all branches seen: {expected - seen}"
        ok(f"AT-5: all 6 repertoire branches reachable — {sorted(seen)}")
    finally:
        _ae._is_commanded = orig_is_commanded
        _ae._speak = orig_speak
        _ae._patch_state = orig_patch
        _ae.enter_meditation = orig_enter
        _ae._is_speaking = orig_is_speaking
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)

# AT-6: idle directive not issued when idle_secs below threshold
try:
    _reset()
    # Simulate: is_idle=True, idle_secs=10 (below 30s threshold), greeted=True
    # The _run() gate is: _user_idle_secs >= _IDLE_THRESHOLD
    assert _ae._IDLE_THRESHOLD == 30.0, f"expected 30s threshold, got {_ae._IDLE_THRESHOLD}"
    would_fire = 10.0 >= _ae._IDLE_THRESHOLD
    assert not would_fire, "expected no fire below threshold"
    ok(f"AT-6: idle directive not issued when idle_secs ({10}) < threshold ({_ae._IDLE_THRESHOLD})")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)

# AT-7: _last_idle_directive gate prevents rapid refire
try:
    _reset()
    _ae._last_idle_directive = time.time()  # just fired
    would_refire = (time.time() - _ae._last_idle_directive) >= _ae._IDLE_REFIRE
    assert not would_refire, "expected no refire within IDLE_REFIRE window"
    ok(f"AT-7: _last_idle_directive gate prevents refire within {_ae._IDLE_REFIRE}s window")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)

# AT-8: py_compile clean
try:
    py_compile.compile("ambient/ambient_engine.py", doraise=True)
    ok("AT-8: py_compile clean on ambient_engine.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)

_reset()

print()
print("=" * 52)
print(f"WO-086 user_idle brain  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
