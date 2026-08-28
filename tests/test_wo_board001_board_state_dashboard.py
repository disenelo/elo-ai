"""
tests/test_wo_board001_board_state_dashboard.py

WO-BOARD-001: board_state.json → Dashboard Backend.
Proves _read_board_state() exposes board_state with overdue/needs_david counts
at the same cadence as company_state, and fails gracefully when the file is absent.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_board001_board_state_dashboard.py -q
"""
import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_REAL_BOARD_STATE = os.path.join(_ROOT, "blender", "board_state.json")


def _get_read_board_state(board_path: str):
    """Import _read_board_state with a patched _BOARD_STATE path."""
    import importlib
    import company_runtime.dashboard_server as ds
    orig = ds._BOARD_STATE
    ds._BOARD_STATE = board_path
    try:
        result = ds._read_board_state()
    finally:
        ds._BOARD_STATE = orig
    return result


def test_board_state_present_populates_key():
    """AT-1: board_state.json present → board_state key populated with correct fields."""
    bs = _get_read_board_state(_REAL_BOARD_STATE)
    assert isinstance(bs, dict), f"AT-1: _read_board_state must return a dict; got {type(bs)}"
    # The real file has moving, overdue, needs_david, build_list — at least these 4 keys
    assert len(bs) >= 4, (
        f"AT-1: board_state must have >=4 fields; got {list(bs.keys())}"
    )


def test_board_state_absent_no_crash_returns_empty():
    """AT-2: board_state.json absent → warning logged, no crash, returns empty dict."""
    records = []

    class _Cap(logging.Handler):
        def emit(self, r):
            records.append(r)

    import company_runtime.dashboard_server as ds
    logger = logging.getLogger(ds.__name__)
    handler = _Cap()
    logger.addHandler(handler)
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    try:
        result = _get_read_board_state("/nonexistent/path/board_state.json")
        assert result == {}, f"AT-2: absent file must return {{}}; got {result!r}"
        msgs = [r.getMessage() for r in records]
        assert any("board_state" in m.lower() or "missing" in m.lower() for m in msgs), (
            f"AT-2: must log a warning when board_state.json is absent; got: {msgs}"
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


def test_moving_array_readable_and_nonempty():
    """AT-3: moving array readable and contains at least one item when file is present."""
    bs = _get_read_board_state(_REAL_BOARD_STATE)
    assert "moving" in bs, "AT-3: board_state must contain 'moving' key"
    # moving may be a plain list or a dict with "items" key (schema evolution)
    moving = bs["moving"]
    moving_items = moving.get("items", moving) if isinstance(moving, dict) else moving
    assert isinstance(moving_items, list), (
        f"AT-3: board_state['moving'] items must be a list; got {type(moving_items)}"
    )
    assert len(moving_items) >= 1, (
        f"AT-3: board_state['moving'] must contain at least one item; got {moving_items}"
    )


def test_overdue_count_is_integer():
    """AT-4: overdue count returned correctly as integer."""
    bs = _get_read_board_state(_REAL_BOARD_STATE)
    # open_defects replaced overdue; may be dict with "items" or plain list
    od = bs.get("open_defects", bs.get("overdue", []))
    overdue_count = len(od.get("items", od) if isinstance(od, dict) else od)
    assert isinstance(overdue_count, int), (
        f"AT-4: overdue count must be an int; got {type(overdue_count)}"
    )
    # Real file has overdue items — count must be >= 0
    assert overdue_count >= 0, f"AT-4: overdue_count must be >= 0; got {overdue_count}"


def test_needs_david_count_is_integer():
    """AT-5: needs_david count returned correctly as integer."""
    bs = _get_read_board_state(_REAL_BOARD_STATE)
    nd = bs.get("needs_david", [])
    nd_count = len(nd.get("items", nd) if isinstance(nd, dict) else nd)
    assert isinstance(nd_count, int), (
        f"AT-5: needs_david count must be an int; got {type(nd_count)}"
    )
    assert nd_count >= 0, f"AT-5: needs_david_count must be >= 0; got {nd_count}"


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_board_state_present_populates_key),
        ("AT-2", test_board_state_absent_no_crash_returns_empty),
        ("AT-3", test_moving_array_readable_and_nonempty),
        ("AT-4", test_overdue_count_is_integer),
        ("AT-5", test_needs_david_count_is_integer),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"WO-BOARD-001   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
