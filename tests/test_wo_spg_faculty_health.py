"""
tests/test_wo_spg_faculty_health.py — Acceptance tests for WO-FACULTY-HEALTH-SPG-SIGNAL-001

WO: SPG tap failures in spine.py surface as faculty degradation.
    - spg entry added to _FACULTIES
    - mark_degraded("spg") called on tap failure
    - mark_recovered("spg") called on success
    - [SPG STATUS: offline] injected to context after 3+ consecutive failures
    - /health endpoint reports spg: DEGRADED

Acceptance:
  - SPG tap forced to fail → get_status("spg") returns DEGRADED
  - /health reports spg: DEGRADED
  - Recovery: next successful tap → get_status("spg") returns CONNECTED
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestSPGInFaculties(unittest.TestCase):
    def test_spg_in_faculties_tuple(self):
        import importlib
        import runtime.faculty_health as fh
        importlib.reload(fh)
        self.assertIn("spg", fh._FACULTIES, "spg must be in _FACULTIES")

    def test_spg_in_registry(self):
        import importlib
        import runtime.faculty_health as fh
        importlib.reload(fh)
        self.assertIn("spg", fh._registry, "spg must appear in registry after reload")

    def test_spg_initial_status_connected(self):
        import importlib
        import runtime.faculty_health as fh
        importlib.reload(fh)
        self.assertEqual(fh.get_status("spg"), fh.CONNECTED)


class TestSPGMarkDegraded(unittest.TestCase):
    def setUp(self):
        import importlib
        import runtime.faculty_health as fh
        importlib.reload(fh)
        self.fh = fh

    def test_mark_degraded_sets_degraded_status(self):
        self.fh.mark_degraded("spg", "test tap failure")
        self.assertEqual(self.fh.get_status("spg"), self.fh.DEGRADED)

    def test_mark_degraded_increments_error_count(self):
        self.fh.mark_degraded("spg", "failure 1")
        count_after = self.fh._registry["spg"]["error_count"]
        self.assertGreaterEqual(count_after, 1)

    def test_mark_recovered_after_degraded(self):
        self.fh.mark_degraded("spg", "tap failure")
        self.fh.mark_recovered("spg")
        self.assertEqual(self.fh.get_status("spg"), self.fh.CONNECTED)

    def test_mark_recovered_resets_error_count(self):
        self.fh.mark_degraded("spg", "x")
        self.fh.mark_degraded("spg", "x")
        self.fh.mark_recovered("spg")
        self.assertEqual(self.fh._registry["spg"]["error_count"], 0)

    def test_unknown_faculty_mark_degraded_noop(self):
        self.fh.mark_degraded("nonexistent_faculty_xyz", "should not raise")
        # No exception = pass


class TestSPGHealthSummary(unittest.TestCase):
    def setUp(self):
        import importlib
        import runtime.faculty_health as fh
        importlib.reload(fh)
        self.fh = fh

    def test_health_summary_includes_spg_degraded(self):
        self.fh.mark_degraded("spg", "tap failed in test")
        summary = self.fh.health_summary()
        self.assertIn("spg", summary.lower())
        self.assertIn("DEGRADED", summary)

    def test_health_summary_spg_ok_when_connected(self):
        summary = self.fh.health_summary()
        # spg entry appears; status is OK
        self.assertIn("spg", summary.lower())

    def test_all_statuses_includes_spg(self):
        statuses = self.fh.all_statuses()
        self.assertIn("spg", statuses)


class TestSPGContextInjection(unittest.TestCase):
    """Verify the server.py SPG offline block logic is present."""

    def test_spg_offline_block_in_server(self):
        _server = Path("server.py").read_text(encoding="utf-8")
        self.assertIn("WO-FACULTY-HEALTH-SPG-SIGNAL-001", _server,
                      "server.py must contain WO-FACULTY-HEALTH-SPG-SIGNAL-001 block")
        self.assertIn("SPG STATUS: offline", _server,
                      "server.py must inject [SPG STATUS: offline] when degraded")
        self.assertIn('"spg"', _server,
                      "server.py must reference spg in the context injection block")

    def test_error_count_threshold_is_3(self):
        _server = Path("server.py").read_text(encoding="utf-8")
        self.assertIn(">= 3", _server,
                      "injection threshold must be >= 3 consecutive failures")


class TestSPGSpineWire(unittest.TestCase):
    """Verify spine.py has the mark_degraded/mark_recovered calls at both tap sites."""

    def test_spine_has_mark_degraded_for_spg(self):
        _spine = (Path("runtime") / "spine" / "spine.py").read_text(encoding="utf-8")
        self.assertIn('_spg_mark_deg("spg"', _spine,
                      "spine.py relationship tap must call mark_degraded(spg)")
        self.assertIn('_spg_er_deg("spg"', _spine,
                      "spine.py execution_report tap must call mark_degraded(spg)")

    def test_spine_has_mark_recovered_for_spg(self):
        _spine = (Path("runtime") / "spine" / "spine.py").read_text(encoding="utf-8")
        self.assertIn('_spg_recover("spg")', _spine,
                      "spine.py relationship tap must call mark_recovered(spg) on success")
        self.assertIn('_spg_er_recover("spg")', _spine,
                      "spine.py execution_report tap must call mark_recovered(spg) on success")


if __name__ == "__main__":
    unittest.main(verbosity=2)
