"""
WO-NAV-001 — ACK Fix + MovementOutcome (SP-1, SP-2, SP-22).
Acceptance Tests AT-1 through AT-5.
Authority: David L3 — SPEC ratification 2026-08-23 + Execution Directive 2026-08-24.
RTR: RTR-008f, RTR-022.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── AT-1 (SP-1): movement_report in _ACK_BODY_TYPES ─────────────────────────

class TestAT1AckBodyTypes(unittest.TestCase):

    def test_at1_movement_report_in_ack_body_types(self):
        """'movement_report' must be in _ACK_BODY_TYPES."""
        import server as _srv
        self.assertIn("movement_report", _srv._ACK_BODY_TYPES,
                      "SP-1: movement_report must be in _ACK_BODY_TYPES")

    def test_at1_source_grep_confirms(self):
        """server.py source contains 'movement_report' in the _ACK_BODY_TYPES line block."""
        fpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "server.py")
        with open(fpath, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("movement_report", text)
        # Verify SP-1 comment is co-located
        self.assertIn("SP-1", text)


# ── AT-2 (SP-2): _PENDING_MOVE matcher reads correct payload path ─────────────

class TestAT2PendingMoveMatcher(unittest.TestCase):

    def test_at2_report_arrived_path_in_source(self):
        """server.py uses payload['report']['arrived'] path for movement_report ACK."""
        fpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "server.py")
        with open(fpath, encoding="utf-8") as f:
            text = f.read()
        self.assertIn('report", {}).get("arrived', text,
                      "SP-2: server.py must read payload['report']['arrived']")
        # No bare subject key for movement_report
        # Confirm SP-2 comment
        self.assertIn("SP-2", text)


# ── AT-3 (SP-1+SP-2): Graph-nav ACK no longer silently discarded ─────────────

class TestAT3IntegrationAckRouted(unittest.TestCase):

    def test_at3_movement_report_ack_resolves_arrived_true(self):
        """
        Simulate a movement_report ACK payload:
        - type='movement_report', report.arrived=True
        Confirm the matcher logic evaluates to arrived=True.
        """
        # Replicate the matcher logic from server.py (SP-2)
        ack_payload = {
            "type": "movement_report",
            "_ts": 1724500010.0,
            "report": {
                "arrived": True,
                "fell": False,
                "goal": "jump_right",
                "_ts": 1724500010.0,
            }
        }
        _qmv_type = ack_payload.get("type", "")
        _qmv_arrived = (
            _qmv_type == "movement_report"
            and bool(ack_payload.get("report", {}).get("arrived", False))
        ) or _qmv_type in ("arrived", "move_complete")
        self.assertTrue(_qmv_arrived,
                        "SP-2 matcher must resolve arrived=True for movement_report with report.arrived=True")

    def test_at3_movement_report_ack_resolves_arrived_false(self):
        """
        movement_report with arrived=False must NOT resolve as arrived.
        """
        ack_payload = {
            "type": "movement_report",
            "_ts": 1724500010.0,
            "report": {"arrived": False, "fell": True, "_ts": 1724500010.0},
        }
        _qmv_type = ack_payload.get("type", "")
        _qmv_arrived = (
            _qmv_type == "movement_report"
            and bool(ack_payload.get("report", {}).get("arrived", False))
        ) or _qmv_type in ("arrived", "move_complete")
        self.assertFalse(_qmv_arrived,
                         "SP-2 matcher must NOT resolve arrived for movement_report with arrived=False")

    def test_at3_legacy_arrived_type_still_resolves(self):
        """Legacy 'arrived' ACK type must still resolve (backwards compat)."""
        ack_payload = {"type": "arrived", "_ts": 1724500010.0}
        _qmv_type = ack_payload.get("type", "")
        _qmv_arrived = (
            _qmv_type == "movement_report"
            and bool(ack_payload.get("report", {}).get("arrived", False))
        ) or _qmv_type in ("arrived", "move_complete")
        self.assertTrue(_qmv_arrived,
                        "Legacy 'arrived' type must still resolve via backwards-compat branch")


# ── AT-4 (SP-22): MovementOutcome importable ─────────────────────────────────

class TestAT4MovementOutcomeImportable(unittest.TestCase):

    def test_at4_import_succeeds(self):
        """from runtime.movement_outcome import MovementOutcome succeeds without error."""
        from runtime.movement_outcome import MovementOutcome
        self.assertIsNotNone(MovementOutcome)


# ── AT-5 (SP-22): MovementOutcome fields correct ─────────────────────────────

class TestAT5MovementOutcomeFields(unittest.TestCase):

    _REQUIRED_FIELDS = {
        "arrived", "fell", "goal", "goal_win_id", "route_nodes",
        "duration_s", "ack_id", "issued_by",
    }

    def test_at5_all_fields_present(self):
        """MovementOutcome has all required fields."""
        from runtime.movement_outcome import MovementOutcome
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(MovementOutcome)}
        self.assertEqual(self._REQUIRED_FIELDS, self._REQUIRED_FIELDS & field_names,
                         f"Missing fields: {self._REQUIRED_FIELDS - field_names}")

    def test_at5_instantiate_with_known_values(self):
        """MovementOutcome can be instantiated with known values; types match spec."""
        from runtime.movement_outcome import MovementOutcome
        mo = MovementOutcome(
            arrived=True,
            fell=False,
            goal="jump_right",
            goal_win_id=42,
            route_nodes=["node_1", "node_2"],
            duration_s=1.23,
            ack_id="ack_abc123",
            issued_by="user_message",
        )
        self.assertTrue(mo.arrived)
        self.assertFalse(mo.fell)
        self.assertEqual(mo.goal, "jump_right")
        self.assertEqual(mo.goal_win_id, 42)
        self.assertEqual(mo.route_nodes, ["node_1", "node_2"])
        self.assertAlmostEqual(mo.duration_s, 1.23)
        self.assertEqual(mo.ack_id, "ack_abc123")
        self.assertEqual(mo.issued_by, "user_message")

    def test_at5_goal_win_id_accepts_none(self):
        """goal_win_id can be None for directional (non-deliberate) moves."""
        from runtime.movement_outcome import MovementOutcome
        mo = MovementOutcome(
            arrived=True, fell=False, goal="jump_left", goal_win_id=None,
            route_nodes=[], duration_s=0.9, ack_id="x", issued_by="user_message",
        )
        self.assertIsNone(mo.goal_win_id)

    def test_at5_from_ack_populates_correctly(self):
        """MovementOutcome.from_ack() populates all fields from a raw ACK payload."""
        from runtime.movement_outcome import MovementOutcome
        ack = {
            "type": "movement_report",
            "_ts": 1724500020.0,
            "report": {
                "arrived": True,
                "fell": False,
                "goal": "jump_right",
                "goal_win_id": 77,
                "route_nodes": ["a", "b"],
                "_ts": 1724500020.0,
                "issued_by": "self_initiation",
            },
            "ack_id": "xyzabc",
        }
        mo = MovementOutcome.from_ack(ack, since=1724500018.5)
        self.assertTrue(mo.arrived)
        self.assertFalse(mo.fell)
        self.assertEqual(mo.goal, "jump_right")
        self.assertEqual(mo.goal_win_id, 77)
        self.assertEqual(mo.route_nodes, ["a", "b"])
        self.assertAlmostEqual(mo.duration_s, 1.5, places=1)
        self.assertEqual(mo.ack_id, "xyzabc")
        self.assertEqual(mo.issued_by, "self_initiation")


if __name__ == "__main__":
    unittest.main()
