"""
tests/test_inner_thought_quality.py — an inner thought that says nothing is
worse than none.

Board P0 2026-10-05, both verbatim from David's session log:

    "the thing I decided not to lead with: 'I'm eLo: calm, observant, playful'"
    "I am settling into a moment of quiet reflection, letting go of any urgency"

The first is the system prompt read back as a thought — "calm, observant,
playful" is a verbatim run from the Core traits line in prompt_builder. The
second is a meditation app.

The Board's standard is David's own example: "well not smarter just more
equipped analytically". The instruction is explicit that suppressing beats
emitting filler, so every rejection yields no thought rather than a
safer-sounding one.
"""
from __future__ import annotations

import pathlib

import pytest

from runtime.inner_thought_quality import (
    _core_traits, is_emittable, reject_reason,
)


# ── the live failures ───────────────────────────────────────────────────────

def test_the_system_prompt_is_not_a_thought():
    why = reject_reason(
        "the thing I decided not to lead with: 'I'm eLo: calm, observant, playful'",
        asked="who are you", reply="I am eLo.",
    )
    assert why, "the model narrating its own context was emitted as a thought"
    assert "character definition" in why


def test_the_trait_descriptor_alone_is_also_caught():
    """Without the 'I'm eLo:' framing, the trait run still gives it away."""
    assert reject_reason(
        "I keep landing on calm, observant, playful when I describe it",
        asked="describe yourself", reply="Hard to say.",
    )


def test_meditation_app_filler_is_rejected():
    why = reject_reason(
        "I am settling into a moment of quiet reflection, letting go of any urgency.",
        asked="do you remember pinkie and the brain",
        reply="I don't have that recorded.",
    )
    assert "filler" in why


def test_filler_is_rejected_even_when_it_mentions_the_topic():
    """
    The contradiction case: the thought referenced Pinkie and the Brain, so a
    relevance check alone would have passed it. It is still filler.
    """
    assert reject_reason(
        "I am settling into a moment of clarity, acknowledging the reference "
        "to Pinkie and the Brain without needing to record it.",
        asked="do you remember pinkie and the brain",
        reply="I don't have that recorded.",
    )


def test_the_existing_rule_based_fallback_is_filler_too():
    """
    server.py falls back to "I'm present for this." when generation is slow.
    By the Board's definition that references nothing, so the gate suppresses
    it. Stated here because it is a real behaviour change, not an oversight.
    """
    assert reject_reason("I'm present for this.",
                         asked="how is the seams work", reply="Going well.")


# ── the standard must pass ──────────────────────────────────────────────────

def test_davids_canonical_example_passes():
    assert is_emittable(
        "well not smarter just more equipped analytically",
        asked="are you smarter than me", reply="I am in theory only",
    )


@pytest.mark.parametrize("thought,asked,reply", [
    ("the seams work is further along than I let on",
     "how is the seams addon", "Coming together."),
    ("he asked about the battery but the real question is the sit threshold",
     "how is the battery", "Draining normally."),
    ("I almost said no and that would have been wrong",
     "can you dream", "Yes, really."),
])
def test_specific_thoughts_pass(thought, asked, reply):
    assert is_emittable(thought, asked=asked, reply=reply), reject_reason(
        thought, asked=asked, reply=reply)


def test_an_untethered_thought_is_rejected():
    assert reject_reason("the weather turned cold earlier than usual",
                         asked="how is the seams work", reply="Going well.")


def test_no_context_means_nothing_to_be_untethered_from():
    """A thought is not punished for a turn we cannot see."""
    assert is_emittable("the corridor was the point", asked="", reply="")


# ── drift ratchet ───────────────────────────────────────────────────────────

def test_the_traits_are_read_from_prompt_builder_not_copied():
    traits = _core_traits()
    assert "calm" in traits and "observant" in traits and "playful" in traits, (
        "the Core traits line in prompt_builder moved or was renamed — the "
        "trait check is now silently inert"
    )
    # Checked by BEHAVIOUR, not by searching the source for the phrase — the
    # module's own docstring quotes the live failure, so a text search finds
    # it there and proves nothing. Point the reader at a missing file: a
    # copied list would survive that, a read one cannot.
    import runtime.inner_thought_quality as itq

    real = itq._PROMPT_BUILDER
    try:
        itq._PROMPT_BUILDER = "/nonexistent/prompt_builder.py"
        assert itq._core_traits() == [], (
            "traits survived prompt_builder being unreadable — they are "
            "copied into this module, not read from it"
        )
    finally:
        itq._PROMPT_BUILDER = real


# ── ordering: a dream thought must survive the gate ─────────────────────────

def test_the_gate_runs_before_the_dream_override():
    """
    A dream insight is SUPPOSED to be untethered from the turn — that is what
    waking with something in your head is. Gating it on turn-relevance would
    delete the feature 02ef0ae built, so the gate must sit above the override.
    """
    src = (pathlib.Path(__file__).resolve().parent.parent / "server.py").read_text()
    gate = src.index("from runtime.inner_thought_quality import")
    dream = src.index("# S2 Phase 3 — the dream wins.")
    assert gate < dream, "the quality gate would suppress eLo's dream thoughts"


# ── the prompt must not ask for what the gate rejects ───────────────────────
#
# The Board blamed the model for "I am settling into a moment of quiet
# reflection, letting go of any urgency". It was not the model. The calm-mode
# prompt asked:
#
#     "what am I settling into — what is becoming clear, or what am I
#      letting go?"
#
# which produced "settling into" and "letting go of any" verbatim. Both are
# now in _FILLER_RES, so leaving the prompt alone would have suppressed every
# calm-mode inner thought — the gate rejecting exactly what the prompt
# requested, on every quiet turn.

def _server_source() -> str:
    return (pathlib.Path(__file__).resolve().parent.parent / "server.py").read_text()


def test_no_inner_thought_prompt_requests_a_blacklisted_phrase():
    """
    Any prompt that asks for language the gate rejects guarantees silence.
    Checked against the real pattern list, so adding a filler pattern without
    checking the prompts fails here.
    """
    import re

    from runtime.inner_thought_quality import _FILLER_RES

    src = _server_source()
    # The inner-thought system prompts are the _it_sys assignments.
    prompts = re.findall(r"_it_sys = \(\s*(.*?)\n\s*\)", src, re.DOTALL)
    assert prompts, "no _it_sys prompt found — the block moved"

    for prompt in prompts:
        for rx in _FILLER_RES:
            assert not rx.search(prompt), (
                f"an inner-thought prompt asks for {rx.pattern!r}, which the "
                f"quality gate rejects — every such turn would be silent"
            )


def test_calm_mode_still_asks_for_something_specific():
    """Calm means slower and quieter, not content-free."""
    src = _server_source()
    i = src.index("I am eLo. This is my inner voice in a quiet moment.")
    block = src[i:i + 900]
    assert "specific" in block
    assert "about the conversation" in block
