"""
tests/test_wo_knowledge_psychology_social.py — Acceptance tests for
WO-KNOWLEDGE-PSYCHOLOGY-001 and WO-SOCIAL-DYNAMICS-001.

Psychology AC:
  1. eLo can discuss psychological concepts with domain competence
  2. eLo understands the difference between a model and a diagnosis of an individual
  3. Psychology knowledge feeds CCM without causing over-interpretation
  4. eLo does not pathologise — observes patterns, not disorders

Social Dynamics AC:
  1. eLo can reason about social context
  2. eLo understands that social norms vary by context, culture, and relationship
  3. Social knowledge feeds CCM without overriding eLo's own values
  4. eLo recognises power dynamics without exploiting or being unconsciously shaped by them
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os

_GRAPH_PATH = os.path.join(
    Path(__file__).resolve().parent.parent,
    "relationships", "world_graph.json"
)


def _load_graph() -> dict:
    with open(_GRAPH_PATH, encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────────────────
# WKG data presence tests
# ──────────────────────────────────────────────────────────────────────────────

class TestPsychologyWKGData(unittest.TestCase):
    """WKG claims for all 16 psychology domains exist."""

    def setUp(self):
        self.g = _load_graph()
        self.claims = self.g.get("wkg_claims", [])
        self.sources = self.g.get("wkg_sources", [])
        self.psych_claims = [
            c for c in self.claims
            if "domain: psychology" in (c.get("notes") or "")
        ]

    def test_psychology_source_exists(self):
        ids = {s["id"] for s in self.sources}
        self.assertIn("wkg:source:psychology_consensus", ids)

    def test_at_least_16_psychology_claims(self):
        self.assertGreaterEqual(len(self.psych_claims), 16)

    def _has_claim_about(self, keyword: str) -> bool:
        kw = keyword.lower()
        return any(
            kw in (c.get("notes") or "").lower() or
            kw in (c.get("interpretation") or "").lower()
            for c in self.psych_claims
        )

    def test_domain_emotion(self):
        self.assertTrue(self._has_claim_about("emotion"))

    def test_domain_motivation(self):
        self.assertTrue(self._has_claim_about("motivation"))

    def test_domain_habit(self):
        self.assertTrue(self._has_claim_about("habit"))

    def test_domain_attention(self):
        self.assertTrue(self._has_claim_about("attention"))

    def test_domain_perception(self):
        self.assertTrue(self._has_claim_about("perception"))

    def test_domain_learning(self):
        self.assertTrue(self._has_claim_about("learning"))

    def test_domain_memory(self):
        self.assertTrue(self._has_claim_about("memory"))

    def test_domain_social_behaviour(self):
        self.assertTrue(self._has_claim_about("social_behaviour") or self._has_claim_about("social behaviour"))

    def test_domain_communication(self):
        self.assertTrue(self._has_claim_about("communication"))

    def test_domain_attachment(self):
        self.assertTrue(self._has_claim_about("attachment"))

    def test_domain_group_dynamics(self):
        self.assertTrue(self._has_claim_about("group_dynamics") or self._has_claim_about("group dynamics"))

    def test_domain_cognitive_biases(self):
        self.assertTrue(self._has_claim_about("cognitive_biases") or self._has_claim_about("cognitive biases"))

    def test_domain_decision_making(self):
        self.assertTrue(self._has_claim_about("decision_making") or self._has_claim_about("decision making"))

    def test_domain_creativity(self):
        self.assertTrue(self._has_claim_about("creativity"))

    def test_domain_stress_responses(self):
        self.assertTrue(self._has_claim_about("stress"))

    def test_domain_behavioural_patterns(self):
        self.assertTrue(self._has_claim_about("behavioural_patterns") or self._has_claim_about("behavioural patterns"))

    def test_model_vs_diagnosis_claim_exists(self):
        self.assertTrue(self._has_claim_about("model_vs_diagnosis") or self._has_claim_about("model") or self._has_claim_about("diagnosis"))

    def test_hard_lane_notes_present_on_all_psych_claims(self):
        for c in self.psych_claims:
            self.assertIn("hard_lane", (c.get("notes") or ""), msg=f"Missing hard_lane in {c['id']}")


class TestSocialDynamicsWKGData(unittest.TestCase):
    """WKG claims for all 16 social dynamics domains exist."""

    def setUp(self):
        self.g = _load_graph()
        self.claims = self.g.get("wkg_claims", [])
        self.sources = self.g.get("wkg_sources", [])
        self.social_claims = [
            c for c in self.claims
            if "domain: social_dynamics" in (c.get("notes") or "")
        ]

    def test_social_dynamics_source_exists(self):
        ids = {s["id"] for s in self.sources}
        self.assertIn("wkg:source:social_dynamics_consensus", ids)

    def test_at_least_16_social_claims(self):
        self.assertGreaterEqual(len(self.social_claims), 16)

    def _has_claim_about(self, keyword: str) -> bool:
        kw = keyword.lower()
        return any(
            kw in (c.get("notes") or "").lower() or
            kw in (c.get("interpretation") or "").lower()
            for c in self.social_claims
        )

    def test_domain_conversation_etiquette(self):
        self.assertTrue(self._has_claim_about("conversation_etiquette") or self._has_claim_about("conversation etiquette"))

    def test_domain_turn_taking(self):
        self.assertTrue(self._has_claim_about("turn_taking") or self._has_claim_about("turn taking"))

    def test_domain_politeness(self):
        self.assertTrue(self._has_claim_about("politeness"))

    def test_domain_humour(self):
        self.assertTrue(self._has_claim_about("humour"))

    def test_domain_boundaries(self):
        self.assertTrue(self._has_claim_about("boundaries"))

    def test_domain_social_context(self):
        self.assertTrue(self._has_claim_about("social_context") or self._has_claim_about("social context"))

    def test_domain_relationship_context(self):
        self.assertTrue(self._has_claim_about("relationship_context") or self._has_claim_about("relationship context"))

    def test_domain_intimacy_levels(self):
        self.assertTrue(self._has_claim_about("intimacy_levels") or self._has_claim_about("intimacy levels"))

    def test_domain_professional_casual(self):
        self.assertTrue(self._has_claim_about("professional_casual") or self._has_claim_about("professional"))

    def test_domain_when_to_speak(self):
        self.assertTrue(self._has_claim_about("when_to_speak") or self._has_claim_about("when to speak"))

    def test_domain_when_to_challenge(self):
        self.assertTrue(self._has_claim_about("when_to_challenge") or self._has_claim_about("challenge"))

    def test_domain_when_to_celebrate(self):
        self.assertTrue(self._has_claim_about("when_to_celebrate") or self._has_claim_about("celebrate"))

    def test_domain_when_to_ask(self):
        self.assertTrue(self._has_claim_about("when_to_ask") or self._has_claim_about("when to ask"))

    def test_domain_when_to_listen(self):
        self.assertTrue(self._has_claim_about("when_to_listen") or self._has_claim_about("listening"))

    def test_domain_power_dynamics(self):
        self.assertTrue(self._has_claim_about("power_dynamics") or self._has_claim_about("power dynamics"))

    def test_domain_norms_vary(self):
        self.assertTrue(self._has_claim_about("norms_vary") or self._has_claim_about("norms vary"))

    def test_feeds_ccm_tag_on_social_claims(self):
        for c in self.social_claims:
            self.assertIn("feeds: CCM", (c.get("notes") or ""), msg=f"Missing 'feeds: CCM' in {c['id']}")


# ──────────────────────────────────────────────────────────────────────────────
# Faculty tests — psychology
# ──────────────────────────────────────────────────────────────────────────────

class TestPsychologyFaculty(unittest.TestCase):
    """AC-1..4 via the psychology_faculty module."""

    def setUp(self):
        from faculties.knowledge.psychology_faculty import (
            query, context_block, is_domain_trigger, HARD_LANE_NOTE,
        )
        self.query = query
        self.context_block = context_block
        self.is_trigger = is_domain_trigger
        self.hard_lane = HARD_LANE_NOTE

    def test_importable(self):
        self.assertIsNotNone(self.query)

    def test_hard_lane_note_prohibits_diagnosis(self):
        self.assertIn("NOT diagnose", self.hard_lane)
        self.assertIn("NOT", self.hard_lane)

    def test_hard_lane_note_prohibits_labelling(self):
        self.assertIn("label", self.hard_lane.lower())

    def test_is_trigger_on_psychology_words(self):
        self.assertTrue(self.is_trigger("I'm struggling with my attention today"))
        self.assertTrue(self.is_trigger("I can't focus"))
        self.assertTrue(self.is_trigger("feeling stressed"))
        self.assertTrue(self.is_trigger("confirmation bias"))

    def test_is_trigger_false_on_unrelated(self):
        self.assertFalse(self.is_trigger("export the blender file"))
        self.assertFalse(self.is_trigger("compile the shader"))

    def test_query_returns_relevant_claims_for_stress(self):
        results = self.query("I'm really stressed and can't think straight", max_results=5)
        self.assertTrue(len(results) > 0)
        self.assertIn("_score", results[0])

    def test_query_returns_claims_for_creativity(self):
        results = self.query("I'm having a creative block", max_results=5)
        self.assertTrue(len(results) > 0)

    def test_query_returns_empty_for_unrelated(self):
        results = self.query("deploy the server binary", max_results=5)
        self.assertEqual(len(results), 0)

    def test_context_block_includes_hard_lane(self):
        block = self.context_block("I'm feeling overwhelmed")
        if block:  # only assert if we got a block
            self.assertIn("PSYCHOLOGY", block)
            self.assertIn("NOT", block)

    def test_context_block_empty_for_unrelated(self):
        block = self.context_block("run the unity tests")
        self.assertEqual(block, "")

    def test_query_respects_max_results(self):
        results = self.query("emotion memory attention stress creativity habit", max_results=2)
        self.assertLessEqual(len(results), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Faculty tests — social dynamics
# ──────────────────────────────────────────────────────────────────────────────

class TestSocialDynamicsFaculty(unittest.TestCase):
    """AC-1..4 via the social_dynamics_faculty module."""

    def setUp(self):
        from faculties.knowledge.social_dynamics_faculty import (
            query, context_block, is_domain_trigger, HARD_LANE_NOTE,
        )
        self.query = query
        self.context_block = context_block
        self.is_trigger = is_domain_trigger
        self.hard_lane = HARD_LANE_NOTE

    def test_importable(self):
        self.assertIsNotNone(self.query)

    def test_hard_lane_note_norms_vary(self):
        self.assertIn("vary", self.hard_lane.lower())

    def test_hard_lane_note_power_dynamics(self):
        self.assertIn("power", self.hard_lane.lower())
        self.assertIn("exploit", self.hard_lane.lower())

    def test_is_trigger_on_social_words(self):
        self.assertTrue(self.is_trigger("when should I speak up"))
        self.assertTrue(self.is_trigger("I'm thinking aloud here"))
        self.assertTrue(self.is_trigger("is it appropriate to challenge"))
        self.assertTrue(self.is_trigger("conversation etiquette"))

    def test_is_trigger_false_on_unrelated(self):
        self.assertFalse(self.is_trigger("parse the json file"))
        self.assertFalse(self.is_trigger("blender shader node"))

    def test_query_returns_results_for_when_to_challenge(self):
        results = self.query("when is it okay to challenge someone's idea", max_results=5)
        self.assertTrue(len(results) > 0)

    def test_query_returns_results_for_silence(self):
        results = self.query("should I stay silent when someone is thinking", max_results=5)
        self.assertTrue(len(results) > 0)

    def test_query_returns_results_for_celebrate(self):
        results = self.query("should I celebrate this achievement", max_results=5)
        self.assertTrue(len(results) > 0)

    def test_context_block_includes_social_tag(self):
        block = self.context_block("when should I speak and when should I listen")
        if block:
            self.assertIn("SOCIAL", block)

    def test_context_block_empty_for_unrelated(self):
        block = self.context_block("git push origin main")
        self.assertEqual(block, "")

    def test_query_respects_max_results(self):
        results = self.query("conversation humour boundaries silence listen challenge celebrate", max_results=2)
        self.assertLessEqual(len(results), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Cross-faculty __init__ import
# ──────────────────────────────────────────────────────────────────────────────

class TestKnowledgePackageImport(unittest.TestCase):
    def test_package_imports_both_faculties(self):
        from faculties.knowledge import (
            psychology_query, psychology_context_block, is_psychology_trigger,
            PSYCHOLOGY_HARD_LANE,
            social_dynamics_query, social_dynamics_context_block,
            is_social_dynamics_trigger, SOCIAL_DYNAMICS_HARD_LANE,
        )
        self.assertIsNotNone(psychology_query)
        self.assertIsNotNone(social_dynamics_query)
        self.assertIn("NOT", PSYCHOLOGY_HARD_LANE)
        self.assertIn("power", SOCIAL_DYNAMICS_HARD_LANE.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
