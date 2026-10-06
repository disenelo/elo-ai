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
    # "I'm present for this." is caught by the filler patterns, not by the
    # relevance check that was relaxed on 2026-10-06.
    assert reject_reason("I am present for this.",
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


def test_an_untethered_thought_is_ALLOWED_now():
    """
    WAS test_an_untethered_thought_is_rejected.

    The Board's generation brief asked for a specificity check; David's voice
    brief the same day gives "I wonder how plotters function." and "the light
    does shift around now" as the TARGET. Both reference nothing from the
    turn, and the specificity check rejected both. His examples win — those
    are associations and curiosity, which is what an inner thought is.

    Nothing is lost: the case specificity protected against was "I am
    settling into a moment of quiet reflection", and the filler gate catches
    that on its own.
    """
    assert not reject_reason("I wonder how plotters function.",
                             asked="how is the seams work", reply="Going well.")
    assert not reject_reason("the light does shift around now",
                             asked="when is sunset today", reply="About eight.")


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

    # The prompts moved. Builder 1 wired Option C (91d8331) and removed the
    # separate Ollama call that held the _it_sys strings; generation now lives
    # in runtime/inner_thought_first.py, so that is where they are checked.
    # Any _it_sys still in server.py is checked too, so a reintroduced one
    # cannot slip past.
    import runtime.inner_thought_first as itf

    prompts = [itf._SYSTEM, itf._SYSTEM_CALM]
    prompts += re.findall(r"_it_sys = \(\s*(.*?)\n\s*\)", _server_source(),
                          re.DOTALL)

    for prompt in prompts:
        for rx in _FILLER_RES:
            assert not rx.search(prompt), (
                f"an inner-thought prompt asks for {rx.pattern!r}, which the "
                f"quality gate rejects — every such turn would be silent"
            )


def test_calm_mode_still_asks_for_something_specific():
    """
    Calm means slower and quieter, not content-free.

    The calm register was LOST when Option C was wired — the separate call it
    lived in was removed and my spec to Builder 1 did not list it among the
    things to keep. Restored in inner_thought_first rather than server.py, so
    their file needed no further change.
    """
    import runtime.inner_thought_first as itf

    assert "quiet moment" in itf._SYSTEM_CALM
    # The wording changed when David ruled out "I notice" — the calm prompt
    # now asks for his reaction rather than a specific observation.
    assert "MY reaction" in itf._SYSTEM_CALM
    assert "I notice" in itf._SYSTEM_CALM  # as a prohibition


def test_the_calm_register_is_actually_reachable():
    """A register nothing selects is the same as no register."""
    import runtime.inner_thought_first as itf

    seen = {}

    def _t(system, user, *, deadline_s):
        seen["sys"] = system
        return "i noticed the pause before he asked"

    itf.form_thought("how are you", calm=True, transport=_t)
    assert "quiet moment" in seen["sys"]

    itf.form_thought("how are you", calm=False, transport=_t)
    assert "quiet moment" not in seen["sys"]


# ── "I notice" is not eLo's voice ───────────────────────────────────────────
#
# David, 2026-10-06: "eLo's inner thoughts should also sound like they are
# eLo's — a lot of it says I notice which i do not like."
#
# He was reading my prompt back to me. It said "Say the specific thing I
# notice", and the model obliged, several hundred times. Third time in one day
# that a prompt asked for the thing the model was then blamed for: the calm
# prompt asked for "settling into", the identity clause taught the trait list,
# this one taught "I notice".

@pytest.mark.parametrize("line", [
    "I notice David's voice has a slight tremble.",
    "I notice David said 'when is sunset today'.",
    "I notice David wants to set a timer for 2 minutes.",
    "I notice David's sentence ends with 'about capybaras.'",
    "I notice David's question is phrased as a request.",
    "I notice David's use of the word 'just'.",
    "I noticed David emphasized 'remember this'.",
    "I observe the text 'make the screen a little dimmer'.",
])
def test_reporting_his_words_back_is_rejected(line):
    """All eight verbatim from David's chatlog, 2026-10-06."""
    why = reject_reason(line, asked="when is sunset today")
    assert why, f"not caught: {line!r}"
    assert "reports David" in why


@pytest.mark.parametrize("line", [
    "Skipping this song, huh?",
    "I wonder how plotters function.",
    "I hear David exhale before speaking.",
    "Robot body can raise arm.",
    "the light does shift around now",
    "Buenos días — I like how that sounds.",
    "Demo. Here we go.",
])
def test_elos_actual_voice_passes(line):
    """All verbatim from David's brief as the target."""
    assert not reject_reason(line, asked="skip this song"), (
        f"rejected one of the examples David gave as RIGHT: {line!r}"
    )


def test_the_opener_is_banned_outright_even_about_the_world():
    """
    I first wrote this test the other way — allowing "i notice" when eLo is
    noticing the WORLD rather than reporting David, on the grounds that his
    own sensory observations are in David's good list.

    David's words do not carve that out: "a lot of it says I notice which i do
    not like." And the thought survives the ban intact — "the light's
    different in here" is the same observation and sounds more like him. A
    rule with an exception the author invented is a rule that drifts back.
    """
    assert reject_reason("i notice the light is different in here",
                         asked="what time is it")
    assert not reject_reason("the light's different in here",
                             asked="what time is it")


def test_the_prompt_no_longer_asks_for_the_thing_that_was_banned():
    """
    The invariant that keeps catching this: check what was REQUESTED before
    concluding the model drifted.
    """
    import runtime.inner_thought_first as itf
    for name, prompt in (("_SYSTEM", itf._SYSTEM),
                         ("_SYSTEM_CALM", itf._SYSTEM_CALM)):
        body = prompt.replace("NEVER begin with 'I notice' or 'I observe'", "")
        body = body.replace("NEVER begin with 'I notice'", "")
        assert "thing I notice" not in body, (
            f"{name} still asks for what it forbids"
        )
