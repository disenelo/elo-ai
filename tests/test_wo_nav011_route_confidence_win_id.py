"""
tests/test_wo_nav011_route_confidence_win_id.py — WO-NAV-011 acceptance tests.

SP-14: route_confidence_by_win_id(target_win_id, route_history) → float.
Also verifies goal_win_id field is recorded by remember_route().
"""
import sys
import os
import json
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from self.route_memory import route_confidence_by_win_id, remember_route


def _rec(target_win_id, arrived):
    return {"goal_win_id": target_win_id, "arrived": arrived}


class TestSP14RouteConfidenceByWinId(unittest.TestCase):

    # AT-1: no history → neutral prior 0.5
    def test_at1_no_history_returns_neutral_prior(self):
        self.assertAlmostEqual(route_confidence_by_win_id(42, []), 0.5)

    # AT-2: no records with matching goal_win_id → 0.5
    def test_at2_no_matching_win_id_returns_neutral(self):
        history = [_rec(99, True), _rec(99, True)]
        self.assertAlmostEqual(route_confidence_by_win_id(42, history), 0.5)

    # AT-3: all arrivals → 1.0
    def test_at3_all_arrivals_returns_one(self):
        history = [_rec(5, True), _rec(5, True), _rec(5, True)]
        self.assertAlmostEqual(route_confidence_by_win_id(5, history), 1.0)

    # AT-4: all failures → epsilon (not 0.0)
    def test_at4_all_failures_returns_epsilon(self):
        history = [_rec(5, False), _rec(5, False)]
        result = route_confidence_by_win_id(5, history)
        self.assertGreater(result, 0.0)
        self.assertLess(result, 0.1)

    # AT-5: mixed — 2 arrivals / 4 attempts → 0.5
    def test_at5_mixed_returns_correct_ratio(self):
        history = [_rec(7, True), _rec(7, False), _rec(7, True), _rec(7, False)]
        self.assertAlmostEqual(route_confidence_by_win_id(7, history), 0.5)

    # AT-6: records without goal_win_id key → not counted
    def test_at6_records_without_goal_win_id_not_counted(self):
        history = [{"arrived": True}, {"arrived": True}]  # no goal_win_id
        self.assertAlmostEqual(route_confidence_by_win_id(1, history), 0.5)

    # AT-7: remember_route writes goal_win_id to JSONL record
    def test_at7_remember_route_records_goal_win_id(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            tmp_path = f.name
        try:
            remember_route(
                goal_surface="window-5",
                legs=["jump"],
                arrived=True,
                fell=False,
                duration_s=1.2,
                smoothness=1.0,
                ack_id="test-ack-001",
                ack_received=True,
                goal_win_id=5,
                log_path=tmp_path,
            )
            with open(tmp_path, encoding="utf-8") as f:
                rec = json.loads(f.read().strip())
            self.assertEqual(rec["goal_win_id"], 5)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
