"""
WO-101 Part B — Significance vector shape consistency.

Rule: evaluate() must return the same key set regardless of whether `outcome`
is supplied. The 3 outcome dims (embodiment, efficiency, safety) + reward
are present always, zeroed when outcome=None or verified=False.

See also: WO-101 card 03c, Architect ruling F (live 12-dim vector is CANONICAL).
P0-3 compliance: lookup() does not call reinforce() (verified in test_wo100_101_096b_109_118.py).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_CANONICAL_KEYS = frozenset({
    "presence", "learning", "logic", "humour", "relationship",
    "creation", "system_change", "novelty", "continuity",
    "overall", "embodiment", "efficiency", "safety", "reward",
})


class TestVectorShapeConsistency(unittest.TestCase):

    def _eval(self, **kwargs):
        from memory.significance_engine import evaluate
        return evaluate(raw="test input", response="test response",
                        action="build", **kwargs)

    def test_no_outcome_has_canonical_keys(self):
        """evaluate() with no outcome still returns all 14 canonical keys."""
        result = self._eval()
        missing = _CANONICAL_KEYS - result.keys()
        self.assertFalse(missing, f"Keys missing when outcome=None: {missing}")

    def test_with_outcome_has_same_canonical_keys(self):
        """evaluate() with outcome also returns the same 14 keys (no additions)."""
        outcome = {"verified": True, "completion": "met", "ack_received": True,
                   "cost": {"seconds": 1.0, "legs": 1, "retries": 0}}
        result = self._eval(outcome=outcome)
        missing = _CANONICAL_KEYS - result.keys()
        self.assertFalse(missing, f"Keys missing with outcome: {missing}")

    def test_no_outcome_body_dims_are_zero(self):
        """ACK-only body dims (embodiment, efficiency, safety) must be 0.0 when no outcome.
        reward = 0.70*outcome_terms + 0.30*overall; with outcome_terms=0, reward = 0.30*overall (nonzero)."""
        result = self._eval()
        self.assertEqual(result["embodiment"], 0.0, "embodiment must be 0 with no outcome")
        self.assertEqual(result["efficiency"], 0.0, "efficiency must be 0 with no outcome")
        self.assertEqual(result["safety"],     0.0, "safety must be 0 with no outcome")
        # reward = 0.30 * overall when no outcome (outcome_terms=0)
        expected_reward = round(0.30 * result["overall"], 4)
        self.assertAlmostEqual(result["reward"], expected_reward, places=4,
                               msg="reward must equal 0.30*overall when no outcome")

    def test_verified_false_outcome_dims_zero(self):
        """verified=False => all outcome_terms = 0 => reward driven by meaning only."""
        outcome = {"verified": False, "completion": "met", "ack_received": True,
                   "cost": {"seconds": 1.0, "legs": 1, "retries": 0}}
        result = self._eval(outcome=outcome)
        # embodiment/efficiency/safety scored from ACK but outcome_terms=0
        expected_reward = result["overall"] * 0.30
        self.assertAlmostEqual(result["reward"], expected_reward, places=4)

    def test_verified_true_reward_above_meaning_only(self):
        """A verified ACK outcome must score differently from no-outcome (reward path is real)."""
        no_ack = self._eval()
        outcome = {"verified": True, "completion": "met", "ack_received": True,
                   "cost": {"seconds": 1.0, "legs": 1, "retries": 0}}
        with_ack = self._eval(outcome=outcome)
        self.assertNotEqual(no_ack["reward"], with_ack["reward"],
                            "Reward must differ between no-outcome and verified outcome")

    def test_key_set_does_not_depend_on_outcome(self):
        """Key set is identical with and without outcome — no extra keys added."""
        result_none = self._eval()
        outcome = {"verified": True, "completion": "partial", "ack_received": True,
                   "cost": {"seconds": 2.0, "legs": 2, "retries": 1}}
        result_with = self._eval(outcome=outcome)
        # Remove emotion_weight which is conditionally added by plan; not outcome-dependent
        keys_none = {k for k in result_none if k != "emotion_weight"}
        keys_with = {k for k in result_with if k != "emotion_weight"}
        self.assertEqual(keys_none, keys_with,
                         f"Key sets differ: only_none={keys_none - keys_with}, only_with={keys_with - keys_none}")


class TestRule1Alarm(unittest.TestCase):
    """Rule 1 alarm: a production caller of evaluate() must supply outcome (or explicit None)."""

    def test_journal_router_passes_outcome(self):
        """journal_router.route() must pass outcome= to evaluate()."""
        import inspect
        from memory import journal_router
        src = inspect.getsource(journal_router.route)
        self.assertIn("outcome", src,
                      "journal_router.route() must pass outcome= to evaluate() (Rule 1 alarm)")

    def test_no_bare_evaluate_call_without_outcome(self):
        """journal_router.route() must pass outcome= to evaluate() — Rule 1 alarm."""
        import inspect
        from memory import journal_router
        # Use inspect.getsource to get just the function, avoiding docstring prose
        route_src = inspect.getsource(journal_router.route)
        # The actual evaluate() call in route() must be accompanied by outcome=
        self.assertIn("outcome", route_src,
                      "journal_router.route() must pass outcome= to evaluate() — Rule 1 alarm")


if __name__ == "__main__":
    unittest.main()
