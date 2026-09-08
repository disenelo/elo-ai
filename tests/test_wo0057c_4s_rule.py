"""
WO-0057-PART-C ATs — 4-second rule detection + reroute flag.

AT1: ELO_4S_RULE=0 → no reroute regardless of latency
AT2: ELO_4S_RULE=1, prompt_eval < 4000ms → no reroute
AT3: ELO_4S_RULE=1, prompt_eval > 4000ms → REASONING tier backends tried
AT4: Reroute attempt logged to backend_health_history.jsonl with trigger: "4s_rule"
AT5: No new routing system — existing _TIER_PROVIDER_CANDIDATES used
AT6: ELO_4S_RULE=1 present in .env
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _reload_router():
    if "runtime.backend_router" in sys.modules:
        del sys.modules["runtime.backend_router"]
    import runtime.backend_router as br
    return br


class AT1_NoRerouteWhenRuleOff(unittest.TestCase):
    def test_rule_off_no_reroute(self):
        br = _reload_router()
        calls = []

        def fake_ollama(sp, ui):
            br._last_ollama_metrics.clear()
            br._last_ollama_metrics["prompt_eval_ms"] = 8000  # would trigger
            return "elo response"

        def fake_groq(sp, ui, max_tokens=None):
            calls.append("groq")
            return "groq response"

        with patch.object(br, "_ollama_call", fake_ollama), \
             patch.object(br, "_groq_call", fake_groq), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_provider_available", side_effect=lambda p: p == "ollama"), \
             patch.dict(os.environ, {"ELO_4S_RULE": "0"}, clear=False):
            result = br._route_by_tier("sys", "hi", br._TIER_CONVERSATIONAL, "answer", 4)

        self.assertNotIn("groq", calls, "Groq should not be called when ELO_4S_RULE=0")
        self.assertIsNotNone(result)


class AT2_NoRerouteWhenFastEnough(unittest.TestCase):
    def test_fast_turn_no_reroute(self):
        br = _reload_router()
        calls = []

        def fake_ollama(sp, ui):
            br._last_ollama_metrics.clear()
            br._last_ollama_metrics["prompt_eval_ms"] = 2000  # below threshold
            return "elo response"

        def fake_groq(sp, ui, max_tokens=None):
            calls.append("groq")
            return "groq response"

        with patch.object(br, "_ollama_call", fake_ollama), \
             patch.object(br, "_groq_call", fake_groq), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_provider_available", side_effect=lambda p: p == "ollama"), \
             patch.dict(os.environ, {"ELO_4S_RULE": "1"}, clear=False):
            result = br._route_by_tier("sys", "hi", br._TIER_CONVERSATIONAL, "answer", 4)

        self.assertNotIn("groq", calls, "Groq should not be called when prompt_eval < 4000ms")


class AT3_RerouteWhenSlow(unittest.TestCase):
    def test_slow_turn_tries_reasoning_tier(self):
        br = _reload_router()
        reasoning_tried = []

        def fake_ollama(sp, ui):
            br._last_ollama_metrics.clear()
            br._last_ollama_metrics["prompt_eval_ms"] = 9000  # above threshold
            return "ollama response"

        def fake_groq(sp, ui, max_tokens=None):
            reasoning_tried.append("groq")
            return "groq fast response"

        def fake_provider_available(p):
            return p in ("ollama", "groq")

        with patch.object(br, "_ollama_call", fake_ollama), \
             patch.object(br, "_groq_call", fake_groq), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_provider_available", fake_provider_available), \
             patch.object(br, "_log_4s_event", MagicMock()), \
             patch.dict(os.environ, {"ELO_4S_RULE": "1"}, clear=False):
            result = br._route_by_tier("sys", "hi", br._TIER_CONVERSATIONAL, "answer", 4)

        self.assertIn("groq", reasoning_tried, "REASONING tier should be tried when slow")
        self.assertIsNotNone(result)
        text, backend = result
        self.assertIn("4s_rule", backend, "Backend label should mark 4s_rule reroute")


class AT4_LoggingOnTrigger(unittest.TestCase):
    def test_4s_event_logged_to_file(self):
        br = _reload_router()
        log_path = os.path.join(ROOT, "data", "backend_health_history.jsonl")
        before_size = os.path.getsize(log_path) if os.path.exists(log_path) else 0

        def fake_ollama(sp, ui):
            br._last_ollama_metrics.clear()
            br._last_ollama_metrics["prompt_eval_ms"] = 9000
            return "slow"

        def fake_groq(sp, ui, max_tokens=None):
            return "fast"

        def fake_provider_available(p):
            return p in ("ollama", "groq")

        with patch.object(br, "_ollama_call", fake_ollama), \
             patch.object(br, "_groq_call", fake_groq), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_provider_available", fake_provider_available), \
             patch.dict(os.environ, {"ELO_4S_RULE": "1"}, clear=False):
            br._route_by_tier("sys", "hi", br._TIER_CONVERSATIONAL, "answer", 4)

        self.assertTrue(os.path.exists(log_path), "backend_health_history.jsonl must exist")
        with open(log_path, encoding="utf-8") as f:
            lines = f.readlines()
        last_entry = json.loads(lines[-1])
        self.assertEqual(last_entry["trigger"], "4s_rule")
        self.assertIn("prompt_eval_ms", last_entry)


class AT5_UsesExistingCandidateStructure(unittest.TestCase):
    def test_tier_provider_candidates_used(self):
        br = _reload_router()
        # Verify _TIER_REASONING candidates exist in existing structure (no new routing system)
        self.assertIn(br._TIER_REASONING, br._TIER_PROVIDER_CANDIDATES)
        reasoning_providers = br._TIER_PROVIDER_CANDIDATES[br._TIER_REASONING]
        # WO-LOCAL-LLM-001 (2026-09-08): ollama is now first in REASONING tier — local-first policy
        self.assertIn("ollama", reasoning_providers)
        self.assertIn("groq", reasoning_providers)


class AT6_EnvFileHasFlag(unittest.TestCase):
    def test_elo_4s_rule_in_env_file(self):
        env_path = os.path.join(ROOT, ".env")
        self.assertTrue(os.path.exists(env_path))
        with open(env_path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ELO_4S_RULE=1", content, ".env must contain ELO_4S_RULE=1")


if __name__ == "__main__":
    unittest.main()
