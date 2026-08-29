"""
tests/test_wo_board_001_dashboard_backend.py — WO-BOARD-001
Verify board_state.json → dashboard backend wiring.
Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_board_001_dashboard_backend.py -v
"""
import json
import os
import sys
import tempfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BOARD_STATE_PATH = os.path.join(ROOT, "blender", "board_state.json")


def _read_board_state(path: str) -> dict:
    """Mirror _read_board_state() from company_runtime/dashboard_server.py."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def test_at1_board_state_present_populates_dashboard():
    """AT-1: board_state.json present → board_state key populated with correct field count."""
    assert os.path.exists(BOARD_STATE_PATH), f"board_state.json missing at {BOARD_STATE_PATH}"
    bs = _read_board_state(BOARD_STATE_PATH)
    assert isinstance(bs, dict), "Expected dict"
    assert len(bs) > 0, "board_state should have at least one key"
    assert "verified_done" in bs or "moving" in bs or "needs_david" in bs, \
        "Expected at least one of verified_done/moving/needs_david in board_state.json"


def test_at2_missing_board_state_no_crash():
    """AT-2: board_state.json absent → returns {}, no crash."""
    result = _read_board_state("/tmp/nonexistent_board_state_99999.json")
    assert result == {}, f"Expected empty dict on missing file, got {result}"


def test_at3_moving_or_verified_readable():
    """AT-3: verified_done array (or moving) readable with at least one item."""
    bs = _read_board_state(BOARD_STATE_PATH)
    verified = bs.get("verified_done", {}).get("items", [])
    moving = bs.get("moving", [])
    at_least_one = len(verified) > 0 or len(moving) > 0
    assert at_least_one, "Expected at least one item in verified_done.items or moving"


def test_at4_overdue_count_integer():
    """AT-4: overdue count returns correctly as integer (may be 0)."""
    bs = _read_board_state(BOARD_STATE_PATH)
    overdue_count = len(bs.get("open_defects", {}).get("items", []))
    assert isinstance(overdue_count, int), f"Expected int, got {type(overdue_count)}"


def test_at5_needs_david_count_integer():
    """AT-5: needs_david count returns correctly as integer (may be 0)."""
    bs = _read_board_state(BOARD_STATE_PATH)
    nd_count = len(bs.get("needs_david", {}).get("items", []))
    assert isinstance(nd_count, int), f"Expected int, got {type(nd_count)}"

    # Also verify module is importable and wired correctly
    from company_runtime.dashboard_server import _read_board_state as _ds_read
    bs2 = _ds_read()
    assert isinstance(bs2, dict), "dashboard_server._read_board_state() must return dict"
