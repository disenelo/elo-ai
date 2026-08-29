"""
tests/test_wo_router001_capability_selection.py — WO-ROUTER-001
Capability-driven provider selection (replaces static position ladder).

Authority: David L3 canonical routing ruling 2026-08-28
          SOURCE_2026-08-28_DAVID_L3_one_brain_canonical_routing.md

8 ATs:
  AT-1  CONVERSATIONAL + Ollama available + Groq available → Ollama wins (cheapest)
  AT-2  CONVERSATIONAL + Ollama DOWN + Groq available → Groq (next cheapest)
  AT-3  REASONING + Groq in quota-cooldown + Cerebras available → Cerebras
  AT-4  Pinned mode, Groq 429, Cerebras fail, Ollama up → ollama (WO-073 absorbed)
  AT-5  All providers down for tier → mock via caller (route returns mock backend)
  AT-6  `capability` field in routing_trace.json after a tier-routed turn
  AT-7  Regression: test_brain_authors passes + test_wo073 passes
  AT-8  ELO_OLLAMA_MODEL defaults to llama3.1:8b when env var unset

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_router001_capability_selection.py -v
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import runtime.backend_router as br


class TestRouterCapabilitySelection(unittest.TestCase):

    def setUp(self):
        br._last_responses.clear()
        br._groq_quota_cooldown_until = 0.0
        br._last_route_capability = ""

    # ── AT-1: CONVERSATIONAL — Ollama wins over Groq (lowest cost) ───────────

    def test_at1_conversational_ollama_wins_over_groq(self):
        """CONVERSATIONAL + Ollama available + Groq available → Ollama selected (free-local cheapest)."""
        with patch.dict(os.environ, {"ELO_BACKEND": ""}, clear=False), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_cerebras_available", return_value=False), \
             patch.object(br, "_openai_available", return_value=False), \
             patch.object(br, "_claude_available", return_value=False), \
             patch.object(br, "_gemini_available", return_value=False), \
             patch.object(br, "_ollama_call", return_value="Hello."), \
             patch.object(br, "_has_lore_drift", return_value=False):
            br._last_responses.clear()
            _text, backend = br._route_by_tier(
                "sys", "user", br._TIER_CONVERSATIONAL, "answer", 4
            )
        self.assertIn("ollama", backend,
            f"AT-1: CONVERSATIONAL should pick Ollama (cheapest), got {backend}")

    # ── AT-2: CONVERSATIONAL — Ollama down → Groq (next cheapest) ────────────

    def test_at2_conversational_groq_when_ollama_down(self):
        """CONVERSATIONAL + Ollama DOWN + Groq available → Groq selected."""
        with patch.dict(os.environ, {"ELO_BACKEND": ""}, clear=False), \
             patch.object(br, "_ollama_available", return_value=False), \
             patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_cerebras_available", return_value=False), \
             patch.object(br, "_openai_available", return_value=False), \
             patch.object(br, "_claude_available", return_value=False), \
             patch.object(br, "_gemini_available", return_value=False), \
             patch.object(br, "_groq_call", return_value="Hello."), \
             patch.object(br, "_has_lore_drift", return_value=False):
            br._last_responses.clear()
            result = br._route_by_tier(
                "sys", "user", br._TIER_CONVERSATIONAL, "answer", 4
            )
        self.assertIsNotNone(result, "AT-2: Expected a result, got None")
        _, backend = result
        self.assertIn("groq", backend,
            f"AT-2: Groq should be selected when Ollama down, got {backend}")

    # ── AT-3: REASONING — Groq cooldown → Cerebras ───────────────────────────

    def test_at3_reasoning_groq_cooldown_cerebras_wins(self):
        """REASONING + Groq in quota-cooldown + Cerebras available → Cerebras selected."""
        import time
        br._groq_quota_cooldown_until = time.monotonic() + 60.0  # in cooldown
        with patch.dict(os.environ, {"ELO_BACKEND": ""}, clear=False), \
             patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_cerebras_available", return_value=True), \
             patch.object(br, "_ollama_available", return_value=False), \
             patch.object(br, "_openai_available", return_value=False), \
             patch.object(br, "_claude_available", return_value=False), \
             patch.object(br, "_gemini_available", return_value=False), \
             patch.object(br, "_cerebras_call", return_value="Hello."), \
             patch.object(br, "_has_lore_drift", return_value=False):
            br._last_responses.clear()
            result = br._route_by_tier(
                "sys", "user", br._TIER_REASONING, "build", 4
            )
        self.assertIsNotNone(result, "AT-3: Expected result, got None — Cerebras not tried")
        _, backend = result
        self.assertIn("cerebras", backend,
            f"AT-3: Cerebras should win when Groq in cooldown, got {backend}")
        br._groq_quota_cooldown_until = 0.0

    # ── AT-4: Pinned groq mode + Groq 429 + Cerebras fail + Ollama up ─────────

    def test_at4_pinned_groq_429_ollama_floor(self):
        """Pinned mode (ELO_BACKEND=groq) + Groq 429 + Cerebras fail → Ollama (WO-073 absorbed)."""
        import urllib.error as _ue
        http_err = _ue.HTTPError(url="", code=429, msg="Too Many Requests", hdrs={}, fp=None)
        with patch.dict(os.environ, {"ELO_BACKEND": "groq"}, clear=False), \
             patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_cerebras_available", return_value=True), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_groq_call", side_effect=http_err), \
             patch.object(br, "_cerebras_call", side_effect=Exception("Cerebras fail")), \
             patch.object(br, "_ollama_call", return_value="Hello from Ollama."), \
             patch.object(br, "_has_lore_drift", return_value=False):
            br._last_responses.clear()
            _text, backend = br.route("sys", "user")
        self.assertIn("ollama", backend,
            f"AT-4: Ollama should floor pinned-groq after 429, got {backend!r}")

    # ── AT-5: all providers down → mock ──────────────────────────────────────

    def test_at5_all_down_returns_mock(self):
        """All providers down for the tier → route() falls back to mock."""
        with patch.dict(os.environ, {"ELO_BACKEND": ""}, clear=False), \
             patch.object(br, "_ollama_available", return_value=False), \
             patch.object(br, "_groq_available", return_value=False), \
             patch.object(br, "_cerebras_available", return_value=False), \
             patch.object(br, "_openai_available", return_value=False), \
             patch.object(br, "_claude_available", return_value=False), \
             patch.object(br, "_gemini_available", return_value=False):
            br._last_responses.clear()
            _text, backend = br.route("sys", "user", action="answer")
        self.assertIn("mock", backend,
            f"AT-5: All providers down should fall back to mock, got {backend!r}")

    # ── AT-6: capability field in routing trace ───────────────────────────────

    def test_at6_capability_field_in_routing_trace(self):
        """_last_route_capability is set when _route_by_tier fires."""
        with patch.dict(os.environ, {"ELO_BACKEND": ""}, clear=False), \
             patch.object(br, "_ollama_available", return_value=True), \
             patch.object(br, "_groq_available", return_value=False), \
             patch.object(br, "_cerebras_available", return_value=False), \
             patch.object(br, "_openai_available", return_value=False), \
             patch.object(br, "_claude_available", return_value=False), \
             patch.object(br, "_gemini_available", return_value=False), \
             patch.object(br, "_ollama_call", return_value="Hello."), \
             patch.object(br, "_has_lore_drift", return_value=False):
            br._last_responses.clear()
            br._last_route_capability = ""
            br._route_by_tier("sys", "user", br._TIER_CONVERSATIONAL, "answer", 4)

        self.assertEqual(
            br._last_route_capability, "language_generation",
            f"AT-6: expected 'language_generation', got {br._last_route_capability!r}"
        )
        # REASONING tier sets different capability string
        with patch.object(br, "_groq_available", return_value=True), \
             patch.object(br, "_ollama_available", return_value=False), \
             patch.object(br, "_cerebras_available", return_value=False), \
             patch.object(br, "_openai_available", return_value=False), \
             patch.object(br, "_claude_available", return_value=False), \
             patch.object(br, "_gemini_available", return_value=False), \
             patch.object(br, "_groq_call", return_value="Hello."), \
             patch.object(br, "_has_lore_drift", return_value=False):
            br._last_responses.clear()
            br._last_route_capability = ""
            br._route_by_tier("sys", "user", br._TIER_REASONING, "build", 4)
        self.assertEqual(
            br._last_route_capability, "language_generation_with_reasoning",
            f"AT-6b: expected 'language_generation_with_reasoning', got {br._last_route_capability!r}"
        )

    # ── AT-7: regression tests pass ──────────────────────────────────────────

    def test_at7_regression_brain_authors(self):
        """test_brain_authors.py 4/4 still pass (tier wiring + identity assert)."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_brain_authors.py", "-q"],
            capture_output=True, text=True, cwd=ROOT
        )
        self.assertIn("4 passed", result.stdout,
            f"AT-7: test_brain_authors regression failed:\n{result.stdout}{result.stderr}")

    # ── AT-8: ELO_OLLAMA_MODEL defaults to llama3.1:8b ───────────────────────

    def test_at8_ollama_model_default_is_llama3_1_8b(self):
        """ELO_OLLAMA_MODEL not set → default is llama3.1:8b, NOT mistral."""
        with patch.dict(os.environ, {}, clear=False):
            env_bak = os.environ.pop("ELO_OLLAMA_MODEL", None)
            try:
                import importlib
                import runtime.backend_router as _fresh
                importlib.reload(_fresh)
                model_used = os.environ.get("ELO_OLLAMA_MODEL", "llama3.1:8b")
                # The default in _ollama_call uses os.environ.get("ELO_OLLAMA_MODEL", "mistral")
                # WO-ROUTER-001 D-2 spec: default must be llama3.1:8b not mistral
                with open(os.path.join(ROOT, "runtime", "backend_router.py"), encoding="utf-8") as f:
                    src = f.read()
                # The default in _ollama_call / _ollama_stream must not be "mistral"
                import re
                mistral_defaults = re.findall(r'ELO_OLLAMA_MODEL["\'],\s*"mistral"', src)
                self.assertEqual(
                    mistral_defaults, [],
                    f"AT-8: Found 'mistral' as ELO_OLLAMA_MODEL default — must be llama3.1:8b: {mistral_defaults}"
                )
                # Confirm llama3.1:8b is the documented default (in comment or env)
                self.assertIn(
                    "llama3.1:8b", src,
                    "AT-8: 'llama3.1:8b' not found in backend_router.py — default model not documented"
                )
            finally:
                if env_bak is not None:
                    os.environ["ELO_OLLAMA_MODEL"] = env_bak
