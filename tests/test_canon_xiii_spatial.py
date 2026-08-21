"""
tests/test_canon_xiii_spatial.py — WO-CANON-XIII (Spatial Faculty)

Tests are staged by §. Only §A is built. §B–§F tests are marked PENDING.

§A (additive channel fields) — SQ-1, and field-presence check:

  SQ-1  A move_command with type and no route is byte-identical to the pre-XIII payload.
        (The additive fields add nothing unless the caller supplies them.)

  A-1   When the intent carries route + issued_by, both appear in move_command.

  A-2   When the intent has no route/issued_by, move_command has only {type, _ts}.

§B–§F: PENDING (Spatial Faculty not yet built; §B needs WO-CANON-XV desktop fix).
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import blender_bridge.state_writer as sw


def _capture_payload(intent: dict) -> dict:
    """Call write with a move intent and capture what _write receives."""
    captured = {}

    def _fake_write(payload: dict) -> dict:
        captured.update(payload)
        return {"ok": True}

    with patch.object(sw, "_write", side_effect=_fake_write):
        sw.write(
            motion={"animation": "idle", "speed": 0},
            intent=intent,
        )
    return captured


class TestCanonXIIISpatial(unittest.TestCase):

    # ── SQ-1: no route → byte-identical to pre-XIII ───────────────────────────

    def test_sq1_no_route_byte_identical(self):
        """A move intent without route produces a move_command with exactly {type, _ts}.

        Disconnection: add a default route or issued_by to move_command → SQ-1 RED.
        """
        intent = {"name": "move", "direction": "right"}
        payload = _capture_payload(intent)

        self.assertIn("move_command", payload, "move_command missing from payload")
        mc = payload["move_command"]

        self.assertIn("type",  mc, "move_command.type missing")
        self.assertIn("_ts",   mc, "move_command._ts missing")
        self.assertNotIn(
            "route", mc,
            "move_command contains 'route' when none was supplied — "
            "the §A additive fields must ONLY appear when the caller provides them."
        )
        self.assertNotIn(
            "issued_by", mc,
            "move_command contains 'issued_by' when none was supplied — "
            "SQ-1 backwards-compatibility guarantee is broken."
        )
        # Exact key set: {type, _ts}
        self.assertEqual(
            set(mc.keys()), {"type", "_ts"},
            f"move_command has unexpected keys: {set(mc.keys())} — expected exactly {{type, _ts}}. "
            "SQ-1: the pre-XIII payload shape must be preserved when route is absent."
        )

    # ── A-1: route + issued_by appear when supplied ───────────────────────────

    def test_a1_route_and_issued_by_appear_when_supplied(self):
        """When the intent carries route and issued_by, both are forwarded into move_command.

        Disconnection: remove the WO-CANON-XIII §A additive block → this test RED.
        """
        sample_route = [
            {
                "verb":        "LEDGE_RUN",
                "to":          {"surface_id": "window_1", "anchor": "top_ledge"},
                "precondition": [],
                "expected_ms": 600,
            }
        ]
        intent = {
            "name":      "move",
            "direction": "right",
            "route":     sample_route,
            "issued_by": "SpatialFaculty",
        }
        payload = _capture_payload(intent)

        mc = payload.get("move_command", {})
        self.assertIn(
            "route", mc,
            "move_command does not contain 'route' even though the intent supplied one. "
            "WO-CANON-XIII §A additive block is absent or broken."
        )
        self.assertEqual(
            mc["route"], sample_route,
            "move_command.route does not match the supplied route."
        )
        self.assertIn(
            "issued_by", mc,
            "move_command does not contain 'issued_by' even though the intent supplied one."
        )
        self.assertEqual(
            mc["issued_by"], "SpatialFaculty",
            "move_command.issued_by does not match the supplied value."
        )
        # type and _ts still present (no regression)
        self.assertIn("type", mc, "move_command.type missing (regression)")
        self.assertIn("_ts",  mc, "move_command._ts missing (regression)")

    # ── A-2: no route/issued_by → clean minimal payload ──────────────────────

    def test_a2_partial_intent_no_extras(self):
        """An intent with sub_type (no route) produces move_command without route/issued_by.

        Tests the write_with_presence code path (second occurrence in state_writer.py).
        """
        captured = {}

        def _fake_write(payload: dict) -> dict:
            captured.update(payload)
            return {"ok": True}

        intent = {"name": "move", "sub_type": "fire_jump"}
        with patch.object(sw, "_write", side_effect=_fake_write):
            sw.write_with_presence(
                motion={"animation": "idle", "speed": 0},
                intent=intent,
            )

        mc = captured.get("move_command", {})
        self.assertNotIn(
            "route", mc,
            f"write_with_presence added 'route' when none was supplied. Keys: {list(mc.keys())}"
        )
        self.assertNotIn(
            "issued_by", mc,
            f"write_with_presence added 'issued_by' when none was supplied. Keys: {list(mc.keys())}"
        )
        self.assertEqual(mc.get("type"), "fire_jump",
                         "move_command.type should be 'fire_jump'")


if __name__ == "__main__":
    unittest.main()
