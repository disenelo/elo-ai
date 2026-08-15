"""
tests/test_0010_wo103_wave3.py — WO-103 Wave 3: three disconnection-proof tests.

## Expected results today
  AT-1 PASS   — ordering is correct; runtime confirms it
  OF-*  FAIL  — faculties.temporal is an orphan (WO-CANON-XXV dead code; leave red)
  PW-*  FAIL  — gaze not in _PRESERVE_KEYS; survives patch() but not _write() (WO-100 open)

Tests:
    AT-1  spine.run() calls assemble_world_state before decide at runtime
    OF-1  enumerate faculties/ packages; fail if any is not reachable from server.py
    PW-1  gaze survives a background patch() write (merge, not overwrite — should pass)
    PW-2  gaze survives a _write() partial call — fails today (gaze not in _PRESERVE_KEYS)

Run: python3 tests/test_0010_wo103_wave3.py
"""
import json
import os
import sys
import tempfile
import unittest.mock as mock

sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: assemble_world_state called before decide() at runtime ──────────────

print("\nAT-1: spine.run() calls assemble_world_state before decide at runtime")
try:
    _call_log = []

    import world.live_world_state as _lws_mod
    import runtime.executive as _exec_mod

    _orig_assemble = _lws_mod.assemble_world_state
    _orig_decide   = _exec_mod.decide

    def _spy_assemble(*a, **kw):
        _call_log.append("assemble")
        try:
            return _orig_assemble(*a, **kw)
        except Exception:
            return None

    def _spy_decide(*a, **kw):
        _call_log.append("decide")
        return _orig_decide(*a, **kw)

    with mock.patch.object(_lws_mod, "assemble_world_state", _spy_assemble), \
         mock.patch.object(_exec_mod, "decide", _spy_decide):
        from runtime.spine.spine import run as _spine_run
        _spine_run("hello", state={}, attention={})

    if "assemble" in _call_log and "decide" in _call_log:
        _ai = _call_log.index("assemble")
        _di = _call_log.index("decide")
        if _ai < _di:
            ok(f"AT-1 — assemble at pos {_ai}, decide at pos {_di} in call log")
        else:
            fail("AT-1", f"decide ({_di}) before assemble ({_ai}) — Ruling C violated")
    elif "assemble" not in _call_log:
        fail("AT-1", "assemble_world_state not called on live turn")
    else:
        fail("AT-1", "decide not called on live turn")
except Exception as e:
    fail("AT-1", repr(e))


# ── OF-1: orphan-faculty detection ────────────────────────────────────────────

print("\nOF-1: faculty packages not reachable from live path → FAIL")
print("      (faculties.temporal expected to fail — WO-CANON-XXV dead code)")
try:
    _root           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _faculties_root = os.path.join(_root, "faculties")

    # Faculty packages: subdirectories of faculties/ that have __init__.py
    _packages = sorted(
        d for d in os.listdir(_faculties_root)
        if os.path.isdir(os.path.join(_faculties_root, d))
        and os.path.exists(os.path.join(_faculties_root, d, "__init__.py"))
        and not d.startswith("_")
    )

    # Live-path source files: server.py + all Python files in runtime/ and world/
    _live_dirs = [
        os.path.join(_root, "server.py"),
        os.path.join(_root, "runtime"),
        os.path.join(_root, "world"),
    ]
    _live_src = ""
    for _lp in _live_dirs:
        if os.path.isfile(_lp):
            with open(_lp, encoding="utf-8") as _f:
                _live_src += _f.read()
        elif os.path.isdir(_lp):
            for _dirpath, _, _fnames in os.walk(_lp):
                for _fn in _fnames:
                    if _fn.endswith(".py"):
                        try:
                            with open(os.path.join(_dirpath, _fn), encoding="utf-8") as _f:
                                _live_src += _f.read()
                        except Exception:
                            pass

    import re as _re
    _orphans = []
    _wired   = []
    for _pkg in _packages:
        # A faculty is reachable if server.py has a real import statement
        # (from faculties.{pkg} or import faculties.{pkg}) — not just a string reference
        _pat = _re.compile(
            rf"(?:from\s+faculties\.{_re.escape(_pkg)}|import\s+faculties\.{_re.escape(_pkg)})"
        )
        if _pat.search(_live_src):
            _wired.append(_pkg)
        else:
            _orphans.append(_pkg)

    if _orphans:
        for _o in _orphans:
            print(f"    ORPHAN: faculties.{_o}")
        print(f"    Wired: {_wired}")
        fail("OF-1", f"orphan faculties found: {_orphans} — wire them or retire them")
    else:
        ok(f"OF-1 — all {len(_packages)} faculty packages reachable from server.py")
