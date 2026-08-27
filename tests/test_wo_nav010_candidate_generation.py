"""
tests/test_wo_nav010_candidate_generation.py — WO-NAV-010 acceptance tests.

SP-12: Surface identity bridge — build_surface_index() maps int win_id → surface dict.
SP-11: Candidate generation — generate_candidates() from body position + surface graph.
"""
import sys
import os
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from world.navigation import Candidate, build_surface_index, generate_candidates


def _make_surface(win_id_str, kind="window", rect_px=None):
    return {
        "win_id": win_id_str,
        "kind": kind,
        "rect_px": rect_px or [100, 200, 50, 30],
        "py_y": 1240,
    }


def _make_edge(from_str, to_str, gap_px=50, requires_verb="jump"):
    return {"from": from_str, "to": to_str, "gap_px": gap_px, "requires_verb": requires_verb}


class TestSP12SurfaceIdentityBridge(unittest.TestCase):

    # AT-1: build_surface_index maps integer key from "win-N" string
    def test_at1_build_surface_index_integer_key(self):
        surfaces = (
            _make_surface("win-1679"),
            _make_surface("win-42"),
        )
        idx = build_surface_index(surfaces)
        self.assertIn(1679, idx)
        self.assertIn(42, idx)

    # AT-2: lookup by win_id returns correct kind
    def test_at2_lookup_returns_correct_surface(self):
        surfaces = (_make_surface("win-5", kind="behind"),)
        idx = build_surface_index(surfaces)
        self.assertEqual(idx[5]["kind"], "behind")

    # AT-3: empty surfaces → empty index
    def test_at3_empty_surfaces_empty_index(self):
        idx = build_surface_index(())
        self.assertEqual(idx, {})

    # AT-4: unparseable win_id → silently skipped
    def test_at4_unparseable_id_skipped(self):
        surfaces = (_make_surface("badid"),)
        idx = build_surface_index(surfaces)
        self.assertEqual(len(idx), 0)


class TestSP11CandidateGeneration(unittest.TestCase):

    def _surface_index_and_edges(self):
        """Body at win-10 with two reachable neighbours and one overhang."""
        surfaces = (
            _make_surface("win-10", rect_px=[0, 200, 50, 30]),    # source
            _make_surface("win-20", rect_px=[110, 200, 50, 30]),   # reachable (gap=60)
            _make_surface("win-30", rect_px=[900, 200, 50, 30]),   # unreachable (gap=850)
            _make_surface("win-40", kind="overhang", rect_px=[200, 200, 50, 30]),  # excluded
        )
        idx = build_surface_index(surfaces)
        edges = (
            _make_edge("win-10", "win-20", gap_px=60, requires_verb="jump"),
            _make_edge("win-10", "win-30", gap_px=850, requires_verb="jump"),
            _make_edge("win-10", "win-40", gap_px=100, requires_verb="jump"),
        )
        return idx, edges

    # AT-5: body_win_id=-1 → empty list (mid-hop L3-NAV-3)
    def test_at5_mid_hop_returns_empty(self):
        idx, edges = self._surface_index_and_edges()
        result = generate_candidates(-1, edges, idx, jump_px=576, route_history=[])
        self.assertEqual(result, [])

    # AT-6: reachable candidate within jump_px included; unreachable excluded
    def test_at6_reachable_within_jump_px(self):
        idx, edges = self._surface_index_and_edges()
        result = generate_candidates(10, edges, idx, jump_px=576, route_history=[])
        win_ids = [c.target_win_id for c in result]
        # win-20 horizontal_gap = 110 - (0+50) = 60 ≤ 576 → reachable
        self.assertIn(20, win_ids)
        # win-30 horizontal_gap = 900 - (0+50) = 850 > 576 → not reachable but still a Candidate
        # (reachable=False, not excluded — only overhang/wall is excluded)
        self.assertIn(30, win_ids)

    # AT-7: overhang node excluded from candidates
    def test_at7_overhang_excluded(self):
        idx, edges = self._surface_index_and_edges()
        result = generate_candidates(10, edges, idx, jump_px=576, route_history=[])
        win_ids = [c.target_win_id for c in result]
        self.assertNotIn(40, win_ids)

    # AT-8: unreachable candidate has reachable=False
    def test_at8_unreachable_candidate_flag(self):
        idx, edges = self._surface_index_and_edges()
        result = generate_candidates(10, edges, idx, jump_px=576, route_history=[])
        win30 = next((c for c in result if c.target_win_id == 30), None)
        self.assertIsNotNone(win30)
        self.assertFalse(win30.reachable)

    # AT-9: no edges from body → empty list
    def test_at9_no_edges_from_body(self):
        idx = build_surface_index((_make_surface("win-99"),))
        # edge goes from win-1 not from win-99
        edges = (_make_edge("win-1", "win-2"),)
        result = generate_candidates(99, edges, idx, jump_px=576, route_history=[])
        self.assertEqual(result, [])

    # AT-10: LiveWorldState has surface_edges and win_id_to_surface fields
    def test_at10_live_world_state_fields_present(self):
        from world.live_world_state import LiveWorldState
        ws = LiveWorldState()
        self.assertTrue(hasattr(ws, "surface_edges"))
        self.assertTrue(hasattr(ws, "win_id_to_surface"))
        self.assertIsInstance(ws.surface_edges, tuple)
        self.assertIsInstance(ws.win_id_to_surface, dict)


if __name__ == "__main__":
    unittest.main()
