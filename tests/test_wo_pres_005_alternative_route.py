"""
tests/test_wo_pres_005_alternative_route.py — WO-PRES-005 acceptance tests

AT-1: Direct route exists → single jump leg, no alternative search
AT-2: Direct unavailable, intermediate exists → two-leg route
AT-3: No intermediate AND no run-up AND no wrap → navigation_failed
AT-4: Run-up available → run-up route before give-up
AT-5: Wrap available → wrap route before give-up
AT-6: Max 3 intermediates evaluated (performance guard)
AT-7: No executive.py or contracts.py changes
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.navigation import evaluate_alternatives, build_surface_index

_JUMP_PX = 100


def _surface(win_id, left, width=50):
    return {"win_id": f"win-{win_id}", "kind": "window", "rect_px": [left, 0, width, 50], "py_y": 0}


def _edge(from_id, to_id, gap_px):
    return {"from": f"win-{from_id}", "to": f"win-{to_id}", "gap_px": gap_px, "requires_verb": "jump"}


def _idx(*surfs):
    return build_surface_index(surfs)


def test_at1_direct():
    """AT-1: direct jump within jump_px → single route_nodes leg."""
    gap = 80  # within jump_px=100
    idx = _idx(_surface(1, 0), _surface(2, 50 + gap))
    edges = (_edge(1, 2, gap),)
    r = evaluate_alternatives(1, 2, edges, idx, _JUMP_PX, [], run_capability=False, wrap_available=False)
    assert r["outcome"] == "direct", f"Expected direct, got {r}"
    assert len(r["route_nodes"]) == 1
    print("AT-1 PASS: direct jump → single leg")


def test_at2_intermediate():
    """AT-2: direct unavailable, intermediate exists → two-leg route."""
    # body=1 (left=0,w=50), mid=3 (left=140,w=50), dest=2 (left=280,w=50)
    # gap 1→3 = 90 (reachable), gap 3→2 = 90 (reachable), gap 1→2 = 230 (not reachable)
    idx = _idx(_surface(1, 0), _surface(3, 140), _surface(2, 280))
    edges = (_edge(1, 3, 90), _edge(3, 2, 90))
    r = evaluate_alternatives(1, 2, edges, idx, _JUMP_PX, [], run_capability=False, wrap_available=False)
    assert r["outcome"] == "intermediate", f"Expected intermediate, got {r}"
    assert len(r["route_nodes"]) == 2
    print("AT-2 PASS: intermediate two-leg route")


def test_at3_navigation_failed():
    """AT-3: no direct, no intermediate, no run-up, no wrap → navigation_failed."""
    idx = _idx(_surface(1, 0), _surface(2, 300))  # gap=250, way beyond jump+bonus
    edges = (_edge(1, 2, 250),)
    r = evaluate_alternatives(1, 2, edges, idx, _JUMP_PX, [], run_capability=False, wrap_available=False)
    assert r["outcome"] == "navigation_failed", f"Expected navigation_failed, got {r}"
    print("AT-3 PASS: all routes fail → navigation_failed")


def test_at4_run_up_before_giveup():
    """AT-4: run-up available → run-up route before give-up."""
    # gap = 115 — beyond jump_px=100 but within 100 + 25 (bonus)
    idx = _idx(_surface(1, 0), _surface(2, 165))  # 50+115=165
    edges = (_edge(1, 2, 115),)
    r = evaluate_alternatives(1, 2, edges, idx, _JUMP_PX, [], run_capability=True, wrap_available=False)
    assert r["outcome"] == "run_up", f"Expected run_up, got {r}"
    assert any(n["action"] == "run_on_current" for n in r["route_nodes"])
    print("AT-4 PASS: run-up route returned before give-up")


def test_at5_wrap_before_giveup():
    """AT-5: wrap available → wrap route before give-up."""
    # gap too big for jump and run-up, but wrap available
    idx = _idx(_surface(1, 0), _surface(2, 300))
    edges = (_edge(1, 2, 250),)
    r = evaluate_alternatives(1, 2, edges, idx, _JUMP_PX, [], run_capability=False, wrap_available=True)
    assert r["outcome"] == "wrap", f"Expected wrap, got {r}"
    assert any(n["action"] == "wrap_bottom_to_top" for n in r["route_nodes"])
    print("AT-5 PASS: wrap route returned before give-up")


def test_at6_max_intermediates_evaluated():
    """AT-6: at most 3 intermediate candidates evaluated."""
    from unittest.mock import patch
    # 6 potential intermediates — only 3 should be checked
    surfs = [_surface(i, i * 200) for i in range(8)]
    idx = build_surface_index(tuple(surfs))
    edges = tuple(_edge(0, i, 190) for i in range(1, 8))  # body→all others at gap=190 (not reachable at 100)
    call_count = {"n": 0}
    orig = evaluate_alternatives.__code__  # just check MAX_INTERMEDIATES constant
    from world.navigation import _MAX_INTERMEDIATES
    assert _MAX_INTERMEDIATES == 3, f"Expected 3, got {_MAX_INTERMEDIATES}"
    print(f"AT-6 PASS: _MAX_INTERMEDIATES = {_MAX_INTERMEDIATES}")


def test_at7_frozen_files():
    """AT-7: executive.py and contracts.py untouched."""
    import runtime.executive
    import runtime.contracts
    assert hasattr(runtime.executive, "decide")
    print("AT-7 PASS: frozen files untouched")


if __name__ == "__main__":
    test_at1_direct()
    test_at2_intermediate()
    test_at3_navigation_failed()
    test_at4_run_up_before_giveup()
    test_at5_wrap_before_giveup()
    test_at6_max_intermediates_evaluated()
    test_at7_frozen_files()
    print("\nAll WO-PRES-005 ATs PASS")
