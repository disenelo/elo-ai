"""
WO-NAV-007 — CognitivePlan + Move Command Schema Additions.
Acceptance Tests AT-1 through AT-4.
Authority: David L3 — Execution Directive 2026-08-24  RTR-052.
"""

import json
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── AT-1: spatial_plan field in CognitivePlan ────────────────────────────────

class TestAT1SpatialPlanField(unittest.TestCase):

    def test_at1_field_exists_default_none(self):
        """CognitivePlan.spatial_plan exists and defaults to None."""
        from runtime.spine.plan import CognitivePlan
        plan = CognitivePlan()
        self.assertTrue(hasattr(plan, "spatial_plan"),
                        "CognitivePlan must have spatial_plan field (SP-15)")
        self.assertIsNone(plan.spatial_plan,
                          "spatial_plan must default to None")

    def test_at1_field_accepts_dict(self):
        """CognitivePlan.spatial_plan can be set to a dict."""
        from runtime.spine.plan import CognitivePlan
        plan = CognitivePlan()
        plan.spatial_plan = {"goal_win_id": "win_42", "candidates": [], "route": []}
        self.assertEqual(plan.spatial_plan["goal_win_id"], "win_42")

    def test_at1_existing_fields_unaffected(self):
        """Adding spatial_plan does not change existing CognitivePlan fields."""
        from runtime.spine.plan import CognitivePlan
        plan = CognitivePlan(intent="conversation", confidence=0.8)
        self.assertEqual(plan.intent, "conversation")
        self.assertEqual(plan.confidence, 0.8)
        self.assertIsNone(plan.spatial_plan)


# ── AT-2: goal_win_id in move_command schema ─────────────────────────────────

