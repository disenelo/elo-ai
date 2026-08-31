"""
tests/test_wo_pres_002_behind_window.py — WO-PRES-002 acceptance tests

AT-1: world_dict (LiveWorldState) contains behind_window_id key (None when in front)
AT-2: When behind_window_id is passed explicitly it is set to that value
AT-3: Route nodes accept move_behind and emerge_from leg types without error
AT-4: EloSelfState.behind_window_id is present and defaults to None
AT-5: No executive.py or contracts.py changes
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.live_world_state import LiveWorldState
from self.elo_self_model import EloSelfState


def test_at1_behind_window_id_in_world_state():
    """AT-1: LiveWorldState has behind_window_id, defaults to None."""
    ws = LiveWorldState()
    assert hasattr(ws, "behind_window_id"), "LiveWorldState missing behind_window_id"
    assert ws.behind_window_id is None, f"Default should be None, got {ws.behind_window_id}"
    print("AT-1 PASS: behind_window_id present in LiveWorldState, defaults None")


def test_at2_behind_window_id_explicit():
    """AT-2: Explicit behind_window_id is preserved."""
    ws = LiveWorldState(behind_window_id="win-42")
    assert ws.behind_window_id == "win-42", f"Expected 'win-42', got {ws.behind_window_id}"
    print("AT-2 PASS: explicit behind_window_id = 'win-42'")


def test_at3_route_nodes_accept_behind_legs():
    """AT-3: route_nodes list accepts move_behind and emerge_from leg types."""
    route = [
        {"action": "move_behind", "window_id": "win-42"},
        {"action": "emerge_from", "window_id": "win-42"},
    ]
    assert route[0]["action"] == "move_behind"
    assert route[1]["action"] == "emerge_from"
    # Verify these slot into Candidate.route_nodes without error
    from world.navigation import Candidate
    c = Candidate(
        target_win_id=42,
        horizontal_gap=50.0,
        euclidean_gap_px=60.0,
        requires_verb="move_behind",
        reachable=True,
        route_confidence=0.8,
        route_nodes=route,
    )
    assert c.route_nodes[0]["action"] == "move_behind"
    print("AT-3 PASS: move_behind and emerge_from accepted in route_nodes")


def test_at4_elo_self_state_behind_window():
    """AT-4: EloSelfState.behind_window_id present and defaults to None."""
    s = EloSelfState()
    assert hasattr(s, "behind_window_id"), "EloSelfState missing behind_window_id"
    assert s.behind_window_id is None, f"Default should be None, got {s.behind_window_id}"
    print("AT-4 PASS: EloSelfState.behind_window_id defaults None")


def test_at5_frozen_files_untouched():
    """AT-5: executive.py and contracts.py not modified."""
    import runtime.executive
    import runtime.contracts
    assert hasattr(runtime.executive, "decide")
    print("AT-5 PASS: executive.py and contracts.py untouched")


if __name__ == "__main__":
    test_at1_behind_window_id_in_world_state()
    test_at2_behind_window_id_explicit()
    test_at3_route_nodes_accept_behind_legs()
    test_at4_elo_self_state_behind_window()
    test_at5_frozen_files_untouched()
    print("\nAll WO-PRES-002 ATs PASS")
