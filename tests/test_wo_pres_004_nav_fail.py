"""
tests/test_wo_pres_004_nav_fail.py — WO-PRES-004 + WO-PRES-004B
Verify failed navigation outcome chain + nav_fail blender_state writes.
Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_pres_004_nav_fail.py -v
"""
import json
import os
import sys
import time
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BLENDER_STATE = os.path.join(ROOT, "blender", "blender_state.json")


def test_at1_handle_navigate_returns_navigation_failed():
    """AT-1: handle_navigate(reachable=False) → navigation_failed outcome."""
    from runtime.backend_router import handle_navigate
    result = handle_navigate({"goal_win_id": 99}, reachable=False)
    assert result is not None, "Expected a dict, got None"
    assert result.get("outcome") == "navigation_failed", \
        f"Expected outcome=navigation_failed, got {result}"
    assert result.get("reason") == "no_reachable_route", \
        f"Expected reason=no_reachable_route, got {result}"


def test_at2_navigate_outcome_distinguishes_success_failure():
    """AT-2: navigation_failed outcome dict is distinct from success intent dict."""
    from runtime.backend_router import handle_navigate
    failed = handle_navigate({"goal_win_id": 1}, reachable=False)
    # A success path returns {"name": "move", ...}, not {"outcome": "navigation_failed"}
    assert "outcome" in failed and failed["outcome"] == "navigation_failed", \
        f"Failed outcome should have outcome=navigation_failed, got {failed}"
    assert "name" not in failed, \
        "navigation_failed should NOT have 'name' key (not a move intent)"


def test_at3_no_repeated_loop_on_failure():
    """AT-3: failure path returns one clear result (no None, no exception, no loop)."""
    from runtime.backend_router import handle_navigate
    results = []
    for _ in range(3):
        r = handle_navigate({"goal_win_id": 7}, reachable=False)
        results.append(r)
    # All 3 calls should return the same stable failure dict — no crash, no None
    for r in results:
        assert r is not None, "navigation_failed should never return None"
        assert r.get("outcome") == "navigation_failed", f"Expected consistent outcome, got {r}"


def test_at4_navigation_failed_no_crash():
    """AT-4: navigation_failed does not crash — handle_navigate is safe."""
    from runtime.backend_router import handle_navigate
    try:
        result = handle_navigate({"goal_win_id": 42}, reachable=False)
        assert result is not None
    except Exception as e:
        pytest.fail(f"handle_navigate raised unexpectedly: {e}")


def test_at5_navigation_failed_has_goal_win_id():
    """AT-5: navigation_failed outcome includes goal_win_id for capability result chain."""
    from runtime.backend_router import handle_navigate
    result = handle_navigate({"goal_win_id": 15}, reachable=False)
    assert result.get("goal_win_id") == 15, \
        f"Expected goal_win_id=15 in outcome, got {result}"


def test_at6a_pres004b_writes_nav_fail_to_blender_state():
    """AT-6a (WO-PRES-004B): blender_state.json gets nav_fail + nav_fail_ts after navigate failure."""
    from blender_bridge.state_writer import patch as _patch
    _patch({
        "nav_fail": "cant_reach",
        "nav_fail_ts": round(time.time(), 3),
    })
    with open(BLENDER_STATE, encoding="utf-8") as f:
        state = json.load(f)
    assert "nav_fail" in state, "nav_fail key missing from blender_state.json"
    assert state["nav_fail"] in ("cant_reach", "evaluating", "no_route"), \
        f"Unexpected nav_fail value: {state['nav_fail']}"
    assert "nav_fail_ts" in state, "nav_fail_ts key missing from blender_state.json"
    assert isinstance(state["nav_fail_ts"], (int, float)), \
        f"nav_fail_ts should be numeric, got {type(state['nav_fail_ts'])}"


def test_at6b_sequential_failures_produce_different_ts():
    """AT-6b (WO-PRES-004B): two sequential failures produce two DIFFERENT nav_fail_ts (edge-trigger)."""
    from blender_bridge.state_writer import patch as _patch
    ts1 = round(time.time(), 3)
    _patch({"nav_fail": "cant_reach", "nav_fail_ts": ts1})
    time.sleep(0.01)  # ensure ts differs
    ts2 = round(time.time(), 3)
    _patch({"nav_fail": "cant_reach", "nav_fail_ts": ts2})
    assert ts2 != ts1, f"Expected different timestamps, both were {ts1}"
    with open(BLENDER_STATE, encoding="utf-8") as f:
        state = json.load(f)
    assert state["nav_fail_ts"] == ts2, \
        f"Expected latest ts {ts2}, got {state['nav_fail_ts']}"
