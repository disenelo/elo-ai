"""
tests/test_canon_xiii_spatial.py — WO-CANON-XIII (Spatial Faculty)

§A (additive channel fields):
  SQ-1  move_command with no route is byte-identical to pre-XIII.
  A-1   route + issued_by appear when supplied.
  A-2   no route → no extras.

§B (Spatial Faculty data model + core logic — WO-CANON-XIII §B):
  FT-1  82px gap vs max_jump_d=75 → UNREACHABLE, margin=-7, blocked_by has numbers.
  FT-2  Unreachable gap → detour route (SLIDE → APPROACH → CLIMB).
  FT-3  PEEK precondition: every LEAP must be immediately preceded by PEEK.
  FT-4  GO_BEHIND affordance exists on window_body surface.
  FT-5  Landing narrower than body.width_px → surface available=False.
  FT-6  PERIPHERAL presence → NoRoute("peripheral_presence"), no planning.
  FT-7  NoRoute has reason string; not a Route; no movement or arrival claim.
  ST-1  Stale desktop domain → map confidence drops; no cross-surface route.
  ST-2  max_jump_d=None → UNREACHABLE, blocked_by says disabled.
  SQ-3  world/live_world_state.py has no competing spatial planning symbols.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest
from dataclasses import dataclass
from unittest.mock import patch

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import blender_bridge.state_writer as sw
from faculties.spatial.spatial_faculty import (
    BodySchema, Surface, DesktopWorldMap, RouteLeg, Route, NoRoute,
    Reachability, RoutePreconditionError,
    SURF_WINDOW_TOP, SURF_WINDOW_BODY, SURF_DESKTOP_FLOOR,
    AFF_GO_BEHIND, AFF_GAP_LEAP,
    VERB_LEAP, VERB_PEEK, VERB_SLIDE, VERB_APPROACH, VERB_CLIMB,
    VERDICT_REACHABLE, VERDICT_UNREACHABLE,
    PRESENCE_PERIPHERAL, PRESENCE_ACTIVE,
    check_reachability, plan_route, validate_route,
    affordances_for_type, build_map, presence_from_live_state,
)


# ── Minimal stubs ─────────────────────────────────────────────────────────────

@dataclass
class _UserState:
    focus_state: str = "unknown"

@dataclass
class _LiveState:
    user: _UserState = None
    domain_health: dict = None

    def __post_init__(self):
        if self.user is None:
            self.user = _UserState()
        if self.domain_health is None:
            self.domain_health = {}


@dataclass
class _FakeWindow:
    """Minimal WindowBounds-like object for build_map."""
    app: str
    x: int
    y: int
    w: int
    h: int


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


class TestCanonXIIISpatialB(unittest.TestCase):
    """WO-CANON-XIII §B — Spatial Faculty data model + core logic."""

    # ── Helper surfaces ───────────────────────────────────────────────────────

    def _top(self, surface_id="window_Chrome_top", x=0, y=0, w=800, h=4,
             available=True) -> Surface:
        return Surface(
            surface_id=surface_id,
            surface_type=SURF_WINDOW_TOP,
            rect=(x, y, w, h),
            affordances=affordances_for_type(SURF_WINDOW_TOP),
            available=available,
        )

    def _floor(self, x=0, y=1439, w=2560, h=1) -> Surface:
        return Surface(
            surface_id="desktop_floor",
            surface_type=SURF_DESKTOP_FLOOR,
            rect=(x, y, w, h),
            affordances=affordances_for_type(SURF_DESKTOP_FLOOR),
            available=True,
        )

    # ── FT-1 ─────────────────────────────────────────────────────────────────

    def test_ft1_gap_unreachable_margin_named(self):
        """82px gap vs max_jump_d=75 → UNREACHABLE, margin=-7, blocked_by names both numbers."""
        body = BodySchema(max_jump_d=75)
        r = check_reachability(82, body)

        self.assertEqual(r.verdict, VERDICT_UNREACHABLE)
        self.assertEqual(r.margin, -7)
        self.assertIn("82", r.blocked_by, "gap_px absent from blocked_by")
        self.assertIn("75", r.blocked_by, "max_jump_d absent from blocked_by")
        self.assertFalse(r.direct_ok)

    # ── FT-2 ─────────────────────────────────────────────────────────────────

    def test_ft2_unreachable_routes_around(self):
        """Unreachable direct gap → detour: SLIDE → APPROACH → CLIMB."""
        body = BodySchema(max_jump_d=75)
        # gap between: floor right edge=2560, target starts at 2560+82=2642 → gap=82
        from_surf = self._top("window_A_top", x=0, y=0, w=400)
        to_surf   = self._top("window_B_top", x=482, y=0, w=400)  # 82px gap

        result = plan_route(from_surf, to_surf, body, presence=PRESENCE_ACTIVE)

        self.assertIsInstance(result, Route, "Expected Route, got NoRoute")
        verbs = [l.verb for l in result.legs]
        self.assertIn(VERB_SLIDE,    verbs, "SLIDE leg absent in detour route")
        self.assertIn(VERB_APPROACH, verbs, "APPROACH leg absent in detour route")
        self.assertIn(VERB_CLIMB,    verbs, "CLIMB leg absent in detour route")
        self.assertNotIn(VERB_LEAP,  verbs, "LEAP should not appear in a detour route")

    # ── FT-3 ─────────────────────────────────────────────────────────────────

    def test_ft3_leap_requires_preceding_peek(self):
        """A LEAP without an immediately preceding PEEK raises RoutePreconditionError."""
        bad_route = Route(legs=(
            RouteLeg(verb=VERB_LEAP, to={"surface_id": "x"}, precondition=("PEEK",)),
        ))
        with self.assertRaises(RoutePreconditionError):
            validate_route(bad_route)

    def test_ft3_valid_peek_leap_accepted(self):
        """PEEK immediately before LEAP passes validation without exception."""
        good_route = Route(legs=(
            RouteLeg(verb=VERB_PEEK, to={"surface_id": "x"}),
            RouteLeg(verb=VERB_LEAP, to={"surface_id": "x"}, precondition=("PEEK",)),
        ))
        validate_route(good_route)   # must not raise

    def test_ft3_plan_route_reachable_includes_peek_before_leap(self):
        """A reachable plan_route produces PEEK immediately before LEAP."""
        body = BodySchema(max_jump_d=75)
        from_surf = self._top("A", x=0, y=0, w=400)
        to_surf   = self._top("B", x=460, y=0, w=400)  # 60px gap — reachable

        result = plan_route(from_surf, to_surf, body, presence=PRESENCE_ACTIVE)
        self.assertIsInstance(result, Route)

        legs = list(result.legs)
        for i, leg in enumerate(legs):
            if leg.verb == VERB_LEAP:
                self.assertGreater(i, 0, "LEAP is first leg — no PEEK possible before it")
                self.assertEqual(legs[i - 1].verb, VERB_PEEK,
                                 f"Leg before LEAP at index {i} is not PEEK")

    # ── FT-4 ─────────────────────────────────────────────────────────────────

    def test_ft4_go_behind_on_window_body(self):
        """GO_BEHIND affordance is in the window_body surface affordance set."""
        affs = affordances_for_type(SURF_WINDOW_BODY)
        self.assertIn(AFF_GO_BEHIND, affs,
                      "GO_BEHIND not in window_body affordances — eLo cannot go behind windows")

    # ── FT-5 ─────────────────────────────────────────────────────────────────

    def test_ft5_narrow_landing_unavailable(self):
        """Surface with width < body.width_px is built as available=False."""
        body = BodySchema(width_px=40)
        narrow_win = _FakeWindow(app="Narrow", x=500, y=100, w=30, h=600)
        world_map = build_map([narrow_win], screen=(2560, 1440), body=body)

        top_surf = next((s for s in world_map.surfaces
                         if s.surface_id == "window_Narrow_top"), None)
        self.assertIsNotNone(top_surf, "window_Narrow_top surface not found in map")
        self.assertFalse(top_surf.available,
                         "Narrow landing (30px < 40px body width) should be available=False")

    def test_ft5_wide_landing_available(self):
        """Surface with width >= body.width_px is available=True."""
        body = BodySchema(width_px=40)
        wide_win = _FakeWindow(app="Wide", x=0, y=0, w=800, h=600)
        world_map = build_map([wide_win], screen=(2560, 1440), body=body)

        top_surf = next((s for s in world_map.surfaces
                         if s.surface_id == "window_Wide_top"), None)
        self.assertIsNotNone(top_surf)
        self.assertTrue(top_surf.available)

    # ── FT-6 ─────────────────────────────────────────────────────────────────

    def test_ft6_peripheral_no_route(self):
        """PERIPHERAL presence → NoRoute(reason='peripheral_presence'), not planned-then-cancelled."""
        body = BodySchema(max_jump_d=75)
        from_surf = self._top("A", x=0, y=0, w=400)
        to_surf   = self._top("B", x=410, y=0, w=400)  # adjacent — would be reachable

        result = plan_route(from_surf, to_surf, body, presence=PRESENCE_PERIPHERAL)

        self.assertIsInstance(result, NoRoute, "Expected NoRoute for PERIPHERAL, got Route")
        self.assertEqual(result.reason, "peripheral_presence")

    def test_ft6_presence_from_live_state_focused(self):
        """LiveWorldState user.focus_state='focused' maps to PRESENCE_PERIPHERAL."""
        state = _LiveState(user=_UserState(focus_state="focused"))
        self.assertEqual(presence_from_live_state(state), PRESENCE_PERIPHERAL)

    # ── FT-7 ─────────────────────────────────────────────────────────────────

    def test_ft7_no_route_has_reason(self):
        """NoRoute carries a non-empty reason; it is not a Route."""
        nr = NoRoute(reason="no_gap_leap_affordance")
        self.assertIsInstance(nr, NoRoute)
        self.assertNotIsInstance(nr, Route)
        self.assertIsInstance(nr.reason, str)
        self.assertGreater(len(nr.reason), 0, "NoRoute.reason is empty")

    def test_ft7_unavailable_surface_gives_no_route(self):
        """Targeting an unavailable surface (closed, too narrow) returns NoRoute."""
        body = BodySchema()
        from_surf = self._floor()
        to_surf   = self._top("Closed", x=0, y=0, w=200, available=False)

        result = plan_route(from_surf, to_surf, body)
        self.assertIsInstance(result, NoRoute)
        self.assertIn("surface_unavailable", result.reason)

    # ── ST-1 ─────────────────────────────────────────────────────────────────

    def test_st1_stale_desktop_confidence_drops(self):
        """Stale desktop domain → DesktopWorldMap.confidence reflects the low domain confidence."""
        low_conf = 0.2
        win = _FakeWindow(app="Chrome", x=0, y=0, w=1200, h=800)
        world_map = build_map([win], screen=(2560, 1440), domain_confidence=low_conf)

        self.assertAlmostEqual(world_map.confidence, low_conf, places=5,
                               msg="Map confidence should carry domain confidence verbatim")

    def test_st1_stale_domain_no_route_in_shadow(self):
        """shadow_plan with stale desktop domain exits without planning (logs stale gate)."""
        import io, contextlib

        state = _LiveState(domain_health={
            "desktop": {"status": "stale", "confidence": 0.1},
        })
        wins = [_FakeWindow(app="X", x=0, y=0, w=600, h=400)]

        # Should not raise; stale domain exits before planning
        try:
            from faculties.spatial.spatial_faculty import shadow_plan
            shadow_plan(state, wins, target_surface_id="window_X_top")
        except Exception as exc:
            self.fail(f"shadow_plan raised on stale domain: {exc}")

    # ── ST-2 ─────────────────────────────────────────────────────────────────

    def test_st2_max_jump_d_none_all_leaps_unreachable(self):
        """max_jump_d=None → every gap is UNREACHABLE; blocked_by says 'disabled'."""
        body = BodySchema(max_jump_d=None)

        for gap in (1, 10, 50, 100, 500):
            r = check_reachability(gap, body)
            self.assertEqual(r.verdict, VERDICT_UNREACHABLE,
                             f"Gap {gap}px should be UNREACHABLE when max_jump_d=None")
            self.assertIn("None", r.blocked_by,
                          f"blocked_by should mention None for gap {gap}")

    def test_st2_max_jump_d_none_no_gap_leap_in_plan(self):
        """With max_jump_d=None, plan_route never produces a LEAP leg."""
        body = BodySchema(max_jump_d=None)
        from_surf = self._top("A", x=0, y=0, w=400)
        to_surf   = self._top("B", x=450, y=0, w=400)  # 50px gap

        result = plan_route(from_surf, to_surf, body, presence=PRESENCE_ACTIVE)

        if isinstance(result, Route):
            verbs = [l.verb for l in result.legs]
            self.assertNotIn(VERB_LEAP, verbs,
                             "LEAP appeared in route even with max_jump_d=None")

    # ── SQ-3 ─────────────────────────────────────────────────────────────────

    def test_sq3_no_rival_spatial_model_in_live_world_state(self):
        """
        world/live_world_state.py must not contain spatial planning symbols.

        Spatial reasoning belongs in faculties/spatial/ — any of these symbols
        in live_world_state.py would create a competing spatial model.
        """
        lws_path = ROOT / "world" / "live_world_state.py"
        self.assertTrue(lws_path.exists(), f"world/live_world_state.py not found at {lws_path}")
        source = lws_path.read_text(encoding="utf-8")

        forbidden = [
            "DesktopWorldMap",
            "affordances_for_type",
            "check_reachability",
            "plan_route",
            "VERDICT_REACHABLE",
            "VERDICT_UNREACHABLE",
            "RoutePreconditionError",
        ]
        for sym in forbidden:
            self.assertNotIn(sym, source,
                             f"world/live_world_state.py contains spatial planning symbol '{sym}' "
                             f"— spatial reasoning belongs in faculties/spatial/ only.")


if __name__ == "__main__":
    unittest.main()
