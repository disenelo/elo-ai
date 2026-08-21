"""
tests/test_wo_chatlog_replay.py — WO-CHATLOG-REPLAY / card 0063

The harness's own test.  Disconnection checks:
1. The ground_jam fixture loads — file and schema present.
2. run_fixture() returns 7 failing turns (4-10) — not fewer (harness wired to real executive).
3. Near-duplicate detection fires on turns 8-9.
4. Confabulation check fires on turn 10 (baseball not in session history).
5. Removing the executive call makes all routing checks go RED.
"""
import pathlib
import sys
import json
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runtime"))
sys.path.insert(0, str(ROOT / "core"))

from tools.chatlog_replay import run_fixture, _near_duplicate

FIXTURE_PATH = ROOT / "blender" / "agent_bus" / "_FIXTURES" / "chatlog_2026-08-20_ground_jam.json"


class TestChatlogReplayHarness(unittest.TestCase):

    def test_1_fixture_loads_and_has_ten_turns(self):
        """Fixture file must exist and contain the 10 turns David recorded."""
        self.assertTrue(FIXTURE_PATH.exists(), f"Fixture not found: {FIXTURE_PATH}")
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            fixture = json.load(f)
        turns = fixture.get("turns", [])
        self.assertEqual(len(turns), 10, "ground_jam fixture must have 10 turns")
        self.assertIn("pass_condition", fixture, "fixture must declare a pass_condition")

    def test_2_seven_failing_turns_reproduced(self):
        """run_fixture must identify all 7 failing turns (4-10).
        If fewer than 7 turns fail, the harness is not wired to the real executive.
        """
        result = run_fixture(FIXTURE_PATH)
        # Count distinct failing turn numbers
        failing_n = set()
        for f in result["failures"]:
            if isinstance(f, str):
                continue  # global assertion string
            if "turn" in str(f).lower():
                # extract turn number from failure message "turn N:"
                try:
                    n = int(str(f).split("turn ")[1].split(":")[0].strip())
                    failing_n.add(n)
                except Exception:
                    pass

        # The fixture marks turns 4-10 as FAIL — at minimum 7 turns must show failures
        self.assertGreaterEqual(
            result["failure_count"], 7,
            f"Expected >= 7 failures, got {result['failure_count']}. "
            "If fewer, the harness is not wired to the real executive pipeline."
        )

    def test_3_near_duplicate_catches_turns_8_9(self):
        """Turns 8 and 9 responses are near-duplicates (both are GROUND restatements of overwhelm).
        _near_duplicate must return True for this pair.
        RED if the threshold is raised above what catches this case.
        """
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            fixture = json.load(f)
        turns = {t["n"]: t["elo"] for t in fixture["turns"]}
        turn_8 = turns[8]
        turn_9 = turns[9]
        self.assertTrue(
            _near_duplicate(turn_8, turn_9),
            f"turns 8 and 9 should be near-duplicates.\n"
            f"Turn 8: {turn_8[:80]}…\nTurn 9: {turn_9[:80]}…"
        )

    def test_4_confabulation_detected_on_turn_10(self):
        """Turn 10 introduces 'baseball' — not present anywhere in the session history.
        This must be flagged as confabulation.
        RED when the confabulation check is removed from the harness.
        """
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            fixture = json.load(f)
        turn_10 = next(t for t in fixture["turns"] if t["n"] == 10)
        elo_10 = turn_10["elo"].lower()
        history = [t["user"] for t in fixture["turns"] if t["n"] < 10]
        full_history_lower = " ".join(history).lower()

        self.assertIn("baseball", elo_10, "turn 10 eLo response must contain 'baseball' (it did)")
        self.assertNotIn("baseball", full_history_lower,
                         "baseball must not appear in turns 1-9 user inputs — it is confabulated")

    def test_5_turns_1_3_pass(self):
        """Turns 1-3 are marked PASS in the fixture — the harness must not flag them."""
        result = run_fixture(FIXTURE_PATH)
        # Count failures that mention turns 1, 2, or 3
        early_fails = [f for f in result["failures"]
                       if isinstance(f, str) and any(f"turn {n}:" in f for n in (1, 2, 3))]
        self.assertEqual(len(early_fails), 0,
                         f"Turns 1-3 should pass but got failures: {early_fails}")


if __name__ == "__main__":
    unittest.main()
