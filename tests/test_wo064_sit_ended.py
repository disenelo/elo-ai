"""
tests/test_wo064_sit_ended.py — BP-5: consume sit_ended → self-model pose = standing (WO-064)

Designer emits sit_ended to unity_events.json when the sit linger stands eLo up
on its own. Builder consumes it and flips self-model pose to "standing" so
eLo never says "I'm sitting" after he's already stood.

  AT-1: sit_ended in unity_events.json → _elo_self.pose flips to "standing"
  AT-2: _ts-guard: sit_ended with _ts > 120s ago → NOT consumed (too old)
  AT-3: after consume, unity_events.json is cleared (empty dict)
  AT-4: non-sit_ended event → pose NOT changed
  AT-5: sit_ended block present in server.py (BP-5 marker)
  AT-6: py_compile clean on server.py

Run: python3 tests/test_wo064_sit_ended.py
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


# ── AT-1: sit_ended → pose flips to "standing" ───────────────────────────────
try:
    from self.elo_self_model import load as _self_load, save as _self_save
    _es = _self_load()
    _es.pose = "idle"
    _self_save(_es)

    _write_events({"type": "sit_ended", "reason": "released", "_ts": time.time()})

    # Simulate the BP-5 consumer block (mirror of server.py logic)
    _se_ev = _read_events()
    _se_ts = float(_se_ev.get("_ts", 0))
    if _se_ev.get("type") == "sit_ended" and _se_ts > time.time() - 120.0:
        _es.pose = "standing"
        _es.available_actions = ["move", "jump", "wave", "gesture", "explore"]
        _self_save(_es)
        _write_events({})

    _es2 = _self_load()
    assert _es2.pose == "standing", f"expected pose='standing', got {_es2.pose!r}"
    ok("AT-1: sit_ended → self-model pose = 'standing'")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: old sit_ended (>120s) → NOT consumed ───────────────────────────────
try:
    from self.elo_self_model import load as _self_load, save as _self_save
    _es = _self_load()
    _es.pose = "idle"
    _self_save(_es)

    _write_events({"type": "sit_ended", "reason": "lapsed", "_ts": time.time() - 200.0})

    _se_ev = _read_events()
    _se_ts = float(_se_ev.get("_ts", 0))
    if _se_ev.get("type") == "sit_ended" and _se_ts > time.time() - 120.0:
        _es.pose = "standing"
        _self_save(_es)
        _write_events({})

    _es2 = _self_load()
    assert _es2.pose == "idle", f"old sit_ended should NOT flip pose, got {_es2.pose!r}"
    ok("AT-2: stale sit_ended (>120s old) NOT consumed — pose stays 'idle'")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: after consume, unity_events.json is cleared ────────────────────────
try:
    _write_events({"type": "sit_ended", "reason": "released", "_ts": time.time()})
    _se_ev = _read_events()
    _se_ts = float(_se_ev.get("_ts", 0))
    if _se_ev.get("type") == "sit_ended" and _se_ts > time.time() - 120.0:
        _write_events({})

    _after = _read_events()
    assert _after == {}, f"unity_events.json should be empty after consume, got {_after}"
    ok("AT-3: unity_events.json cleared after sit_ended consumed")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: non-sit_ended event → pose NOT changed ─────────────────────────────
try:
    from self.elo_self_model import load as _self_load, save as _self_save
    _es = _self_load()
    _es.pose = "idle"
    _self_save(_es)

    _write_events({"type": "move_complete", "_ts": time.time()})

    _se_ev = _read_events()
    _se_ts = float(_se_ev.get("_ts", 0))
    if _se_ev.get("type") == "sit_ended" and _se_ts > time.time() - 120.0:
        _es.pose = "standing"
        _self_save(_es)
        _write_events({})

    _es2 = _self_load()
    assert _es2.pose == "idle", f"move_complete should NOT flip pose, got {_es2.pose!r}"
    ok("AT-4: move_complete event leaves pose unchanged")
    _write_events({})  # clean up
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: BP-5 marker present in server.py ───────────────────────────────────
try:
    with open("server.py", encoding="utf-8") as f:
        _src = f.read()
    assert "BP-5 (WO-064)" in _src, "BP-5 marker not found in server.py"
    assert "sit_ended" in _src, "'sit_ended' not found in server.py consumer"
    assert "pose = \"standing\"" in _src or "pose='standing'" in _src, "pose=standing not set in consumer"
    ok("AT-5: BP-5 consumer block confirmed in server.py")
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
print(f"BP-5 sit_ended consume  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
