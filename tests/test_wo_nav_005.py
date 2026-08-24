"""
WO-NAV-005 — Embodiment Capability Safety.
Acceptance Tests AT-1 through AT-5.
Authority: David L3 — Execution Directive 2026-08-24  RTR-049.
"""

import dataclasses
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── AT-1: embodiment_scope field exists on all Capability objects ─────────────

class TestAT1EmbodimentScopeField(unittest.TestCase):

    def test_at1_field_present_on_dataclass(self):
        """Capability dataclass has embodiment_scope frozenset field."""
        from runtime.capabilities.capability import Capability
        field_names = {f.name for f in dataclasses.fields(Capability)}
        self.assertIn("embodiment_scope", field_names,
                      "Capability dataclass missing embodiment_scope — WO-NAV-005 not applied")

    def test_at1_default_is_frozenset_desktop(self):
        """Default embodiment_scope is frozenset({'desktop'})."""
        from runtime.capabilities.capability import Capability
        cap = Capability(
            id="test-cap", display_name="Test", category="utility",
            description="test", verbs=["test"],
            ack_source="sync_return",
        )
        self.assertIsInstance(cap.embodiment_scope, frozenset)
        self.assertIn("desktop", cap.embodiment_scope)

    def test_at1_all_registry_capabilities_have_field(self):
        """Every capability in ALL_CAPABILITIES has embodiment_scope as a frozenset."""
        from runtime.capabilities.registry import ALL_CAPABILITIES
        for cap in ALL_CAPABILITIES:
            self.assertIsInstance(
                cap.embodiment_scope, frozenset,
                f"Capability {cap.id} has non-frozenset embodiment_scope",
            )


# ── AT-2: desktop-only capability blocked in non-desktop embodiment ──────────

class TestAT2EmbodimentFilter(unittest.TestCase):

    def _run_faculty(self, meaning: str, embodiment: str) -> list:
        from runtime.spine.spine import _capability_faculty
        return _capability_faculty(meaning, "", current_embodiment=embodiment)

    def test_at2_robot_only_cap_blocked_on_desktop(self):
        """A capability scoped to {'robot'} does not appear when current_embodiment='desktop'."""
        from runtime.capabilities.capability import Capability
        from runtime.capabilities import registry as _reg

        # Inject a robot-only cap into ALL_CAPABILITIES temporarily
        robot_cap = Capability(
            id="test-robot-jump", display_name="Robot Jump", category="robot",
            description="jump for robot", verbs=["robot-jump-unique-test-verb"],
            ack_source="sync_return",
            embodiment_scope=frozenset({"robot"}),
        )
        _orig = list(_reg.ALL_CAPABILITIES)
        _reg.ALL_CAPABILITIES.append(robot_cap)
        try:
            results = self._run_faculty("robot-jump-unique-test-verb", "desktop")
            ids = [r["id"] for r in results]
            self.assertNotIn("test-robot-jump", ids,
                             "Robot-only capability must not appear when embodiment=desktop")
        finally:
            _reg.ALL_CAPABILITIES[:] = _orig

    def test_at2_desktop_cap_visible_on_desktop(self):
        """A capability scoped to {'desktop'} appears when current_embodiment='desktop'."""
        from runtime.capabilities.capability import Capability
        from runtime.capabilities import registry as _reg

        desk_cap = Capability(
            id="test-desk-cap", display_name="Desk Cap", category="utility",
            description="desktop only cap", verbs=["desk-unique-test-verb-42"],
            ack_source="sync_return",
            embodiment_scope=frozenset({"desktop"}),
        )
        _orig = list(_reg.ALL_CAPABILITIES)
        _reg.ALL_CAPABILITIES.append(desk_cap)
        try:
            results = self._run_faculty("desk-unique-test-verb-42", "desktop")
            ids = [r["id"] for r in results]
            self.assertIn("test-desk-cap", ids,
                          "Desktop capability must appear when embodiment=desktop")
        finally:
            _reg.ALL_CAPABILITIES[:] = _orig


# ── AT-3: universal ('any') capability passes all embodiments ────────────────

class TestAT3UniversalCapability(unittest.TestCase):

    def _run_faculty(self, meaning: str, embodiment: str) -> list:
        from runtime.spine.spine import _capability_faculty
        return _capability_faculty(meaning, "", current_embodiment=embodiment)

    def test_at3_any_cap_appears_in_desktop(self):
        """A capability scoped to {'any'} appears when embodiment='desktop'."""
        self._check_any_cap_visible("desktop")

    def test_at3_any_cap_appears_in_robot(self):
        """A capability scoped to {'any'} appears when embodiment='robot'."""
        self._check_any_cap_visible("robot")

    def test_at3_any_cap_appears_in_phone(self):
        """A capability scoped to {'any'} appears when embodiment='phone'."""
        self._check_any_cap_visible("phone")

    def _check_any_cap_visible(self, embodiment: str):
        from runtime.capabilities.capability import Capability
        from runtime.capabilities import registry as _reg

        any_cap = Capability(
            id="test-any-cap", display_name="Any Cap", category="utility",
            description="universal cap", verbs=["any-unique-test-verb-99"],
            ack_source="sync_return",
            embodiment_scope=frozenset({"any"}),
        )
        _orig = list(_reg.ALL_CAPABILITIES)
        _reg.ALL_CAPABILITIES.append(any_cap)
        try:
            results = self._run_faculty("any-unique-test-verb-99", embodiment)
            ids = [r["id"] for r in results]
            self.assertIn("test-any-cap", ids,
                          f"Universal cap must appear when embodiment='{embodiment}'")
        finally:
            _reg.ALL_CAPABILITIES[:] = _orig


# ── AT-4: current_embodiment in world_dict ───────────────────────────────────

class TestAT4CurrentEmbodimentInWorldDict(unittest.TestCase):

    def test_at4_current_embodiment_in_world_dict(self):
        """build_executive_context() includes current_embodiment in ctx.world."""
        from runtime.executive_context import build_executive_context

        stub_world = types.SimpleNamespace(
            desktop=types.SimpleNamespace(platform="mac", active_app="", available=True),
            degraded=(),
            route_history=(),
            gaze=None,
        )
        ctx = build_executive_context(
            intent="conversation",
            emotional_context={},
            world=stub_world,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=[],
            attention={},
            lessons=[],
        )
        self.assertIn("current_embodiment", ctx.world,
                      "current_embodiment must be in world_dict")
        val = ctx.world["current_embodiment"]
        self.assertIsInstance(val, str)
        self.assertTrue(val, "current_embodiment must be non-empty string")


# ── AT-5: existing desktop capabilities unaffected when embodiment='desktop' ──

class TestAT5ExistingCapabilitiesUnaffected(unittest.TestCase):

    def test_at5_desktop_registry_capabilities_pass_desktop_filter(self):
        """All non-future, enabled registry capabilities pass when embodiment='desktop'."""
        from runtime.capabilities.registry import ALL_CAPABILITIES

        for cap in ALL_CAPABILITIES:
            if cap.future or not cap.enabled:
                continue
            scope = getattr(cap, "embodiment_scope", frozenset({"desktop"}))
            passes = "any" in scope or "desktop" in scope
            self.assertTrue(
                passes,
                f"Existing desktop capability {cap.id!r} blocked by embodiment filter "
                f"(scope={scope!r}) — AT-5 requires all enabled caps remain visible on desktop",
            )


if __name__ == "__main__":
    unittest.main()
