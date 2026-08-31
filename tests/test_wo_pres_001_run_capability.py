"""
tests/test_wo_pres_001_run_capability.py — WO-PRES-001 acceptance tests

AT-1: gap < jump_px → direct jump, no run-up leg
AT-2: jump_px < gap <= jump_px + bonus AND run_capability=True → run-up route planned
AT-3: gap > jump_px + bonus → unreachable even with run-up
AT-4: run_capability=False → no run-up route, surface unreachable
AT-5: run_capability and run_up_distance_px appear in LiveWorldState
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.navigation import generate_candidates, build_surface_index


def _edge(from_key, to_key, gap_px):
    return {"from": from_key, "to": to_key, "gap_px": gap_px, "requires_verb": "jump"}


def _surfaces(from_id, to_id, from_rect, to_rect):
    return (
        {"win_id": f"win-{from_id}", "kind": "window", "rect_px": from_rect, "py_y": 0},
        {"win_id": f"win-{to_id}",   "kind": "window", "rect_px": to_rect,   "py_y": 0},
    )


def _make(from_id, to_id, gap_px, jump_px, run_capability=True):
    src_w = 100
    from_rect = [0, 0, src_w, 50]
    to_rect   = [src_w + gap_px, 0, 100, 50]  # left edge of target = src_right + gap
    surfs = _surfaces(from_id, to_id, from_rect, to_rect)
    idx   = build_surface_index(surfs)
    edges = (
        _edge(f"win-{from_id}", f"win-{to_id}", gap_px),
    )
    run_up_bonus = jump_px * 0.25
    return generate_candidates(
        body_win_id=from_id,
        surface_edges=edges,
        surface_index=idx,
        jump_px=jump_px,
        route_history=[],
        run_capability=run_capability,
    ), run_up_bonus


def test_at1_direct_jump_no_runup():
    """AT-1: gap < jump_px → reachable with no run-up."""
    jump_px = 576
    gap_px  = 400  # well within jump range
    candidates, _ = _make(1, 2, gap_px, jump_px)
    assert len(candidates) == 1
    c = candidates[0]
    assert c.reachable, "Should be reachable"
    assert not c.requires_run_up, "Should not require run-up"
    assert c.route_nodes is None, "No run-up nodes expected"
    print("AT-1 PASS: gap < jump_px → direct jump, no run-up")


def test_at2_runup_route_planned():
    """AT-2: jump_px < gap <= jump_px + bonus AND run_capability=True → run-up route."""
    jump_px = 576
    gap_px  = int(jump_px * 1.15)   # 15% beyond jump, within 25% bonus
    candidates, _ = _make(1, 2, gap_px, jump_px, run_capability=True)
    assert len(candidates) == 1
    c = candidates[0]
    assert c.reachable, "Run-up candidate should be reachable"
    assert c.requires_run_up, "Should require run-up"
    assert c.route_nodes is not None and len(c.route_nodes) == 2, (
        f"Expected 2 route_nodes, got {c.route_nodes}"
    )
    assert c.route_nodes[0]["action"] == "run_on_current"
    assert c.route_nodes[1]["action"] == "jump"
    assert c.route_nodes[1].get("run_up") is True
    print("AT-2 PASS: gap in run-up range → run-up route planned")


def test_at3_beyond_runup_unreachable():
    """AT-3: gap > jump_px + bonus → unreachable even with run-up."""
    jump_px = 576
    gap_px  = int(jump_px * 1.30)   # 30% beyond jump, exceeds 25% bonus
    candidates, _ = _make(1, 2, gap_px, jump_px, run_capability=True)
    assert len(candidates) == 1
    c = candidates[0]
    assert not c.reachable, f"Should be unreachable but got reachable={c.reachable}"
    assert not c.requires_run_up
    print("AT-3 PASS: gap > jump + bonus → unreachable")


def test_at4_no_runup_when_capability_false():
    """AT-4: run_capability=False → no run-up even in range."""
    jump_px = 576
    gap_px  = int(jump_px * 1.15)
    candidates, _ = _make(1, 2, gap_px, jump_px, run_capability=False)
    assert len(candidates) == 1
    c = candidates[0]
    assert not c.reachable, "Without run_capability should be unreachable"
    assert not c.requires_run_up
    print("AT-4 PASS: run_capability=False → no run-up route")


def test_at5_fields_on_live_world_state():
    """AT-5: run_capability and run_up_distance_px are on LiveWorldState."""
    from world.live_world_state import LiveWorldState
    ws = LiveWorldState()
    assert hasattr(ws, "run_capability"),     "LiveWorldState missing run_capability"
    assert hasattr(ws, "run_up_distance_px"), "LiveWorldState missing run_up_distance_px"
    assert ws.run_capability is True,         f"Default should be True, got {ws.run_capability}"
    assert ws.run_up_distance_px == 120.0,    f"Default should be 120.0, got {ws.run_up_distance_px}"
    print("AT-5 PASS: run_capability and run_up_distance_px present on LiveWorldState")


if __name__ == "__main__":
    test_at1_direct_jump_no_runup()
    test_at2_runup_route_planned()
    test_at3_beyond_runup_unreachable()
    test_at4_no_runup_when_capability_false()
    test_at5_fields_on_live_world_state()
    print("\nAll WO-PRES-001 ATs PASS")
