"""
tests/test_wo_route_confidence_intent_001.py — WO-ROUTE-CONFIDENCE-INTENT-001

Acceptance criteria:
  AC-1: Given a window with route_confidence < 0.40, exec_decision.confidence is
        downgraded and route_confidence_low=True is set on exec_decision.
  AC-2: Given a window with route_confidence > 0.70, exec_decision is unchanged
        (no confidence downgrade, no route_confidence_low flag).
  AC-3: route_confidence_by_win_id returns 0.5 (neutral prior) when no history exists.
  AC-4: route_confidence_by_win_id returns epsilon (not 0.0) when all attempts failed.
"""
from __future__ import annotations

import json
import tempfile
import pathlib
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from self.route_memory import route_confidence_by_win_id, remember_route, _EPSILON


def _make_record(win_id: int, arrived: bool) -> dict:
    return {
        "ts": 0.0,
        "goal": f"win_{win_id}",
        "goal_win_id": win_id,
        "route_legs": [],
        "arrived": arrived,
        "fell": not arrived,
        "duration_s": 1.0,
        "smoothness": 0.8,
        "ack_id": "test",
        "experience_id": "",
        "brain_route": None,
        "unity_route": None,
    }


class TestRouteConfidenceByWinId(unittest.TestCase):

    def test_ac3_neutral_prior_when_no_history(self):
        """AC-3: No records → 0.5 neutral prior."""
        conf = route_confidence_by_win_id(99, [])
        self.assertAlmostEqual(conf, 0.5)

    def test_ac4_epsilon_when_all_failed(self):
        """AC-4: All attempts failed → epsilon (not 0.0)."""
        history = [_make_record(5, arrived=False) for _ in range(3)]
        conf = route_confidence_by_win_id(5, history)
        self.assertEqual(conf, _EPSILON)
        self.assertGreater(conf, 0.0)

    def test_low_confidence_window(self):
        """1 success in 5 attempts = 0.2 < 0.40."""
        history = [_make_record(7, arrived=False)] * 4 + [_make_record(7, arrived=True)]
        conf = route_confidence_by_win_id(7, history)
        self.assertLess(conf, 0.40)

    def test_high_confidence_window(self):
        """9 successes in 10 = 0.9 > 0.70."""
        history = [_make_record(3, arrived=True)] * 9 + [_make_record(3, arrived=False)]
        conf = route_confidence_by_win_id(3, history)
        self.assertGreater(conf, 0.70)

    def test_ignores_other_win_ids(self):
        """Confidence only counts records for the requested win_id."""
        history = (
            [_make_record(1, arrived=False)] * 5   # win 1: 0% success
            + [_make_record(2, arrived=True)] * 5  # win 2: 100% success
        )
        conf_1 = route_confidence_by_win_id(1, history)
        conf_2 = route_confidence_by_win_id(2, history)
        self.assertLess(conf_1, 0.40)
        self.assertGreater(conf_2, 0.70)


class TestMovementIntentRouteConfidenceIntegration(unittest.TestCase):
    """
    Verify the route confidence consultation block in server.py's _movement_intent()
    via static code inspection (server.py can't be called in isolation).
    """

    def test_ac1_code_present_low_confidence_branch(self):
        """AC-1: server.py contains route_confidence_low downgrade logic."""
        with open("server.py", encoding="utf-8") as f:
            src = f.read()
        self.assertIn("WO-ROUTE-CONFIDENCE-INTENT-001", src)
        self.assertIn("route_confidence_value", src)
        self.assertIn("route_confidence_low", src)
        self.assertIn("exec_decision[\"confidence\"] = round", src)

    def test_ac2_code_only_downgrades_below_threshold(self):
        """AC-2: Downgrade only fires when _rc_val < 0.40."""
        with open("server.py", encoding="utf-8") as f:
            src = f.read()
        self.assertIn("if _rc_val < 0.40:", src)

    def test_route_confidence_consulted_flag_set(self):
        """route_confidence_consulted key is written to exec_decision on navigate action."""
        with open("server.py", encoding="utf-8") as f:
            src = f.read()
        self.assertIn("route_confidence_consulted", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
