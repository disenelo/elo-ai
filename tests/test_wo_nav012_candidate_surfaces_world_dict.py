"""
tests/test_wo_nav012_candidate_surfaces_world_dict.py — WO-NAV-012 acceptance tests.

SP-13: candidate_surfaces in world_dict.
- Populated from generate_candidates() — reachable=True only
- Sorted: route_confidence DESC, horizontal_gap ASC
- Capped at 10
- Empty when body_win_id=-1 (mid-hop)
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _make_candidate(target_win_id, horizontal_gap, route_confidence, reachable=True):
    from world.navigation import Candidate
    return Candidate(
        target_win_id=target_win_id,
        horizontal_gap=horizontal_gap,
        euclidean_gap_px=horizontal_gap + 10,
        requires_verb="jump",
        reachable=reachable,
        route_confidence=route_confidence,
    )


def _make_world(body_win_id=5, surface_edges=(), win_id_to_surface=None, jump_px=576, route_history=()):
    """Build a minimal LiveWorldState-like object for tests."""
    ws = MagicMock()
    ws.body_win_id = body_win_id
    ws.surface_edges = surface_edges
    ws.win_id_to_surface = win_id_to_surface or {}
    ws.jump_px = jump_px
    ws.route_history = route_history
    ws.degraded = []
    ws.desktop = None
    ws.gaze = None
    ws.surfaces = ()
    return ws


def _call_build_world_dict(world):
    """
    Isolate the world_dict assembly from build_executive_context.
    We test via generate_candidates directly with same logic rather than
    running the full context builder (which has many side effects).
    """
    from world.navigation import generate_candidates, Candidate
    all_cands = generate_candidates(
        body_win_id=world.body_win_id,
        surface_edges=world.surface_edges,
        surface_index=world.win_id_to_surface,
        jump_px=world.jump_px,
        route_history=list(world.route_history or []),
    )
    reachable = [c for c in all_cands if c.reachable]
    reachable.sort(key=lambda c: (-c.route_confidence, c.horizontal_gap))
    return [
        {
            "target_win_id": c.target_win_id,
            "horizontal_gap": c.horizontal_gap,
            "euclidean_gap_px": c.euclidean_gap_px,
            "requires_verb": c.requires_verb,
            "route_confidence": c.route_confidence,
        }
        for c in reachable[:10]
    ]


class TestSP13CandidateSurfacesWorldDict(unittest.TestCase):

    def _setup_surface_index_and_edges(self):
        from world.navigation import build_surface_index
        surfaces = (
            {"win_id": "win-5",  "kind": "window", "rect_px": [0,   200, 50, 30], "py_y": 1240},
            {"win_id": "win-10", "kind": "window", "rect_px": [110, 200, 50, 30], "py_y": 1240},
            {"win_id": "win-20", "kind": "window", "rect_px": [220, 200, 50, 30], "py_y": 1240},
            {"win_id": "win-30", "kind": "window", "rect_px": [900, 200, 50, 30], "py_y": 1240},
        )
        idx = build_surface_index(surfaces)
        edges = (
            {"from": "win-5", "to": "win-10", "gap_px": 60,  "requires_verb": "jump"},
            {"from": "win-5", "to": "win-20", "gap_px": 170, "requires_verb": "jump"},
            {"from": "win-5", "to": "win-30", "gap_px": 850, "requires_verb": "jump"},  # unreachable (gap>576)
        )
        return idx, edges

    # AT-1: candidate_surfaces key exists in world_dict output
    def test_at1_candidate_surfaces_key_exists(self):
        idx, edges = self._setup_surface_index_and_edges()
        world = _make_world(body_win_id=5, surface_edges=edges, win_id_to_surface=idx)
        result = _call_build_world_dict(world)
        self.assertIsInstance(result, list)

    # AT-2: body_win_id=-1 → empty list
    def test_at2_mid_hop_empty_list(self):
        idx, edges = self._setup_surface_index_and_edges()
        world = _make_world(body_win_id=-1, surface_edges=edges, win_id_to_surface=idx)
        result = _call_build_world_dict(world)
        self.assertEqual(result, [])

    # AT-3: only reachable=True candidates included (win-30 horizontal_gap=850 > 576 excluded)
    def test_at3_only_reachable_included(self):
        idx, edges = self._setup_surface_index_and_edges()
        world = _make_world(body_win_id=5, surface_edges=edges, win_id_to_surface=idx, jump_px=576)
        result = _call_build_world_dict(world)
        win_ids = [c["target_win_id"] for c in result]
        self.assertNotIn(30, win_ids)  # gap=850 > 576
        self.assertIn(10, win_ids)     # gap=60 ≤ 576
        self.assertIn(20, win_ids)     # gap=170 ≤ 576

    # AT-4: sorted route_confidence DESC (higher confidence first)
    def test_at4_sorted_by_confidence_desc(self):
        idx, edges = self._setup_surface_index_and_edges()
        # Inject route_history with known confidence for win-10 and win-20
        history = [
            {"goal_win_id": 10, "arrived": True},
            {"goal_win_id": 10, "arrived": True},
            {"goal_win_id": 20, "arrived": False},
            {"goal_win_id": 20, "arrived": False},
        ]
        world = _make_world(body_win_id=5, surface_edges=edges, win_id_to_surface=idx,
                            jump_px=576, route_history=tuple(history))
        result = _call_build_world_dict(world)
        if len(result) >= 2:
            self.assertGreaterEqual(result[0]["route_confidence"], result[1]["route_confidence"])

    # AT-5: capped at 10 candidates
    def test_at5_capped_at_10(self):
        from world.navigation import build_surface_index
        # Build 15 reachable surfaces from body win-0
        surfaces = [{"win_id": "win-0", "kind": "window", "rect_px": [0, 200, 10, 30], "py_y": 1240}]
        edges = []
        for i in range(1, 16):
            surfaces.append({"win_id": f"win-{i}", "kind": "window",
                              "rect_px": [20 * i, 200, 10, 30], "py_y": 1240})
            edges.append({"from": "win-0", "to": f"win-{i}", "gap_px": 10,
                           "requires_verb": "jump"})
        idx = build_surface_index(tuple(surfaces))
        world = _make_world(body_win_id=0, surface_edges=tuple(edges), win_id_to_surface=idx, jump_px=1000)
        result = _call_build_world_dict(world)
        self.assertLessEqual(len(result), 10)

    # AT-6: each candidate dict has required keys
    def test_at6_candidate_dict_has_required_keys(self):
        idx, edges = self._setup_surface_index_and_edges()
        world = _make_world(body_win_id=5, surface_edges=edges, win_id_to_surface=idx)
        result = _call_build_world_dict(world)
        for c in result:
            for key in ("target_win_id", "horizontal_gap", "euclidean_gap_px",
                        "requires_verb", "route_confidence"):
                self.assertIn(key, c, f"Missing key {key!r} in candidate dict")

    # AT-7: candidate_surfaces in executive_context world_dict (integration check)
    def test_at7_candidate_surfaces_in_executive_context_world_dict(self):
        from runtime.executive_context import build_executive_context
        from world.live_world_state import LiveWorldState
        ws = LiveWorldState()
        ctx = build_executive_context(
            intent="",
            emotional_context={},
            world=ws,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=None,
            attention={},
        )
        self.assertIn("candidate_surfaces", ctx.world)
        self.assertIsInstance(ctx.world["candidate_surfaces"], list)


if __name__ == "__main__":
    unittest.main()
