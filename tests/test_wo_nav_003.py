"""
WO-NAV-003 — AT-1 through AT-5.
SP-6 (gaze_win_id in world_dict) · SP-16 (navigation intent) · SP-17 (referent resolver)
"""

import sys
import os
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.router import intent_engine
from runtime import referent_resolver


# ── AT-1: SP-6 — gaze_win_id appears in world_dict after gaze event ──────────

class TestSP6GazeWiring(unittest.TestCase):

    def _ctx(self, gaze):
        from runtime.executive_context import build_executive_context
        desktop = types.SimpleNamespace(platform="main", active_app="Chrome", available=True)
        world = types.SimpleNamespace(
            desktop=desktop, gaze=gaze, degraded=(), route_history=(),
        )
        return build_executive_context(
            intent="test",
            emotional_context={},
            world=world,
            working_memory=None,
            capabilities=[],
            cognitive_state=None,
            affordances=None,
            attention={},
        )

    def test_at1_gaze_win_id_in_world_dict(self):
        """gaze_win_id is populated from GazeState.win_id when world has a live gaze."""
        gaze = types.SimpleNamespace(win_id=10130, window="Chrome", on_window=True)
        ctx = self._ctx(gaze)
        self.assertIn("gaze_win_id", ctx.world)
        self.assertEqual(ctx.world["gaze_win_id"], 10130)

    def test_at1b_gaze_win_id_zero_when_no_gaze(self):
        """gaze_win_id defaults to 0 when world has no gaze."""
        ctx = self._ctx(None)
        self.assertEqual(ctx.world.get("gaze_win_id", 0), 0)


# ── AT-2/AT-3: SP-16 — navigation intent fires; catch-all still fires ────────

class TestSP16NavigationIntent(unittest.TestCase):

    def test_at2_navigation_intent_fires(self):
        """'go to that platform' classifies as navigation, not conversation."""
        result = intent_engine.detect("go to that platform")
        self.assertEqual(result["intent"], "navigation")
        self.assertNotEqual(result["intent"], "conversation")

    def test_at2b_jump_to(self):
        result = intent_engine.detect("jump to the ledge")
        self.assertEqual(result["intent"], "navigation")

    def test_at2c_navigate_to(self):
        result = intent_engine.detect("navigate to the other side")
        self.assertEqual(result["intent"], "navigation")

    def test_at3_catch_all_fires_for_non_nav(self):
        """'how are you doing' routes to non-navigation intent (conversation)."""
        result = intent_engine.detect("how are you doing")
        self.assertNotEqual(result["intent"], "navigation")

    def test_at3b_social_phrase_not_nav(self):
        result = intent_engine.detect("hey, what's good?")
        self.assertNotEqual(result["intent"], "navigation")


# ── AT-4/AT-5: SP-17 — referent resolver ─────────────────────────────────────

class TestSP17ReferentResolver(unittest.TestCase):

    def _world(self, gaze_win_id=99):
        return {"gaze_win_id": gaze_win_id}

    def test_at4_proximal_deixis_resolves(self):
        """'that platform' → returns current gaze_win_id."""
        result = referent_resolver.resolve("that platform", self._world(99))
        self.assertEqual(result, 99)

    def test_at4b_here_resolves(self):
        result = referent_resolver.resolve("here", self._world(42))
        self.assertEqual(result, 42)

    def test_at4c_over_there_resolves(self):
        result = referent_resolver.resolve("go over there", self._world(77))
        self.assertEqual(result, 77)

    def test_at5_unresolvable_returns_none(self):
        """'the invisible ledge' → None (does not raise)."""
        result = referent_resolver.resolve(
            "the invisible ledge", self._world(0), spatial=None
        )
        self.assertIsNone(result)

    def test_at5b_no_gaze_proximal_returns_none(self):
        """Proximal deixis with gaze_win_id=0 → None (no gaze lock)."""
        result = referent_resolver.resolve("that thing", {"gaze_win_id": 0})
        self.assertIsNone(result)

    def test_at5c_resolve_does_not_raise(self):
        """Resolver never raises regardless of input."""
        for phrase in ["", "xyzzy", "the abyss", None.__class__.__name__]:
            try:
                referent_resolver.resolve(phrase, {})
            except Exception as e:
                self.fail(f"resolve raised {e!r} on {phrase!r}")


if __name__ == "__main__":
    unittest.main()
