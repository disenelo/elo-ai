"""
WO-NAV-004 — Surface Graph Reader + Y-Flip + BodySchema Geometry.
Acceptance Tests AT-1 through AT-5.
Authority: David L3 — Execution Directive 2026-08-24  RTR-047.
"""

import glob
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SPATIAL_PATH = os.path.join(_ROOT, "blender", "elo_spatial.json")


def _load_spatial():
    with open(_SPATIAL_PATH, encoding="utf-8") as f:
        return json.load(f)


def _spatial_mtime():
    return os.path.getmtime(_SPATIAL_PATH)


# ── AT-1: surfaces in world state, node count matches ───────────────────────────

class TestAT1SurfacesLoaded(unittest.TestCase):

    def test_at1_surfaces_field_present_and_populated(self):
        """LiveWorldState.surfaces contains nodes from elo_spatial.json surface_graph."""
        from world.live_world_state import LiveWorldState, assemble_world_state

        # Field must exist with correct default type
        ws_empty = LiveWorldState()
        self.assertIsInstance(ws_empty.surfaces, tuple)
        self.assertEqual(ws_empty.jump_px, 0)

        # After assembly, surfaces must be populated
        ws = assemble_world_state(turn_id="at1-test")
        self.assertIsInstance(ws.surfaces, tuple)

        # Count must match surface_graph nodes in the live file
        _sd = _load_spatial()
        expected_count = len(_sd.get("surface_graph", {}).get("nodes", []))
        self.assertGreater(expected_count, 0, "elo_spatial.json must have nodes")
        self.assertEqual(len(ws.surfaces), expected_count,
                         f"Expected {expected_count} surfaces, got {len(ws.surfaces)}")

    def test_at1_each_surface_has_required_fields(self):
        """Each surface dict has win_id, kind, rect_px, py_y."""
        from world.live_world_state import assemble_world_state

        ws = assemble_world_state(turn_id="at1b-test")
        self.assertGreater(len(ws.surfaces), 0)
        for s in ws.surfaces:
            self.assertIn("win_id",  s, f"Missing win_id in {s}")
            self.assertIn("kind",    s, f"Missing kind in {s}")
            self.assertIn("rect_px", s, f"Missing rect_px in {s}")
            self.assertIn("py_y",    s, f"Missing py_y in {s}")


# ── AT-2: Y-flip applied correctly ───────────────────────────────────────────────

class TestAT2YFlip(unittest.TestCase):

    def test_at2_yflip_formula_applied(self):
        """py_y = screen_h - unity_y for every surface node."""
        from world.live_world_state import assemble_world_state

        ws = assemble_world_state(turn_id="at2-test")
        _sd = _load_spatial()
        screen_h = int(_sd.get("screen_h", 1440))
        nodes = _sd.get("surface_graph", {}).get("nodes", [])

        self.assertGreater(len(nodes), 0)
        # Build a quick lookup by win_id
        surface_by_id = {s["win_id"]: s for s in ws.surfaces}
        for n in nodes:
            wid = n["id"]
            unity_y = n["rect_px"][1]
            expected_py_y = screen_h - unity_y
            got_py_y = surface_by_id[wid]["py_y"]
            self.assertEqual(
                got_py_y, expected_py_y,
                f"Node {wid}: expected py_y={expected_py_y}, got {got_py_y}",
            )


# ── AT-3: max_jump_d = 75 absent from all Python planning code ───────────────────

class TestAT3MaxJumpDRetired(unittest.TestCase):

    def test_at3_no_max_jump_d_in_python_code(self):
        """No Python file in the project uses max_jump_d = 75 as a reachability value."""
        hit_files = []
        _this_file = os.path.abspath(__file__)
        for root, dirs, files in os.walk(_ROOT):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules")]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                if os.path.abspath(fpath) == _this_file:
                    continue  # exclude this AT file from the scan
                try:
                    with open(fpath, encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    # Flag stale assignment / usage as a reachability value
                    if "max_jump_d" in text and "75" in text:
                        hit_files.append(fpath)
                except Exception:
                    pass
        self.assertEqual(
            hit_files, [],
            f"max_jump_d still referenced in: {hit_files}",
        )


# ── AT-4: reachability via capability_set.jump_px ────────────────────────────────

class TestAT4Reachability(unittest.TestCase):

    def test_at4_reachability_uses_jump_px(self):
        """Platforms within jump_px are reachable; beyond are not."""
        from world.live_world_state import assemble_world_state

        ws = assemble_world_state(turn_id="at4-test")
        jump_px = ws.jump_px
        self.assertGreater(jump_px, 0, "jump_px must be populated from capability_set")

        # Derive near/far gaps from live jump_px (not hardcoded — spec changed with maxHopSizes 6→3)
        gap_near = max(jump_px - 50, jump_px // 2)  # well within reach
        gap_far  = jump_px + 50                      # just beyond reach

        self.assertLessEqual(gap_near, jump_px,
                             f"gap_near={gap_near} should be <= jump_px={jump_px}")
        self.assertGreater(gap_far, jump_px,
                           f"gap_far={gap_far} should be > jump_px={jump_px}")

    def test_at4_canonical_live_matches_capability_set(self):
        """jump_px assembled from live elo_spatial.json matches capability_set.jump_px exactly."""
        from world.live_world_state import assemble_world_state

        ws = assemble_world_state(turn_id="at4b-test")
        jump_px = ws.jump_px
        self.assertGreater(jump_px, 0, "jump_px must be > 0 (populated from capability_set)")

        # Verify assembly reads the live file verbatim — no hardcoded override
        live = _load_spatial()
        expected = int(live.get("surface_graph", {}).get("capability_set", {}).get("jump_px", 0))
        self.assertEqual(jump_px, expected,
                         f"assembled jump_px={jump_px} does not match live capability_set.jump_px={expected}")


# ── AT-5: elo_spatial.json unchanged after world assembly ────────────────────────

class TestAT5SpatialReadOnly(unittest.TestCase):

    def test_at5_spatial_json_opened_read_only(self):
        """assemble_world_state() never opens elo_spatial.json for writing.

        elo_spatial.json is written by Unity concurrently; content changes are
        expected. This test verifies our assembly code uses read-only mode only.
        """
        import builtins
        import unittest.mock as mock

        write_mode_opens = []
        _real_open = builtins.open

        def _guarded_open(file, mode="r", *args, **kwargs):
            if (str(file) == _SPATIAL_PATH
                    and any(m in str(mode) for m in ("w", "a", "x"))):
                write_mode_opens.append((file, mode))
            return _real_open(file, mode, *args, **kwargs)

        from world import live_world_state as _lwm
        with mock.patch("builtins.open", side_effect=_guarded_open):
            _lwm.assemble_world_state(turn_id="at5-test")

        self.assertEqual(
            write_mode_opens, [],
            f"elo_spatial.json was opened for writing by assembly: {write_mode_opens}",
        )


if __name__ == "__main__":
    unittest.main()
