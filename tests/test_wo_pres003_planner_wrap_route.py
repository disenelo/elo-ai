"""
tests/test_wo_pres003_planner_wrap_route.py

Acceptance tests for WO-PRES-003-PLANNER (wrap_bottom_to_top route leg).
5 pytest-style ATs.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_pres003_planner_wrap_route.py -v
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_spatial(body_win_id: int, gap_px: int, jump_px: int) -> str:
    """Write a minimal elo_spatial.json stub to a temp file; return its path."""
    data = {
        "body_win_id": body_win_id,
        "surface_graph": {
            "capability_set": {"jump_px": jump_px, "reach_px": 89, "scale": 1.0},
            "nodes": [
                {"id": f"win-{body_win_id}", "kind": "ledge"},
                {"id": "win-999",            "kind": "ledge"},
            ],
            "edges": [
                # One edge from body → target (win-999) with configurable gap
                {
                    "from": f"win-{body_win_id}",
                    "to":   "win-999",
                    "gap_px": gap_px,
                    "requires_verb": "jump",
                },
                # win-888 unreachable: only inbound from nowhere we model
                {
                    "from": "win-ISOLATED",
                    "to":   "win-888",
                    "gap_px": 0,
                    "requires_verb": "jump",
                },
            ],
        },
    }
    tf = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, tf)
    tf.close()
    return tf.name


# AT-1 — beyond direct jump reach → route includes wrap_bottom_to_top leg first
def test_wrap_leg_added_when_beyond_reach():
    """
    WO-PRES-003-PLANNER AT-1:
    target gap_px(500) > jump_px(100) → route[0] is wrap_bottom_to_top.
    """
    from runtime.backend_router import handle_navigate
    path = _make_spatial(body_win_id=1679, gap_px=500, jump_px=100)
    try:
        result = handle_navigate({"goal_win_id": 999}, _elo_spatial_path=path)
        assert result is not None, "AT-1: expected move intent, got None"
        assert result.get("name") == "move", f"AT-1: expected name='move', got {result}"
        route = result.get("route")
        assert route is not None, f"AT-1: 'route' missing from intent {result}"
        assert isinstance(route, list) and len(route) >= 1, \
            f"AT-1: route must be a non-empty list, got {route}"
        assert route[0].get("type") == "wrap_bottom_to_top", \
            f"AT-1: first route leg must be wrap_bottom_to_top, got {route[0]}"
        assert route[0].get("from_win_id") == 1679, \
            f"AT-1: wrap leg from_win_id must be body_win_id=1679, got {route[0]}"
        assert route[0].get("to_position") == "screen_top_same_x", \
            f"AT-1: wrap leg to_position must be 'screen_top_same_x', got {route[0]}"
    finally:
        os.unlink(path)


# AT-2 — within direct jump reach → no wrap leg (direct path preferred)
def test_no_wrap_when_directly_reachable():
    """
    WO-PRES-003-PLANNER AT-2:
    target gap_px(50) <= jump_px(200) → intent has no 'route' field.
    """
    from runtime.backend_router import handle_navigate
    path = _make_spatial(body_win_id=1679, gap_px=50, jump_px=200)
    try:
        result = handle_navigate({"goal_win_id": 999}, _elo_spatial_path=path)
        assert result is not None, "AT-2: expected move intent, got None"
        assert result.get("name") == "move", f"AT-2: expected name='move', got {result}"
        assert "route" not in result, \
            f"AT-2: 'route' must be absent for directly reachable target, got {result}"
    finally:
        os.unlink(path)


# AT-3 — unreachable even via wrap (jump_px=0) → navigation_failed
def test_navigation_failed_when_jump_px_zero():
    """
    WO-PRES-003-PLANNER AT-3:
    jump_px=0 (no jump capability) → navigation_failed outcome, no crash.
    """
    from runtime.backend_router import handle_navigate
    path = _make_spatial(body_win_id=1679, gap_px=50, jump_px=0)
    try:
        result = handle_navigate({"goal_win_id": 999}, _elo_spatial_path=path)
        assert result is not None, "AT-3: expected outcome dict, got None"
        assert result.get("outcome") == "navigation_failed", \
            f"AT-3: expected navigation_failed outcome, got {result}"
        assert result.get("reason") == "no_reachable_route", \
            f"AT-3: expected reason='no_reachable_route', got {result}"
    finally:
        os.unlink(path)


# AT-4 — jump_px=10 (tiny reach) → wrap candidate considered even for short gaps
def test_wrap_considered_with_tiny_jump_px():
    """
    WO-PRES-003-PLANNER AT-4:
    jump_px=10, gap_px=50 (beyond reach) → wrap route is added.
    Confirms live jump_px is used, not any hardcoded value.
    """
    from runtime.backend_router import handle_navigate
    path = _make_spatial(body_win_id=1679, gap_px=50, jump_px=10)
    try:
        result = handle_navigate({"goal_win_id": 999}, _elo_spatial_path=path)
        assert result is not None, "AT-4: expected move intent, got None"
        assert result.get("name") == "move", f"AT-4: expected name='move', got {result}"
        route = result.get("route")
        assert route is not None and route[0].get("type") == "wrap_bottom_to_top", \
            f"AT-4: wrap leg expected with jump_px=10, got route={route}"
    finally:
        os.unlink(path)


# AT-5 — route field is serialised correctly in the move_command dict
def test_route_serialised_in_move_command():
    """
    WO-PRES-003-PLANNER AT-5 / D-2:
    route field is present and JSON-serialisable in the intent dict.
    """
    from runtime.backend_router import handle_navigate
    path = _make_spatial(body_win_id=1679, gap_px=500, jump_px=100)
    try:
        result = handle_navigate({"goal_win_id": 999}, _elo_spatial_path=path)
        assert result is not None, "AT-5: expected move intent, got None"
        route = result.get("route")
        assert route is not None, f"AT-5: 'route' missing from intent"
        # Must be JSON-serialisable (move_command is sent over the wire)
        serialised = json.dumps(result)
        decoded = json.loads(serialised)
        assert decoded.get("route", [{}])[0].get("type") == "wrap_bottom_to_top", \
            f"AT-5: route not preserved through JSON round-trip: {decoded}"
        # Second leg must name the goal
        assert decoded["route"][1].get("goal_win_id") == 999, \
            f"AT-5: second route leg goal_win_id missing: {decoded['route']}"
    finally:
        os.unlink(path)
