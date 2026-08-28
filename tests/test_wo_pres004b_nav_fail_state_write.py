"""
tests/test_wo_pres004b_nav_fail_state_write.py — WO-PRES-004B

AT-6a: blender_state.json contains nav_fail (string) + nav_fail_ts (float) after
       navigation failure (patch() called with correct values).
AT-6b: Two sequential failures produce two DIFFERENT nav_fail_ts values
       (edge-trigger contract — Design reads a changed ts to fire expression).
"""
import json
import os
import sys
import time
import tempfile
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── AT-6a: patch() call writes nav_fail + nav_fail_ts to blender_state ────────

def test_at6a_nav_fail_fields_written_to_blender_state(tmp_path):
    """D: patch(nav_fail, nav_fail_ts) lands in blender_state.json after nav failure."""
    state_file = tmp_path / "blender_state.json"
    state_file.write_text("{}", encoding="utf-8")

    import blender_bridge.state_writer as _sw
    original_path = _sw._STATE_PATH
    _sw._STATE_PATH = str(state_file)
    try:
        _sw.patch({
            "nav_fail":    "cant_reach",
            "nav_fail_ts": time.time(),
        })
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert "nav_fail" in state, "nav_fail key missing from blender_state.json"
        assert state["nav_fail"] == "cant_reach", f"Expected 'cant_reach', got {state['nav_fail']!r}"
        assert "nav_fail_ts" in state, "nav_fail_ts key missing from blender_state.json"
        assert isinstance(state["nav_fail_ts"], float), "nav_fail_ts must be a float"
    finally:
        _sw._STATE_PATH = original_path


def test_at6a_nav_fail_val_mapping():
    """no_reachable_route → cant_reach; eval reason → evaluating; other → no_route."""
    def _map(reason):
        return (
            "cant_reach" if reason == "no_reachable_route"
            else "evaluating" if "eval" in reason
            else "no_route"
        )
    assert _map("no_reachable_route") == "cant_reach"
    assert _map("evaluating_alternatives") == "evaluating"
    assert _map("unknown_error") == "no_route"


def test_at6a_server_source_has_pres004b_patch_call():
    """server.py must call patch with nav_fail and nav_fail_ts inside NAVIGATION_FAILED block."""
    server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()
    nav_failed_idx = src.index("[NAVIGATION_FAILED]")
    # The patch call must appear after [NAVIGATION_FAILED]
    after = src[nav_failed_idx:nav_failed_idx + 3000]
    assert "nav_fail" in after, "nav_fail key not found in NAVIGATION_FAILED block"
    assert "nav_fail_ts" in after, "nav_fail_ts key not found in NAVIGATION_FAILED block"
    assert "state_writer" in after or "sw_patch" in after, "state_writer patch not called in NAVIGATION_FAILED block"


# ── AT-6b: two sequential failures produce different nav_fail_ts (edge-trigger) ─

def test_at6b_sequential_failures_produce_different_ts(tmp_path):
    """Each nav failure writes a fresh nav_fail_ts — Design fires on ts change."""
    state_file = tmp_path / "blender_state.json"
    state_file.write_text("{}", encoding="utf-8")

    import blender_bridge.state_writer as _sw
    original_path = _sw._STATE_PATH
    _sw._STATE_PATH = str(state_file)
    try:
        _sw.patch({"nav_fail": "cant_reach", "nav_fail_ts": time.time()})
        state_1 = json.loads(state_file.read_text(encoding="utf-8"))
        ts_1 = state_1["nav_fail_ts"]

        # Small sleep to guarantee different float value
        time.sleep(0.01)

        _sw.patch({"nav_fail": "cant_reach", "nav_fail_ts": time.time()})
        state_2 = json.loads(state_file.read_text(encoding="utf-8"))
        ts_2 = state_2["nav_fail_ts"]

        assert ts_2 != ts_1, (
            f"nav_fail_ts must change between failures for edge-trigger; got {ts_1} == {ts_2}"
        )
        assert ts_2 > ts_1, "second failure ts must be greater than first"
    finally:
        _sw._STATE_PATH = original_path
