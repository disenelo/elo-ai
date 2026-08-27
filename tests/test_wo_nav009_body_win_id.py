"""
tests/test_wo_nav009_body_win_id.py — WO-NAV-009 acceptance tests (SP-9).

body_win_id: Python consumer of Unity-emitted body position in elo_spatial.json.
L3-NAV-3: confirmed body position updates only on arrived=True.
"""
import json
import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _make_spatial(body_win_id: int, screen_h: int = 1440) -> dict:
    return {
        "body_win_id": body_win_id,
        "screen_h": screen_h,
        "surface_graph": {"nodes": [], "capability_set": {}},
    }


class TestWONAV009BodyWinId(unittest.TestCase):

    def setUp(self):
        """Reset confirmed body win id to -1 before each test."""
        import world.live_world_state as lws
        lws._confirmed_body_win_id = -1

    # AT-1: body_win_id present in LiveWorldState after assembly (key exists)
    def test_at1_body_win_id_present_in_live_world_state(self):
        import world.live_world_state as lws
        ws = lws.LiveWorldState()
        self.assertTrue(hasattr(ws, "body_win_id"))

    # AT-2: spatial body_win_id=5 → LiveWorldState.body_win_id=5
    def test_at2_body_win_id_5_from_spatial(self):
        import world.live_world_state as lws
        _orig_path = lws._SPATIAL_PATH
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(_make_spatial(5), f)
            tmp_path = f.name
        try:
            lws._SPATIAL_PATH = tmp_path
            ws = lws.assemble_world_state(turn_id="test-at2")
            self.assertEqual(ws.body_win_id, 5)
        finally:
            lws._SPATIAL_PATH = _orig_path
            os.unlink(tmp_path)

    # AT-3: spatial body_win_id=-1 (mid-hop) → LiveWorldState.body_win_id=-1
    def test_at3_body_win_id_minus1_mid_hop(self):
        import world.live_world_state as lws
        _orig_path = lws._SPATIAL_PATH
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(_make_spatial(-1), f)
            tmp_path = f.name
        try:
            lws._SPATIAL_PATH = tmp_path
            ws = lws.assemble_world_state(turn_id="test-at3")
            self.assertEqual(ws.body_win_id, -1)
        finally:
            lws._SPATIAL_PATH = _orig_path
            os.unlink(tmp_path)

    # AT-4: update_confirmed_body_win_id(arrived=False) → _confirmed_body_win_id unchanged
    def test_at4_l3_nav3_arrived_false_no_update(self):
        import world.live_world_state as lws
        lws._confirmed_body_win_id = 3   # previous confirmed position
        lws.update_confirmed_body_win_id(arrived=False, goal_win_id=7)
        self.assertEqual(lws._confirmed_body_win_id, 3)  # unchanged

    # AT-5: update_confirmed_body_win_id(arrived=True, goal_win_id=7) → confirmed updated to 7
    def test_at5_l3_nav3_arrived_true_updates(self):
        import world.live_world_state as lws
        lws._confirmed_body_win_id = 3
        lws.update_confirmed_body_win_id(arrived=True, goal_win_id=7)
        self.assertEqual(lws._confirmed_body_win_id, 7)

    # Bonus: get_confirmed_body_win_id() reflects updates
    def test_bonus_get_confirmed_reflects_update(self):
        import world.live_world_state as lws
        lws._confirmed_body_win_id = -1
        lws.update_confirmed_body_win_id(arrived=True, goal_win_id=42)
        self.assertEqual(lws.get_confirmed_body_win_id(), 42)


if __name__ == "__main__":
    unittest.main()
