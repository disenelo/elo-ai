"""
tests/test_capability_fabric.py — WO-B1-0105

Tests for:
  - runtime/identity_kernel.py: four invariants + two_truths_gate()
  - runtime/prompt_builder.py:  build_faculty_prompt() typed contracts

All tests are headless (no live server, no LLM calls).
"""

import pytest
from runtime.identity_kernel import (
    IDENTITY,
    _CAPABILITY_INVARIANTS,
    two_truths_gate,
)
from runtime.prompt_builder import build_faculty_prompt


# ── Identity kernel — invariants ───────────────────────────────────────────────

class TestIdentityKernelInvariants:
    def test_four_invariants_present(self):
        assert len(_CAPABILITY_INVARIANTS) == 4

    def test_invariant_1_capabilities_dont_replace_identity(self):
        assert any("must not replace" in inv.lower() or "identity" in inv.lower()
                   for inv in _CAPABILITY_INVARIANTS)

    def test_invariant_2_tools_provide_results_elo_responds(self):
        assert any("external tools" in inv.lower() or "tools provide results" in inv.lower()
                   for inv in _CAPABILITY_INVARIANTS)

    def test_invariant_3_inner_life_continuous(self):
        assert any("inner life" in inv.lower() or "continuous" in inv.lower()
                   for inv in _CAPABILITY_INVARIANTS)

    def test_invariant_4_elo_recognises_need(self):
        assert any("recognises a need" in inv.lower() or "does not select a tier" in inv.lower()
                   for inv in _CAPABILITY_INVARIANTS)

    def test_identity_singleton_loadable(self):
        assert IDENTITY is not None
        assert IDENTITY.purpose
        assert IDENTITY.core_philosophy


# ── two_truths_gate() ──────────────────────────────────────────────────────────

class TestTwoTruthsGate:
    def test_no_operational_result_synthesise(self):
        result = two_truths_gate(None)
        assert result["synthesise"] is True
        assert result["fast_answer"] is None
        assert result["operational"] is None

    def test_definitive_macOS_fast_answer(self):
        op = {"value": "3:45 PM", "source": "macOS", "authority": "definitive", "confidence": 1.0, "freshness": "live"}
        result = two_truths_gate(op)
        assert result["fast_answer"] == "3:45 PM"
        assert result["synthesise"] is False
        assert result["operational"] is op

    def test_definitive_macOS_math(self):
        op = {"value": "2072", "source": "macOS", "authority": "definitive", "confidence": 1.0, "freshness": "live"}
        result = two_truths_gate(op)
        assert result["fast_answer"] == "2072"
        assert result["synthesise"] is False

    def test_recorded_truth_needs_synthesis(self):
        op = {"value": "Building capability fabric", "source": "elo_state", "authority": "recorded", "confidence": 0.9, "freshness": "live"}
        result = two_truths_gate(op)
        assert result["synthesise"] is True
        assert result["fast_answer"] is None

    def test_inference_truth_needs_synthesis(self):
        op = {"value": "probably working on WO-0105", "source": "memory", "authority": "inference", "confidence": 0.7, "freshness": 300}
        result = two_truths_gate(op)
        assert result["synthesise"] is True

    def test_value_none_synthesise(self):
        op = {"value": None, "source": "macOS", "authority": "definitive", "confidence": 1.0, "freshness": "live"}
        result = two_truths_gate(op)
        assert result["synthesise"] is True
        assert result["fast_answer"] is None

    def test_identity_response_preserved(self):
        op = {"value": "3:45 PM", "source": "macOS", "authority": "definitive", "confidence": 1.0, "freshness": "live"}
        result = two_truths_gate(op, identity_response="I can tell you the time.")
        assert result["identity"] == "I can tell you the time."

    def test_operational_truth_not_overridden(self):
        """INVARIANT 2: operational result is preserved verbatim in gate output."""
        op = {"value": "14:23", "source": "macOS", "authority": "definitive", "confidence": 1.0, "freshness": "live"}
        result = two_truths_gate(op)
        # The gate must return the operational result unchanged
        assert result["operational"]["value"] == "14:23"
        assert result["operational"]["authority"] == "definitive"


# ── build_faculty_prompt() — typed contracts ───────────────────────────────────

