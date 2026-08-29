"""
tests/test_wo_pres_003_planner.py — WO-PRES-003-PLANNER
Verify bottom→top wrap as navigation route leg in handle_navigate().
Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_pres_003_planner.py -v
"""
import json
import os
import sys
import tempfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _make_spatial(
    body_win_id: int = 1,
    jump_px: int = 576,
    edges: list = None,
) -> "str":
    """Write a temp elo_spatial.json and return its path."""
    if edges is None:
        edges = []
    data = {
        "body_win_id": body_win_id,
        "surface_graph": {
            "capability_set": {"jump_px": jump_px},
            "edges": edges,
        }
    }
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, f)
    f.close()
    return f.name


def test_at1_beyond_reach_gets_wrap_leg():
    """AT-1: goal beyond jump reach → route includes wrap_bottom_to_top leg."""
    from runtime.backend_router import handle_navigate
    # body=1, goal=3, gap=1000px > jump_px=576 → not directly reachable
    edges = [
        {"from": "win-1", "to": "win-3", "gap_px": 1000},
    ]
    spatial = _make_spatial(body_win_id=1, jump_px=576, edges=edges)
    try:
        result = handle_navigate(
            {"goal_win_id": 3},
            _elo_spatial_path=spatial,
        )
        route = result.get("route", [])
        assert route, "Expected non-empty route"
        wrap_legs = [l for l in route if l.get("type") == "wrap_bottom_to_top"]
        assert wrap_legs, f"No wrap_bottom_to_top leg in route: {route}"
    finally:
        os.unlink(spatial)


def test_at2_within_reach_no_wrap():
    """AT-2: goal within jump reach → NO wrap leg (direct path)."""
    from runtime.backend_router import handle_navigate
    # body=1, goal=2, gap=400px < jump_px=576 → directly reachable
    edges = [
        {"from": "win-1", "to": "win-2", "gap_px": 400},
    ]
    spatial = _make_spatial(body_win_id=1, jump_px=576, edges=edges)
    try:
        result = handle_navigate(
            {"goal_win_id": 2},
            _elo_spatial_path=spatial,
        )
        route = result.get("route", [])
        wrap_legs = [l for l in route if l.get("type") == "wrap_bottom_to_top"]
        assert not wrap_legs, f"Unexpected wrap leg in direct-reach route: {route}"
    finally:
        os.unlink(spatial)


def test_at3_unreachable_returns_navigation_failed():
    """AT-3: goal unreachable even via wrap (jump_px=0 + edges present) → navigation_failed."""
    from runtime.backend_router import handle_navigate
    # jump_px=0 AND edges non-empty → D-4 path fires (if _body is not None and _edges → jump_px <= 0)
    edges = [{"from": "win-1", "to": "win-5", "gap_px": 1000}]
    spatial = _make_spatial(body_win_id=1, jump_px=0, edges=edges)
    try:
        result = handle_navigate(
            {"goal_win_id": 5},
            _elo_spatial_path=spatial,
        )
        assert result.get("outcome") == "navigation_failed", \
            f"Expected navigation_failed, got {result}"
        # Also verify the reachable=False path (PRES-004 direct)
        result2 = handle_navigate({"goal_win_id": 5}, reachable=False)
        assert result2.get("outcome") == "navigation_failed", \
            f"Expected navigation_failed via reachable=False, got {result2}"
    finally:
        os.unlink(spatial)


def test_at4_tiny_jump_px_considers_wrap():
    """AT-4: mock jump_px=10 → wrap leg still considered for any unreachable gap."""
    from runtime.backend_router import handle_navigate
    # With jump_px=10, even a gap of 20px is unreachable → wrap candidate
    edges = [
        {"from": "win-1", "to": "win-4", "gap_px": 20},
    ]
    spatial = _make_spatial(body_win_id=1, jump_px=10, edges=edges)
    try:
        result = handle_navigate(
            {"goal_win_id": 4},
            _elo_spatial_path=spatial,
        )
        route = result.get("route", [])
        wrap_legs = [l for l in route if l.get("type") == "wrap_bottom_to_top"]
        assert wrap_legs, f"Expected wrap_bottom_to_top for tiny jump_px=10, got route: {route}"
    finally:
        os.unlink(spatial)


def test_at5_wrap_route_includes_correct_leg_type():
    """AT-5: wrap route serialised with type=wrap_bottom_to_top for Unity."""
    from runtime.backend_router import handle_navigate
    edges = [
        {"from": "win-1", "to": "win-6", "gap_px": 800},  # gap > jump_px=576
    ]
    spatial = _make_spatial(body_win_id=1, jump_px=576, edges=edges)
    try:
        result = handle_navigate(
            {"goal_win_id": 6},
            _elo_spatial_path=spatial,
        )
        route = result.get("route", [])
        assert route, "Expected route in result"
        first_leg = route[0]
        assert first_leg.get("type") == "wrap_bottom_to_top", \
            f"First leg type should be wrap_bottom_to_top, got {first_leg}"
        assert "from_win_id" in first_leg, "wrap leg must include from_win_id"
        assert first_leg.get("to_position") == "screen_top_same_x", \
            f"Expected to_position=screen_top_same_x, got {first_leg.get('to_position')}"
    finally:
        os.unlink(spatial)
