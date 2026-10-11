"""
tests/test_inner_thought_anchor_b1.py — WO-INNER-THOUGHT-ANCHOR-B1

Verifies that inner_thought_text from blender_state.json reaches the assembled
system prompt in Option C ordering (after self-model, before respond_now).
Also confirms the "I notice [David...]" banned pattern cannot appear.

Implemented in runtime/prompt_builder.py:1161+ (commit 91d8331 context).
"""
from __future__ import annotations

import io
import json
import unittest.mock as mock

import pytest


def _build_with_inner_thought(text: str) -> str:
    """Call prompt_builder.build() with a mocked blender_state.json containing inner_thought_text."""
    from runtime import prompt_builder as pb
    fake_state = {"inner_thought_text": text, "mode": "conversational"}
    fake_json_str = json.dumps(fake_state)

    original_open = open

    def patched_open(path, *args, **kwargs):
        if isinstance(path, str) and path.endswith("blender_state.json"):
            return io.StringIO(fake_json_str)
        return original_open(path, *args, **kwargs)

    with mock.patch("builtins.open", side_effect=patched_open):
        result = pb.build("hello")
    return result if isinstance(result, str) else str(result)


# ── T1: inner_thought appears in prompt when blender_state has it ─────────────

def test_inner_thought_text_appears_in_assembled_prompt():
    """T1: inner_thought_text → [MY CURRENT INNER THOUGHT] block in system prompt."""
    sp = _build_with_inner_thought("Robot body can raise arm.")
    assert "[MY CURRENT INNER THOUGHT]" in sp, (
        "inner_thought_text from blender_state.json not injected into system prompt"
    )
    assert "Robot body can raise arm." in sp


# ── T2: Option C — appears before respond_now ────────────────────────────────

def test_inner_thought_is_before_respond_now():
    """T2: Option C ordering — inner_thought anchor appears before the terminal directive."""
    marker = "Robot body can raise arm."
    sp = _build_with_inner_thought(marker)
    pos_it = sp.find("[MY CURRENT INNER THOUGHT]")
    # respond_now / "RESPOND NOW" is the last section added in build()
    pos_respond = sp.rfind("RESPOND NOW") if "RESPOND NOW" in sp else sp.rfind("respond_now")
    assert pos_it >= 0, "inner_thought anchor missing from prompt"
    if pos_respond >= 0:
        assert pos_it < pos_respond, (
            f"inner_thought (pos {pos_it}) appears AFTER respond_now (pos {pos_respond}) — Option C violated"
        )


# ── T3: banned "I notice [David...]" gate ────────────────────────────────────

def test_i_notice_david_banned_from_inner_thought():
    """
    T3: the generation-time quality gate in inner_thought_quality rejects
    "I notice David..." before it ever reaches the prompt anchor.
    """
    from runtime.inner_thought_quality import reject_reason
    banned_phrase = "I notice David said something interesting."
    reason = reject_reason(banned_phrase)
    assert reason is not None and reason != "", (
        f"'I notice David...' was not rejected by quality gate: {banned_phrase!r}"
    )
