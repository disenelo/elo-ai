"""
tests/test_0002_wo118_route.py — Acceptance tests for WO-118 (card 0002).

4 tests:
    RT-1  Completed move appears in route_memory with correct outcome
    RT-2  Failed move (arrived=False) is recorded as failure
    RT-3  Success rate for a repeated route changes after repeated attempts
    RT-4  last_move absent while body navigating ⇒ WARNING fires

Run: python3 tests/test_0002_wo118_route.py
"""
import json
import os
import sys
import tempfile
import logging

sys.path.insert(0, ".")

logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from self.route_memory import remember_route, route_confidence, recall_route


# ── RT-1: completed move recorded with correct outcome ────────────────────────

print("\nRT-1: Completed move appears in route_memory with correct outcome")
_tmp1 = None
try:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
        _tmp1 = tf.name

    ok1 = remember_route(
        goal_surface="window_a",
        legs=["step", "jump"],
        arrived=True,
        fell=False,
        duration_s=1.5,
        smoothness=0.9,
        ack_id="test-ack-1",
        ack_received=True,
        log_path=_tmp1,
    )
    rec = recall_route("window_a", log_path=_tmp1)

    if not ok1:
        fail("RT-1", "remember_route returned False")
    elif rec is None:
        fail("RT-1", "recall_route returned None after write")
    elif not rec.get("arrived"):
        fail("RT-1", f"arrived not True in record: {rec}")
    elif rec.get("goal") != "window_a":
        fail("RT-1", f"goal mismatch: {rec}")
    else:
        ok("RT-1 — completed move recorded with correct goal and arrived=True")
except Exception as e:
    fail("RT-1", repr(e))
finally:
    if _tmp1:
        try: os.unlink(_tmp1)
        except: pass


# ── RT-2: failed move recorded as failure ─────────────────────────────────────

print("\nRT-2: Failed move (arrived=False) recorded as failure")
_tmp2 = None
try:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
        _tmp2 = tf.name

    remember_route(
        goal_surface="window_b",
        legs=["step"],
        arrived=False,
        fell=True,
        duration_s=0.8,
        smoothness=0.2,
        ack_id="test-ack-2",
        ack_received=True,
        log_path=_tmp2,
    )
    rec2 = recall_route("window_b", log_path=_tmp2)

    if rec2 is None:
        fail("RT-2", "recall_route returned None for failed move")
    elif rec2.get("arrived") is not False:
        fail("RT-2", f"expected arrived=False, got: {rec2}")
    elif rec2.get("fell") is not True:
        fail("RT-2", f"expected fell=True, got: {rec2}")
    else:
        ok("RT-2 — failed move recorded with arrived=False, fell=True")
except Exception as e:
    fail("RT-2", repr(e))
finally:
    if _tmp2:
        try: os.unlink(_tmp2)
        except: pass


# ── RT-3: success rate changes after repeated attempts ────────────────────────

print("\nRT-3: Success rate changes after repeated attempts on same route")
_tmp3 = None
try:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
        _tmp3 = tf.name

    c0 = route_confidence("window_c", log_path=_tmp3)  # no attempts yet

    remember_route("window_c", [], arrived=True,  fell=False, duration_s=1.0,
                   smoothness=1.0, ack_id="r1", ack_received=True, log_path=_tmp3)
    c1 = route_confidence("window_c", log_path=_tmp3)   # 1/1 success

    remember_route("window_c", [], arrived=False, fell=True,  duration_s=1.0,
                   smoothness=0.0, ack_id="r2", ack_received=True, log_path=_tmp3)
    c2 = route_confidence("window_c", log_path=_tmp3)   # 1/2

    remember_route("window_c", [], arrived=True,  fell=False, duration_s=1.0,
                   smoothness=1.0, ack_id="r3", ack_received=True, log_path=_tmp3)
    c3 = route_confidence("window_c", log_path=_tmp3)   # 2/3

    if c0 != 0.0:
        fail("RT-3", f"expected 0.0 before any attempts, got {c0}")
    elif c1 != 1.0:
        fail("RT-3", f"expected 1.0 after 1 success, got {c1}")
    elif not (0.0 < c2 < 1.0):
        fail("RT-3", f"expected between 0 and 1 after mixed results, got {c2}")
    elif c3 <= c2:
        fail("RT-3", f"expected confidence to rise after 2nd success: c2={c2} c3={c3}")
    else:
        ok(f"RT-3 — success rate changes correctly: {c0} → {c1} → {c2} → {c3}")
except Exception as e:
    fail("RT-3", repr(e))
finally:
    if _tmp3:
        try: os.unlink(_tmp3)
        except: pass


# ── RT-4: last_move absent while body navigating → WARNING fires ──────────────

print("\nRT-4: last_move absent while body navigating ⇒ WARNING fires")
_tmp4 = None
try:
    import desktop.spatial_state as _ss

    # Fake spatial JSON: body has an active goal but no last_move
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump({"x": 0.5, "y": 0.1, "height": 120, "goal": 99999, "route": [1, 2]}, tf)
        _tmp4 = tf.name

    _orig_path = _ss._SPATIAL_PATH
    _ss._SPATIAL_PATH = _tmp4
    _ss._absent_last_move_count = 0   # reset from any prior state

    _warned: list = []
    _orig_warning = _ss._log.warning
    def _capture(*a, **kw):
        _warned.append(a[0] if a else "")
        _orig_warning(*a, **kw)
    _ss._log.warning = _capture

    try:
        for _ in range(4):
            _ss.get_elo_spatial()
    finally:
        _ss._SPATIAL_PATH = _orig_path
        _ss._log.warning = _orig_warning

    _wo118 = [w for w in _warned if "WO-118" in str(w)]
    if not _wo118:
        fail("RT-4", f"WO-118 WARNING not emitted; warnings seen: {_warned}")
    else:
        ok("RT-4 — WO-118 Rule 1 WARNING fires after 3 consecutive absent last_move reads")
except Exception as e:
    fail("RT-4", repr(e))
finally:
    if _tmp4:
        try: os.unlink(_tmp4)
        except: pass


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"WO-118 Route: {PASS} passed, {FAIL} failed")
if FAIL:
    sys.exit(1)
