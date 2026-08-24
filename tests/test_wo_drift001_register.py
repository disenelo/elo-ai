"""
tests/test_wo_drift001_register.py — WO-DRIFT-001 §C/§D acceptance tests.

Card 0060: eLo jammed in GROUND register (2026-08-20 incident).

Tests:
  T1  F-3 fix: David's key turns do NOT all route to ground/reflect
  T2  "Food wise, are you defaulting to Cerebas?" → answer, not ground
  T3  _is_duplicate catches near-identical Ollama generations
  T4  _last_responses[action] populated after _finish() on Cerebras/Ollama paths
  T5  valence classification — shopping sentence is NOT negative_low
  T6  duplicate guard: _finish() updates _last_responses (regression vs §C pre-fix)

Tests gated on live stack (marked skip):
  T_LIVE_7  "yo" through pipeline does not return grounding restatement

Run: python3 tests/test_wo_drift001_register.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pytest


# ── T1: F-3 fix — David's turns no longer ALL route to ground/reflect ────────

def test_t1_david_turns_not_all_ground():
    from runtime.executive import _conversation_action
    turns = [
        # (user_input, intent, valence, momentum)
        ("Okay I need to go shop and buy some food for dinner", "conversation", "neutral", "stable"),
        ("Yeah I was trying to budget with Gemini", "inquiry", "neutral", "stable"),
        ("Food wise, are you defaulting to Cerebas?", "inquiry", "neutral", "stable"),
        ("I got to check your routing", "conversation", "neutral", "stable"),
    ]
    actions = [_conversation_action(*t)["action"] for t in turns]
    grounded = sum(1 for a in actions if a in ("ground", "reflect"))
    assert grounded < len(turns), (
        f"F-3 REGRESSED: all {len(turns)} turns → ground/reflect: {actions}"
    )
    assert "answer" in actions, f"No turn reached 'answer': {actions}"


# ── T2: question → answer (§B fix: neutral valence + inquiry intent = answer) ─

def test_t2_food_question_routes_to_answer():
    from runtime.executive import _conversation_action
    result = _conversation_action(
        "Food wise, are you defaulting to Cerebas?",
        "inquiry", "neutral", "stable"
    )
    assert result["action"] == "answer", (
        f"Expected 'answer' for food question, got {result['action']!r} (reason={result.get('reason')})"
    )


# ── T3: _is_duplicate catches near-identical generations ──────────────────────

def test_t3_duplicate_guard_fires():
    from runtime.backend_router import _is_duplicate
    # Identical sentence → always flagged
    same = "You were thinking about your budget earlier and now here we are."
    assert _is_duplicate(same, same), (
        "_is_duplicate: identical sentence must be flagged"
    )
    # Clearly distinct → not flagged
    distinct = "That sounds like a good plan — enjoy the shops."
    assert not _is_duplicate(distinct, same), (
        "_is_duplicate should NOT flag clearly distinct generations"
    )
    # Empty prev → never a duplicate
    assert not _is_duplicate(same, ""), "_is_duplicate with empty prev must be False"


# ── T4: _finish() updates _last_responses so duplicate guard is armed ─────────

def test_t4_finish_updates_last_responses():
    from runtime.backend_router import _finish, _last_responses
    _last_responses.clear()
    action = "reflect"
    out = _finish("You were thinking about the budget.", action, max_sentences=3, backend="ollama")
    assert _last_responses.get(action), (
        f"_last_responses[{action!r}] not set after _finish() — §C guard is blind"
    )
    assert _last_responses[action] == out, (
        "_last_responses[action] must store the normalised output from _finish()"
    )


# ── T5: shopping sentence is NOT classified negative_low ─────────────────────

def test_t5_shopping_sentence_not_negative_low():
    from core.memory_relevance_filter import _emotional_context
    ctx = _emotional_context(
        "Okay I need to go shop and buy some food for dinner",
        []
    )
    valence = ctx.get("valence", "neutral")
    assert valence not in ("negative_low", "negative_high"), (
        f"Shopping sentence mis-classified as {valence!r} — this is what jammed the GROUND gate"
    )


# ── T6: _finish raises ValueError on second identical call (guard is armed) ───

def test_t6_consecutive_duplicate_via_finish():
    from runtime.backend_router import _finish, _last_responses
    _last_responses.clear()
    action = "ground"
    identical_raw = "You are feeling a bit stuck right now let me slow down with you."
    # First call succeeds and stores in _last_responses
    out1 = _finish(identical_raw, action, max_sentences=3, backend="ollama")
    assert out1, "First _finish call must return a non-empty response"
    assert _last_responses.get(action), "_last_responses must be populated after first call"
    # Second identical call must raise ValueError (guard fires) — this is §C confirmed
    with pytest.raises(ValueError, match="duplicate"):
        _finish(identical_raw, action, max_sentences=3, backend="ollama")
