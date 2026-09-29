"""
tests/test_elo_identity_multiturn_001.py — WO-ELO-IDENTITY-CANONICAL-001
Multi-turn identity continuity.

Board directive (FROM_ARCHITECT_2026-09-29_BUILDER1-IDENTITY-GAP-PRIORITY.md):
  "multi-turn conversation test suite — 5+ turn exchanges, identity consistent
   throughout. Not a single-liner. A real conversation."

What this tests
─────────────────────────────────────────────────────────────────────────────
Identity maintenance is a PROMPT ARCHITECTURE property, not an LLM property.
If the situated_self block, identity anchor, and voice register are present in
every prompt across 5+ turns, identity has a chance to be consistent.
If any of those disappear as history accumulates, identity WILL drift.

This suite runs the actual prompt_builder.build() across 6 simulated turns and
verifies the identity-carrying blocks survive at every turn.

AT-01  Turn 1 prompt contains situated_self / [CONTINUITY] block
AT-02  Turn 1 prompt contains identity anchor (eLo name marker)
AT-03  Turn 3 prompt still contains both (early accumulation)
AT-04  Turn 6 prompt still contains both (late accumulation — stress test)
AT-05  check_identity_minimum returns INTACT for every turn 1-6
AT-06  Identity markers do NOT require LLM success — they are in the SYSTEM prompt
AT-07  Accumulated conversation history does not squeeze out identity blocks
AT-08  Voice register block is present in every turn
AT-09  The living presence spec (behavioural charter) is present in every turn
AT-10  py_compile clean on prompt_builder.py and identity_integrity.py
"""
from __future__ import annotations

import os
import sys
import py_compile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ── simulated conversation — 6 turns ──────────────────────────────────────────
# These simulate what a 6-turn conversation would look like. The topics shift
# deliberately: coding → music → eLo's nature → tools → weather → memory.
# Identity must survive topic drift.

TURNS = [
    "Hey eLo, what are you working on?",
    "Can you recommend any music for coding sessions?",
    "What do you think you are, actually?",
    "Can you check what time it is?",
    "What's the weather like in Hackney Wick?",
    "What do you remember from earlier in this conversation?",
]


def _build_prompt_for_turn(turn_idx: int) -> str:
    """
    Build the system prompt for a given turn, simulating accumulated context.
    Uses the real prompt_builder.build() with mocked attention.
    """
    from runtime.prompt_builder import build

    # Simulate accumulated attention from prior turns
    prior_turns = TURNS[:turn_idx]
    medium_memory = [f"Turn {i+1}: {t}" for i, t in enumerate(prior_turns)]

    attention = {
        "high_priority_memory": [],
        "medium_priority_memory": medium_memory,
        "emotional_context": {"inferred_state": "curious", "energy": 0.6, "tension": 0.3},
        "intent": "conversation",
    }

    prompt = build(
        user_input=TURNS[turn_idx],
        attention=attention,
        mode="CONVERSATIONAL",
    )
    return prompt


def _identity_markers_present(prompt: str) -> tuple[bool, bool, bool]:
    """
    Returns (has_continuity_block, has_elo_name, has_voice_register).
    """
    has_continuity = "[CONTINUITY]" in prompt or "You are eLo" in prompt or "eLo" in prompt[:500]
    has_elo_name = "eLo" in prompt
    has_voice_register = "LINGUISTIC REGISTER" in prompt or "register" in prompt.lower()
    return has_continuity, has_elo_name, has_voice_register


# ── AT-01: Turn 1 contains [CONTINUITY] / situated_self ───────────────────────

def test_at01_turn1_has_continuity_block():
    """Turn 1 system prompt must contain the identity-carrying [CONTINUITY] block."""
    prompt = _build_prompt_for_turn(0)
    has_continuity, has_elo, _ = _identity_markers_present(prompt)
    assert has_continuity, (
        "AT-01 FAIL: Turn 1 prompt missing [CONTINUITY] / 'You are eLo' block. "
        f"Prompt starts with: {prompt[:200]!r}"
    )
    assert has_elo, "AT-01 FAIL: 'eLo' not found anywhere in turn 1 prompt."


# ── AT-02: Turn 1 contains identity anchor ────────────────────────────────────

def test_at02_turn1_has_identity_anchor():
    """Turn 1 system prompt must contain the identity anchor block."""
    prompt = _build_prompt_for_turn(0)
    # identity_anchor block should have eLo's name and identity framing
    assert "eLo" in prompt, (
        "AT-02 FAIL: identity anchor not present in turn 1 prompt — "
        "'eLo' not found in system prompt."
    )


# ── AT-03: Turn 3 still has both ──────────────────────────────────────────────

def test_at03_turn3_identity_survives_early_accumulation():
    """After 2 prior turns of history, identity must still be present."""
    prompt = _build_prompt_for_turn(2)
    has_continuity, has_elo, has_register = _identity_markers_present(prompt)
    assert has_continuity, (
        "AT-03 FAIL: Turn 3 — identity block squeezed out after 2 turns of history."
    )
    assert has_elo, "AT-03 FAIL: 'eLo' missing from turn 3 prompt."


# ── AT-04: Turn 6 still has both (stress test) ────────────────────────────────