except Exception as e:
    fail("OF-1", repr(e))


# ── PW-1: gaze survives a patch() call (deep-merge, not overwrite) ────────────

print("\nPW-1: gaze survives a patch() write (merge path — should pass)")
try:
    import blender_bridge.state_writer as _sw

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as _tf:
        _tmp_path = _tf.name
        json.dump({"gaze": {"yaw": 10.0, "pitch": 5.0, "active": True},
                   "motion": {"animation": "idle"}}, _tf)

    _orig_path = _sw._STATE_PATH
    try:
        _sw._STATE_PATH = _tmp_path
        # patch() does a deep-merge — it reads current state and merges, never strips
        _sw.patch({"state": {"mode": "idle"}})
        with open(_tmp_path) as _f:
            _result = json.load(_f)
        if "gaze" in _result:
            ok("PW-1 — gaze survives patch() (merge path correct)")
        else:
            fail("PW-1", "gaze stripped by patch() — merge logic broken")
    finally:
        _sw._STATE_PATH = _orig_path
        try: os.unlink(_tmp_path)
        except: pass
except Exception as e:
    fail("PW-1", repr(e))


# ── PW-2: gaze survives _write() — fails today (not in _PRESERVE_KEYS) ───────

print("\nPW-2: gaze survives _write() (full overwrite path) — EXPECTED TO FAIL today")
print("      Fix: add 'gaze' to _PRESERVE_KEYS in state_writer.py (WO-100 open)")
try:
    import blender_bridge.state_writer as _sw2

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as _tf2:
        _tmp_path2 = _tf2.name
        # Simulate a prior full write that included gaze
        json.dump({"gaze": {"yaw": 10.0, "pitch": 5.0, "active": True},
                   "motion": {"animation": "idle"}, "_ts": 0.0}, _tf2)

    _orig_path2 = _sw2._STATE_PATH
    try:
        _sw2._STATE_PATH = _tmp_path2
        # Full _write() without gaze — preserves only _PRESERVE_KEYS
        _sw2._write({"motion": {"animation": "run"}, "_ts": 1.0})
        with open(_tmp_path2) as _f2:
            _result2 = json.load(_f2)
        if "gaze" in _result2:
            ok("PW-2 — gaze survives _write() (gaze now in _PRESERVE_KEYS)")
        else:
            fail("PW-2", "gaze stripped by _write() — add 'gaze' to _PRESERVE_KEYS (WO-100)")
    finally:
        _sw2._STATE_PATH = _orig_path2
        try: os.unlink(_tmp_path2)
        except: pass
except Exception as e:
    fail("PW-2", repr(e))


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"WO-103 Wave 3: {PASS} passed, {FAIL} failed")
print()
print("Expected today:")
print("  AT-1 PASS  — ordering correct at runtime")
print("  OF-1 FAIL  — faculties.temporal orphaned (correct; leave red)")
print("  PW-1 PASS  — patch() (merge) preserves gaze")
print("  PW-2 FAIL  — _write() strips gaze (WO-100 open; leave red)")
if FAIL:
    sys.exit(1)