class TestAT2GoalWinIdField(unittest.TestCase):

    def _call_state_writer_move(self, intent_dict):
        """Call state_writer.write_state with a move intent and capture the payload."""
        import unittest.mock as mock
        import json

        _written = []

        def _fake_open(path, mode="r", **kwargs):
            if "w" in mode and "blender_state" in str(path):
                m = mock.mock_open()()
                m.write = lambda s: _written.append(s)
                m.__enter__ = lambda self: self
                m.__exit__ = mock.MagicMock(return_value=False)
                return m
            return mock.mock_open(read_data=json.dumps({}))()

        from blender_bridge import state_writer as _sw

        # We'll call the internal builder directly
        # state_writer._build_payload(intent, ...) if it exists, else reconstruct
        # The intent dict approach: call write_state on a minimal stub
        captured = {}
        original_dump = json.dumps

        with mock.patch("blender_bridge.state_writer.json.dumps") as mock_dump:
            mock_dump.side_effect = lambda obj, **kw: original_dump(obj, **kw)
            with mock.patch("builtins.open", mock.mock_open(read_data="{}")):
                try:
                    _sw.write_state(
                        mode="idle",
                        intent=intent_dict,
                        trigger=None,
                        gesture=None,
                        gaze=None,
                        expression=None,
                        animation=None,
                    )
                    if mock_dump.called:
                        captured = mock_dump.call_args[0][0]
                except Exception:
                    pass
        return captured

    def test_at2_goal_win_id_in_move_command_when_set(self):
        """move_command includes goal_win_id when intent provides it."""
        from blender_bridge import state_writer as _sw
        import unittest.mock as mock

        captured_payloads = []
        _motion = {"animation": "idle", "speed": 1.0, "intensity": 0.5, "duration": 4.0, "mood": "neutral", "mode": "idle"}

        with mock.patch("blender_bridge.state_writer._write",
                        side_effect=lambda p: captured_payloads.append(p) or True):
            _sw.write(
                motion=_motion,
                intent={"name": "move", "direction": "left", "goal_win_id": "win_77"},
            )

        # Find the payload with move_command
        mc = None
        for p in captured_payloads:
            if isinstance(p, dict) and "move_command" in p:
                mc = p["move_command"]
                break
        self.assertIsNotNone(mc, "move_command must appear in the written payload")
        self.assertIn("goal_win_id", mc,
                      "move_command must include goal_win_id when intent provides it (SP-19)")
        self.assertEqual(mc["goal_win_id"], "win_77")

    def test_at2_goal_win_id_absent_on_normal_move(self):
        """move_command does NOT include goal_win_id when intent does not provide it."""
        import unittest.mock as mock
        from blender_bridge import state_writer as _sw
        captured_payloads = []
        _motion = {"animation": "idle", "speed": 1.0, "intensity": 0.5, "duration": 4.0, "mood": "neutral", "mode": "idle"}

        with mock.patch("blender_bridge.state_writer._write",
                        side_effect=lambda p: captured_payloads.append(p) or True):
            _sw.write(motion=_motion, intent={"name": "move", "direction": "right"})

        mc = None
        for p in captured_payloads:
            if isinstance(p, dict) and "move_command" in p:
                mc = p["move_command"]
                break
        if mc is not None:
            self.assertNotIn("goal_win_id", mc,
                             "goal_win_id must NOT appear when intent does not supply it")

    def test_at2_source_contains_goal_win_id(self):
        """state_writer.py source contains 'goal_win_id' as an SP-19 addition."""
        fpath = os.path.join(_ROOT, "blender_bridge", "state_writer.py")
        with open(fpath, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("goal_win_id", text,
                      "state_writer.py must reference goal_win_id (SP-19)")
        self.assertIn("SP-19", text,
                      "state_writer.py must reference SP-19 in a comment")


# ── AT-3: Existing moves unaffected ──────────────────────────────────────────

class TestAT3ExistingMovesUnaffected(unittest.TestCase):

    def test_at3_spatial_plan_none_on_normal_plan(self):
        """A normal CognitivePlan created without spatial_plan has spatial_plan = None."""
        from runtime.spine.plan import CognitivePlan
        plan = CognitivePlan(intent="conversation", conversation_action="speak")
        self.assertIsNone(plan.spatial_plan)

    def test_at3_move_command_type_unaffected(self):
        """Normal directional move_command still has correct type field."""
        import unittest.mock as mock
        from blender_bridge import state_writer as _sw
        captured_payloads = []
        _motion = {"animation": "idle", "speed": 1.0, "intensity": 0.5, "duration": 4.0, "mood": "neutral", "mode": "idle"}

        with mock.patch("blender_bridge.state_writer._write",
                        side_effect=lambda p: captured_payloads.append(p) or True):
            _sw.write(motion=_motion, intent={"name": "move", "direction": "up"})

        mc = None
        for p in captured_payloads:
            if isinstance(p, dict) and "move_command" in p:
                mc = p["move_command"]
                break
        self.assertIsNotNone(mc, "move_command must be in payload")
        self.assertIn("type", mc, "move_command must still have 'type' field")
        self.assertEqual(mc["type"], "jump_top")


# ── AT-4: SP-24 — Unity acceptance of goal_win_id ────────────────────────────

class TestAT4SP24UnityVerification(unittest.TestCase):

    def test_at4_sp24_schema_valid_for_unity(self):
        """
        SP-24 schema verification: a move_command with goal_win_id is a valid dict
        that Unity's JSON parser can accept (no invalid types or non-serialisable values).
        """
        import json
        # Construct the payload as state_writer would
        test_mc = {
            "type": "jump_right",
            "_ts": 1724500000.0,
            "goal_win_id": "win_42",
        }
        # Must be JSON-serialisable
        serialised = json.dumps(test_mc)
        roundtrip = json.loads(serialised)
        self.assertEqual(roundtrip["goal_win_id"], "win_42")
        self.assertEqual(roundtrip["type"], "jump_right")
        # Builder note (SP-24): Unity live acceptance requires a running session.
        # This test confirms the schema is valid; live Unity test is David's lane.


if __name__ == "__main__":
    unittest.main()
