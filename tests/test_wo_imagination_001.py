"""
tests/test_wo_imagination_001.py — Acceptance tests for WO-IMAGINATION-001

WO: Deliberate simulation (Imagination) faculty.
    5 simulation types callable by Executive.
    SimulationResult schema with confidence and expiry.
    Epistemic gate: SIMULATED → CANDIDATE → VERIFY → KNOWLEDGE | REMAINS_HYPOTHESIS.
    Results are NEVER written to WKG as fact.

Acceptance criteria:
  1. Five simulation types callable by Executive
  2. SimulationResult schema implemented with confidence and expiry
  3. Simulation outputs clearly marked SIMULATED — never promoted automatically
  4. Epistemic gate exists between SimulationResult and knowledge promotion
  5. Perspective simulation feeds CCM (structure correct for CCM consumption)
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from faculties.imagination.imagination_faculty import (
    SimulationResult,
    VALID_SIMULATION_TYPES,
    simulate,
    simulate_outcome,
    simulate_counterfactual,
    simulate_perspective,
    simulate_design,
    simulate_self,
    context_block,
)


class TestSimulationResultSchema(unittest.TestCase):
    """AC-2: SimulationResult schema with confidence and expiry."""

    def test_schema_has_required_fields(self):
        r = simulate_outcome("test action", confidence=0.6)
        self.assertIsInstance(r.simulation_type, str)
        self.assertIsInstance(r.hypothesis, str)
        self.assertIsInstance(r.confidence, float)
        self.assertIsInstance(r.evidence, list)
        self.assertIsInstance(r.expiry, float)
        self.assertIsInstance(r.epistemic_status, str)
        self.assertIsInstance(r.timestamp, float)

    def test_confidence_clamping_raises_on_out_of_range(self):
        with self.assertRaises(ValueError):
            SimulationResult(
                simulation_type="outcome",
                hypothesis="test",
                confidence=1.5,
            )

    def test_confidence_zero_valid(self):
        r = SimulationResult(
            simulation_type="outcome",
            hypothesis="test",
            confidence=0.0,
        )
        self.assertEqual(r.confidence, 0.0)

    def test_expiry_defaults_to_one_hour_from_now(self):
        before = time.time()
        r = simulate_outcome("test")
        after = time.time()
        self.assertGreater(r.expiry, before + 3500)
        self.assertLess(r.expiry, after + 3700)

    def test_is_not_expired_immediately(self):
        r = simulate_outcome("test")
        self.assertFalse(r.is_expired)

    def test_is_expired_with_past_expiry(self):
        r = SimulationResult(
            simulation_type="outcome",
            hypothesis="test",
            confidence=0.5,
            expiry=time.time() - 1.0,
        )
        self.assertTrue(r.is_expired)

    def test_empty_hypothesis_raises(self):
        with self.assertRaises(ValueError):
            SimulationResult(
                simulation_type="outcome",
                hypothesis="   ",
                confidence=0.5,
            )

    def test_unknown_simulation_type_raises(self):
        with self.assertRaises(ValueError):
            SimulationResult(
                simulation_type="unknown_xyz",  # type: ignore[arg-type]
                hypothesis="test",
                confidence=0.5,
            )


class TestFiveSimulationTypes(unittest.TestCase):
    """AC-1: All five simulation types callable by Executive."""

    def test_valid_simulation_types_are_five(self):
        self.assertEqual(len(VALID_SIMULATION_TYPES), 5)
        expected = {"outcome", "counterfactual", "perspective", "design", "self"}
        self.assertEqual(VALID_SIMULATION_TYPES, expected)

    def test_simulate_outcome(self):
        r = simulate_outcome("send a message", confidence=0.7)
        self.assertEqual(r.simulation_type, "outcome")
        self.assertIn("send a message", r.hypothesis)
        self.assertEqual(r.confidence, 0.7)

    def test_simulate_counterfactual(self):
        r = simulate_counterfactual(
            past_event="the decision to skip the call",
            alternative="attended the call",
            confidence=0.4,
        )
        self.assertEqual(r.simulation_type, "counterfactual")
        self.assertIn("the decision to skip the call", r.hypothesis)

    def test_simulate_perspective(self):
        r = simulate_perspective(
            subject="David",
            situation="eLo goes quiet mid-session",
            confidence=0.45,
        )
        self.assertEqual(r.simulation_type, "perspective")
        self.assertIn("David", r.hypothesis)

    def test_simulate_design(self):
        r = simulate_design(
            mechanism="servo + cable tension",
            capability_query="arm raise and hold position",
            confidence=0.6,
        )
        self.assertEqual(r.simulation_type, "design")
        self.assertIn("servo + cable tension", r.hypothesis)

    def test_simulate_self(self):
        r = simulate_self(
            embodiment="desktop voice + avatar",
            capability_query="ambient emotion detection",
            confidence=0.5,
        )
        self.assertEqual(r.simulation_type, "self")
        self.assertIn("desktop voice", r.hypothesis)

    def test_dispatcher_routes_all_types(self):
        r1 = simulate("outcome", action="test action")
        r2 = simulate("counterfactual", past_event="event", alternative="alt")
        r3 = simulate("perspective", subject="David", situation="quiet")
        r4 = simulate("design", mechanism="mech", capability_query="what can")
        r5 = simulate("self", embodiment="voice", capability_query="detect")
        for r, t in zip([r1, r2, r3, r4, r5],
                        ["outcome", "counterfactual", "perspective", "design", "self"]):
            self.assertEqual(r.simulation_type, t)

    def test_dispatcher_raises_on_unknown_type(self):
        with self.assertRaises(ValueError):
            simulate("magic_type", action="test")  # type: ignore[arg-type]


class TestEpistemicGate(unittest.TestCase):
    """AC-3 & AC-4: Epistemic gate; results start SIMULATED, never auto-promoted."""

    def test_initial_status_is_simulated(self):
        r = simulate_outcome("test")
        self.assertEqual(r.epistemic_status, "SIMULATED")

    def test_promote_simulated_to_candidate(self):
        r = simulate_outcome("test")
        r2 = r.promote()
        self.assertEqual(r2.epistemic_status, "CANDIDATE")

    def test_promote_candidate_to_verify(self):
        r = simulate_outcome("test").promote()
        r2 = r.promote()
        self.assertEqual(r2.epistemic_status, "VERIFY")

    def test_promote_verify_to_knowledge(self):
        r = simulate_outcome("test").promote().promote()
        r2 = r.promote()
        self.assertEqual(r2.epistemic_status, "KNOWLEDGE")

    def test_promote_knowledge_is_noop(self):
        r = simulate_outcome("test").promote().promote().promote()
        self.assertEqual(r.epistemic_status, "KNOWLEDGE")
        r2 = r.promote()
        self.assertEqual(r2.epistemic_status, "KNOWLEDGE")

    def test_invalidate_sets_remains_hypothesis(self):
        r = simulate_outcome("test")
        r2 = r.invalidate()
        self.assertEqual(r2.epistemic_status, "REMAINS_HYPOTHESIS")

    def test_promote_does_not_mutate_original(self):
        r = simulate_outcome("test")
        r.promote()  # should not modify r
        self.assertEqual(r.epistemic_status, "SIMULATED")

    def test_invalidate_does_not_mutate_original(self):
        r = simulate_outcome("test")
        r.invalidate()
        self.assertEqual(r.epistemic_status, "SIMULATED")


class TestContextBlock(unittest.TestCase):
    """context_block() produces marked hypothesis injection string."""

    def test_empty_results_returns_empty_string(self):
        self.assertEqual(context_block([]), "")

    def test_expired_results_excluded(self):
        r = SimulationResult(
            simulation_type="outcome",
            hypothesis="expired sim",
            confidence=0.5,
            expiry=time.time() - 1.0,
        )
        self.assertEqual(context_block([r]), "")

    def test_non_simulated_status_excluded(self):
        r = simulate_outcome("test").promote()  # CANDIDATE
        self.assertEqual(context_block([r]), "")

    def test_active_simulated_result_in_block(self):
        r = simulate_outcome("build the robot arm", confidence=0.7)
        block = context_block([r])
        self.assertIn("IMAGINATION", block)
        self.assertIn("hypothes", block.lower())  # matches "hypothesis" or "hypotheses"
        self.assertIn("OUTCOME", block)
        self.assertIn("70%", block)

    def test_multiple_results_in_block(self):
        r1 = simulate_outcome("action A", confidence=0.6)
        r2 = simulate_perspective("David", "quiet moment", confidence=0.4)
        block = context_block([r1, r2])
        self.assertIn("OUTCOME", block)
        self.assertIn("PERSPECTIVE", block)


class TestPerspectiveFeedsCCM(unittest.TestCase):
    """AC-5: Perspective simulation is structurally correct for CCM consumption."""

    def test_perspective_result_has_subject_in_hypothesis(self):
        r = simulate_perspective("David", "eLo goes quiet", confidence=0.45)
        self.assertIn("David", r.hypothesis)
        self.assertIn("perspective", r.simulation_type)

    def test_perspective_evidence_identifies_subject(self):
        r = simulate_perspective("K-7", "eLo retreats", confidence=0.5)
        self.assertTrue(any("K-7" in e for e in r.evidence))


if __name__ == "__main__":
    unittest.main(verbosity=2)