class TestBuildFacultyPrompt:
    def test_executive_prompt_contains_packet_fields_not_raw_dump(self):
        packet = {
            "goal": "Ship WO-0105 today",
            "facts": ["capability_dispatcher done", "identity_kernel updated"],
            "state": "WO queue has 0105 and 0106 remaining",
            "constraints": ["no server tests during David session"],
            "options": ["build partial", "build full"],
        }
        prompt = build_faculty_prompt("executive", packet)
        assert "GOAL: Ship WO-0105 today" in prompt
        assert "capability_dispatcher done" in prompt
        assert "EXECUTIVE FACULTY" in prompt
        # Must NOT contain raw conversation history dump markers
        assert "[DIRECTIVE — THIS RESPONSE ONLY]" not in prompt

    def test_executive_prompt_has_identity_anchor(self):
        packet = {"goal": "decide what to build next"}
        prompt = build_faculty_prompt("executive", packet)
        assert "[IDENTITY ANCHOR]" in prompt

    def test_executive_prompt_has_decision_contract(self):
        packet = {"goal": "what should I do?"}
        prompt = build_faculty_prompt("executive", packet)
        assert "decision" in prompt.lower()
        assert "rationale" in prompt.lower()
        assert "next action" in prompt.lower() or "next_action" in prompt.lower()

    def test_planning_prompt_typed(self):
        packet = {
            "goal": "finish capability fabric",
            "current_state": "identity_kernel done, prompt_builder done",
            "constraints": ["no breaking changes to build()"],
        }
        prompt = build_faculty_prompt("planning", packet)
        assert "PLANNING FACULTY" in prompt
        assert "GOAL: finish capability fabric" in prompt
        assert "CURRENT STATE" in prompt
        assert "no breaking changes" in prompt
        assert "[IDENTITY ANCHOR]" in prompt

    def test_planning_prompt_has_plan_contract(self):
        packet = {"goal": "build the daemon"}
        prompt = build_faculty_prompt("planning", packet)
        assert "plan" in prompt.lower()
        assert "blockers" in prompt.lower()

    def test_creativity_prompt_typed(self):
        packet = {
            "intent": "make eLo's idle more expressive",
            "constraints": ["no new dependencies", "must work with current ambient_engine"],
            "reference_context": "ambient_engine has _wander_gaze and _idle_breathe",
        }
        prompt = build_faculty_prompt("creativity", packet)
        assert "CREATIVITY FACULTY" in prompt
        assert "INTENT: make eLo's idle" in prompt
        assert "REFERENCE CONTEXT" in prompt
        assert "[IDENTITY ANCHOR]" in prompt

    def test_creativity_prompt_has_ideas_contract(self):
        packet = {"intent": "express curiosity differently"}
        prompt = build_faculty_prompt("creativity", packet)
        assert "ideas" in prompt.lower()
        assert "rationale" in prompt.lower()

    def test_identity_preserved_in_all_faculties(self):
        """INVARIANT 1: faculty prompt never replaces identity."""
        for faculty in ("executive", "planning", "creativity"):
            prompt = build_faculty_prompt(faculty, {"goal": "test"})
            assert "[IDENTITY ANCHOR]" in prompt
            assert "You are eLo" in prompt or "eLo" in prompt

    def test_faculty_receives_classified_packet_not_raw_dump(self):
        """The faculty prompt must contain intent/context/task fields, not a full context blob."""
        packet = {
            "intent": "decide",
            "goal": "ship today",
            "facts": ["fact A", "fact B"],
        }
        exec_prompt = build_faculty_prompt("executive", packet)
        # The prompt is focused — it contains the packet keys
        assert "goal" in exec_prompt.lower() or "GOAL" in exec_prompt
        # It does NOT contain the living_presence_spec (that's the full build() path)
        assert "LIVING PRESENCE" not in exec_prompt

    def test_unknown_faculty_doesnt_crash(self):
        prompt = build_faculty_prompt("analyze", {"task": "do something"})
        assert "[IDENTITY ANCHOR]" in prompt
        assert "analyze" in prompt.lower() or "FACULTY" in prompt

    def test_inner_life_not_suspended_during_capability_call(self):
        """
        INVARIANT 3: inner life is continuous, not suspended.
        This is an architectural contract test — build_faculty_prompt must not
        inject anything that blocks or halts the inner_thought loop.
        We verify by checking no suspension keywords appear in the output.
        """
        packet = {"goal": "calculate 28 × 74", "facts": ["result: 2072"]}
        prompt = build_faculty_prompt("executive", packet)
        suspension_keywords = ["pause inner", "suspend inner", "stop thinking", "halt life"]
        for kw in suspension_keywords:
            assert kw not in prompt.lower(), f"Found suspension keyword: '{kw}'"
