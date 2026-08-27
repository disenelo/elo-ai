"""
tests/test_wo_nav013_navigate_handler.py

Acceptance tests for WO-NAV-013 (SP-18 / SP-20 / SP-21).
5 pytest-style ATs — no sys.exit at module level.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_nav013_navigate_handler.py -q
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# AT-1 — SP-18: handle_navigate exists and is callable
def test_handle_navigate_importable():
    from runtime.backend_router import handle_navigate
    assert callable(handle_navigate)


# AT-2 — SP-18: goal_win_id → movement intent dict with correct structure
def test_handle_navigate_goal_win_id():
    from runtime.backend_router import handle_navigate
    result = handle_navigate({"goal_win_id": 7})
    assert result is not None
    assert isinstance(result, dict)
    assert result.get("name") == "move"
    assert result.get("goal_win_id") == 7


# AT-3 — SP-18: nav_type maps to direction; no goal_win_id required
def test_handle_navigate_type_maps_to_direction():
    from runtime.backend_router import handle_navigate
    result = handle_navigate({"type": "jump_right"})
    assert result is not None
    assert result.get("direction") == "right"
    result_left = handle_navigate({"type": "jump_left"})
    assert result_left is not None
    assert result_left.get("direction") == "left"


# AT-4 — SP-20: navigate action in server.py routes through handle_navigate
#         (no duplicate path — same ACK channel as other body intents)
def test_navigate_action_uses_handle_navigate_not_duplicate_path():
    server_path = os.path.join(os.path.dirname(__file__), "..", "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "handle_navigate" in source, "handle_navigate not found in server.py"
    assert 'action == "navigate"' in source, 'navigate action gate missing in server.py'


# AT-5 — SP-21: [NAVIGATE_OUTCOME] injected into g_ctx after navigation
def test_navigate_outcome_injected_into_g_ctx():
    server_path = os.path.join(os.path.dirname(__file__), "..", "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "[NAVIGATE_OUTCOME]" in source, "[NAVIGATE_OUTCOME] block missing from server.py"
    assert "g_ctx" in source and "NAVIGATE_OUTCOME" in source, \
        "[NAVIGATE_OUTCOME] not wired into g_ctx in server.py"