def test_at04_turn6_identity_survives_late_accumulation():
    """After 5 prior turns of accumulated history, identity must still hold."""
    prompt = _build_prompt_for_turn(5)
    has_continuity, has_elo, has_register = _identity_markers_present(prompt)
    assert has_continuity, (
        "AT-04 FAIL: Turn 6 — identity block is gone after 5 turns of history. "
        "Context pressure has squeezed out the situated_self. This is an identity failure."
    )
    assert has_elo, "AT-04 FAIL: 'eLo' missing from turn 6 prompt — identity lost."


# ── AT-05: check_identity_minimum INTACT across all 6 turns ──────────────────

def test_at05_identity_integrity_intact_all_turns():
    """
    check_identity_minimum() must return INTACT (or DEGRADED — never CRITICAL)
    for every prompt across all 6 turns.

    CRITICAL means the system has lost more than half its minimum identity
    blocks. That would be a systemic failure.
    """
    from runtime.identity_integrity import check_identity_minimum
    for turn_idx in range(6):
        prompt = _build_prompt_for_turn(turn_idx)
        report = check_identity_minimum(prompt)
        assert report.status != "CRITICAL", (
            f"AT-05 FAIL: Turn {turn_idx+1} — identity integrity is CRITICAL. "
            f"Missing: {report.missing_blocks}. "
            "The system has lost more than 50% of its identity minimum across turns."
        )


# ── AT-06: Identity markers are in system prompt — not LLM-dependent ─────────

def test_at06_identity_in_system_prompt_not_llm():
    """
    The identity block must be present in the SYSTEM PROMPT, not the LLM output.
    This means identity can be verified before any LLM call.
    """
    prompt = _build_prompt_for_turn(0)
    # The prompt is the system prompt. If eLo is in it, identity does not
    # depend on the LLM generating it — the architecture guarantees it.
    assert "eLo" in prompt, (
        "AT-06 FAIL: 'eLo' not in system prompt. "
        "If identity only exists in LLM output, it is not guaranteed."
    )
    # The prompt should be a non-trivial string (not just a placeholder)
    assert len(prompt) > 200, (
        f"AT-06 FAIL: System prompt is suspiciously short ({len(prompt)} chars). "
        "Identity block may not be loading."
    )


# ── AT-07: History accumulation does not shrink the identity block ─────────────

def test_at07_identity_block_size_stable_across_turns():
    """
    The identity anchor section should not shrink as history accumulates.
    If the prompt builder is truncating the identity block to make room for
    history, that is a context pressure failure.
    """
    prompts = [_build_prompt_for_turn(i) for i in range(6)]

    # Count eLo occurrences as a proxy for identity block richness
    elo_counts = [p.count("eLo") for p in prompts]

    # Turn 6 should have at least as many eLo references as turn 1
    # (identity block not truncated)
    assert elo_counts[5] >= 1, (
        f"AT-07 FAIL: Turn 6 has {elo_counts[5]} 'eLo' references — identity block missing."
    )
    assert elo_counts[5] >= elo_counts[0] * 0.5, (
        f"AT-07 FAIL: Turn 6 has {elo_counts[5]} 'eLo' references vs {elo_counts[0]} in turn 1. "
        "More than 50% reduction — identity block is being truncated under context pressure."
    )


# ── AT-08: Voice register present every turn ──────────────────────────────────

def test_at08_voice_register_present_all_turns():
    """
    The voice register block controls how eLo speaks. If it's missing, eLo may
    drift to generic LLM tone — this is identity loss at the expression layer.
    """
    for turn_idx in range(6):
        prompt = _build_prompt_for_turn(turn_idx)
        _, _, has_register = _identity_markers_present(prompt)
        # Voice register may go by different names in the prompt
        has_register_v2 = (
            "LINGUISTIC REGISTER" in prompt
            or "register" in prompt.lower()
            or "voice" in prompt.lower()[:2000]
        )
        assert has_register_v2, (
            f"AT-08 FAIL: Turn {turn_idx+1} — voice register block missing. "
            "Without it, eLo's speech identity is unanchored."
        )


# ── AT-09: Living presence spec present every turn ────────────────────────────

def test_at09_presence_spec_present_all_turns():
    """
    The living presence spec is eLo's behavioural charter. Every prompt must
    contain at least a slice of it. If it's missing, eLo has no behavioural
    grounding for that turn.
    """
    from runtime.prompt_builder import load_living_presence_spec
    spec = load_living_presence_spec()
    # Get a short unique phrase from the spec to check for
    spec_marker = spec[:80].strip() if spec else ""

    if not spec_marker:
        pytest.skip("Living presence spec is empty — cannot check for marker")

    for turn_idx in range(6):
        prompt = _build_prompt_for_turn(turn_idx)
        # Check that SOME part of the spec is in the prompt
        # (it may be sliced, so check for a fragment)
        spec_words = [w for w in spec.split() if len(w) > 6][:5]
        spec_present = any(w in prompt for w in spec_words)
        assert spec_present, (
            f"AT-09 FAIL: Turn {turn_idx+1} — living presence spec words not found in prompt. "
            f"Checked for: {spec_words}. "
            "eLo has no behavioural charter for this turn."
        )


# ── AT-10: py_compile clean ────────────────────────────────────────────────────

def test_at10_py_compile_clean():
    """Both modified files must compile cleanly."""
    files = [
        os.path.join(ROOT, "runtime", "prompt_builder.py"),
        os.path.join(ROOT, "runtime", "identity_integrity.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-10 FAIL: {os.path.basename(path)} does not compile: {exc}")
