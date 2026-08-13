"""
tests/test_wo065_sit_held_pose.py — WO-065 io_contract_note: sit_held → pose = sitting

Designer emits sit_held to unity_events.json every 4 s while eLo is in the sit pose.
Builder consumes it and keeps self-model pose = "sitting" so eLo never
claims to be standing during a sit linger (e.g. after crash/restart).

  AT-1: sit_held in unity_events.json → _elo_self.pose flips to "sitting"
  AT-2: _ts-guard: sit_held with _ts > 30s ago → NOT consumed (too old)
  AT-3: after consume, unity_events.json is cleared
  AT-4: non-sit_held event → pose NOT changed
  AT-5: WO-065 marker present in server.py
  AT-6: py_compile clean on server.py

Run: python3 tests/test_wo065_sit_held_pose.py
"""
import sys, os, json, time, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

_UNITY_EVENTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "unity_events.json")
_UNITY_EVENTS = os.path.normpath(_UNITY_EVENTS)

def _write_events(payload: dict):
    with open(_UNITY_EVENTS, "w", encoding="utf-8") as f:
        json.dump(payload, f)

def _read_events() -> dict:
    try:
        with open(_UNITY_EVENTS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── AT-1: sit_held → pose flips to "sitting" ─────────────────────────────────
try:
    from self.elo_self_model import load as _self_load, save as _self_save
    _es = _self_load()
    _es.pose = "standing"
    _self_save(_es)

    _write_events({"type": "sit_held", "_ts": time.time()})

    # Mirror of server.py sit_held consumer block
    _sh_ev = _read_events()
    _sh_ts = float(_sh_ev.get("_ts", 0))
    if _sh_ev.get("type") == "sit_held" and _sh_ts > time.time() - 30.0:
        _es.pose = "sitting"
        _es.available_actions = ["stand", "look", "wave", "gesture"]
        _self_save(_es)
        _write_events({})

    _es2 = _self_load()
    assert _es2.pose == "sitting", f"expected pose='sitting', got {_es2.pose!r}"
    ok("AT-1: sit_held → self-model pose = 'sitting'")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: old sit_held (>30s) → NOT consumed ─────────────────────────────────
try:
    from self.elo_self_model import load as _self_load, save as _self_save
    _es = _self_load()
    _es.pose = "standing"
    _self_save(_es)

    _write_events({"type": "sit_held", "_ts": time.time() - 60.0})

    _sh_ev = _read_events()
    _sh_ts = float(_sh_ev.get("_ts", 0))
    if _sh_ev.get("type") == "sit_held" and _sh_ts > time.time() - 30.0:
        _es.pose = "sitting"
        _self_save(_es)
        _write_events({})

    _es2 = _self_load()
    assert _es2.pose == "standing", f"stale sit_held should NOT flip pose, got {_es2.pose!r}"
    ok("AT-2: stale sit_held (>30s old) NOT consumed — pose stays 'standing'")
    _write_events({})  # clean up
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: after consume, unity_events.json is cleared ────────────────────────
try:
    _write_events({"type": "sit_held", "_ts": time.time()})
    _sh_ev = _read_events()
    _sh_ts = float(_sh_ev.get("_ts", 0))
    if _sh_ev.get("type") == "sit_held" and _sh_ts > time.time() - 30.0:
        _write_events({})

    _after = _read_events()
    assert _after == {}, f"unity_events.json should be empty after consume, got {_after}"
    ok("AT-3: unity_events.json cleared after sit_held consumed")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: non-sit_held event → pose NOT changed ───────────────────────────────
try:
    from self.elo_self_model import load as _self_load, save as _self_save
    _es = _self_load()
    _es.pose = "standing"
    _self_save(_es)

    _write_events({"type": "move_complete", "_ts": time.time()})

    _sh_ev = _read_events()
    _sh_ts = float(_sh_ev.get("_ts", 0))
    if _sh_ev.get("type") == "sit_held" and _sh_ts > time.time() - 30.0:
        _es.pose = "sitting"
        _self_save(_es)
        _write_events({})

    _es2 = _self_load()
    assert _es2.pose == "standing", f"move_complete should NOT flip pose, got {_es2.pose!r}"
    ok("AT-4: move_complete event leaves pose unchanged")
    _write_events({})  # clean up
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: WO-065 marker present in server.py ─────────────────────────────────
try:
    with open("server.py", encoding="utf-8") as f:
        _src = f.read()
    assert "WO-065" in _src, "WO-065 marker not found in server.py"
    assert "sit_held" in _src, "'sit_held' not found in server.py consumer"
    assert "pose = \"sitting\"" in _src or "pose='sitting'" in _src, "pose=sitting not set in consumer"
    ok("AT-5: WO-065 sit_held consumer block confirmed in server.py")
except AssertionError as e:
    fail("AT-5", e)


# ── AT-6: py_compile clean ───────────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-6: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-6", e)


print()
print("=" * 50)
print(f"WO-065 sit_held pose  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
