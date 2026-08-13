"""
tests/test_wo096_desktop_perception.py — WO-096: desktop perception not silently dead

ATs:
  AT-1: assemble_world_state() desktop domain is NOT absent (import no longer broken)
  AT-2: both call sites use get(), not get_active_window()
  AT-3: a broken perception source produces a logged error state, NOT silent absent
  AT-4: perception_faculty.perceive() reads .app/.title attributes correctly
  AT-5: py_compile clean on all three files

Run: python3 tests/test_wo096_desktop_perception.py
"""
from __future__ import annotations
import logging
import os
import py_compile
import sys
import types

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


_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Stub window state at module level ─────────────────────────────────────────

class _FakeWS:
    app = "TestApp"
    title = "TestTitle"
    activity = "coding"
    available = True


_fake_ws_mod = types.ModuleType("desktop.window_state")
_fake_ws_mod.get = lambda: _FakeWS()


def _broken_get():
    raise RuntimeError("accessibility not granted")


_broken_ws_mod = types.ModuleType("desktop.window_state")
_broken_ws_mod.get = _broken_get


def _reload_lws():
    for k in list(sys.modules):
        if "live_world_state" in k:
            del sys.modules[k]
    from world.live_world_state import assemble_world_state
    return assemble_world_state


def _reload_pf():
    for k in list(sys.modules):
        if "perception_faculty" in k:
            del sys.modules[k]
    from faculties.perception.perception_faculty import perceive
    return perceive


# ── AT-1: desktop domain populated after import fix ───────────────────────────
try:
    sys.modules["desktop.window_state"] = _fake_ws_mod
    assemble_world_state = _reload_lws()
    ws = assemble_world_state()

    desktop = ws.desktop
    assert desktop is not None, "desktop domain must not be None"
    assert desktop.active_app == "TestApp", (
        f"expected active_app='TestApp', got {desktop.active_app!r}"
    )
    assert desktop.active_window == "TestTitle", (
        f"expected active_window='TestTitle', got {desktop.active_window!r}"
    )
    ok("AT-1: desktop domain populated (not absent) after import fix")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)

# ── AT-2: both call sites use get(), not get_active_window() ──────────────────
try:
    with open(os.path.join(_BASE, "world", "live_world_state.py")) as f:
        lws_src = f.read()
    with open(os.path.join(_BASE, "faculties", "perception", "perception_faculty.py")) as f:
        pf_src = f.read()

    assert "get_active_window" not in lws_src, \
        "live_world_state.py still references get_active_window"
    assert "get_active_window" not in pf_src, \
        "perception_faculty.py still references get_active_window"

    assert "window_state import get" in lws_src, \
        "live_world_state.py must import get from window_state"
    assert "window_state import get" in pf_src, \
        "perception_faculty.py must import get from window_state"

    ok("AT-2: both call sites use get() — get_active_window removed from both files")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)

# ── AT-3: broken perception source → logged error, assembly continues ──────────
try:
    sys.modules["desktop.window_state"] = _broken_ws_mod
    assemble_world_state2 = _reload_lws()

    log_records = []

    class _CapHandler(logging.Handler):
        def emit(self, r):
            log_records.append(r)

    root = logging.getLogger()
    cap = _CapHandler()
    root.addHandler(cap)
    old_level = root.level
    root.setLevel(logging.DEBUG)
    try:
        ws2 = assemble_world_state2()
    finally:
        root.removeHandler(cap)
        root.setLevel(old_level)

    assert ws2 is not None, "assemble_world_state must not raise on perception failure"

    relevant = [r for r in log_records
                if any(kw in r.getMessage().lower()
                       for kw in ("desktop", "window", "accessibility", "unavailable"))]
    assert relevant, (
        "broken window_state must produce at least one log record; all records: %s"
        % [r.getMessage() for r in log_records]
    )

    ok("AT-3: broken perception source logs error, assembly continues cleanly")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)
finally:
    sys.modules["desktop.window_state"] = _fake_ws_mod

# ── AT-4: perceive_from_live_state() reads window .app/.title attributes ───────
try:
    sys.modules["desktop.window_state"] = _fake_ws_mod
    _reload_pf()  # ensure fresh import
    from faculties.perception.perception_faculty import perceive_from_live_state
    result = perceive_from_live_state()

    assert result is not None, "perceive_from_live_state() must return a result"
    win_health = result.source_health.get("window", {})
    assert win_health.get("status") == "live", (
        f"window source_health must be 'live', got {win_health!r}"
    )
    win_read = result.modality_reads.get("window", "")
    assert "TestApp" in win_read, (
        f"modality_reads['window'] must contain 'TestApp', got {win_read!r}"
    )
    ok("AT-4: perceive_from_live_state() reads window .app/.title via get() attribute access")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)

# ── AT-5: compile clean ────────────────────────────────────────────────────────
try:
    for path in (
        os.path.join(_BASE, "world", "live_world_state.py"),
        os.path.join(_BASE, "faculties", "perception", "perception_faculty.py"),
        os.path.join(_BASE, "desktop", "window_state.py"),
    ):
        py_compile.compile(path, doraise=True)
    ok("AT-5: py_compile clean on all three files")
except py_compile.PyCompileError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-096 desktop perception     {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
