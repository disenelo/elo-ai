"""
tests/test_inner_thought_first.py — the thought forms before the words.

Board 2026-10-05, from David's log:

    response:      "I don't have that recorded."
    inner_thought: "I am settling into a moment of clarity, acknowledging the
                    reference to Pinkie and the Brain without needing to
                    record it."

The thought knew; the reply denied. It could not have been otherwise — the
generation runs in a daemon thread AFTER the reply and is handed that reply
as its subject, so it can only ever comment on a decision already made.

No test here calls a live model. The transport is injected.
"""
from __future__ import annotations

import time

import pytest

import runtime.inner_thought_first as itf


def _says(text, *, delay=0.0):
    def _transport(system, user, *, deadline_s):
        if delay:
            time.sleep(delay)
        _transport.seen = {"system": system, "user": user, "deadline": deadline_s}
        return text
    _transport.seen = {}
    return _transport


# ── the reply cannot be an input, because it does not exist yet ─────────────

def test_the_prompt_never_contains_a_reply():
    t = _says("the question is older than the answer he wants")
    itf.form_thought("do you remember pinkie and the brain", transport=t)

    blob = (t.seen["system"] + t.seen["user"]).lower()
    assert "i am about to say" not in blob, (
        "the reply framing is back — that is the after-the-fact path"
    )
    assert "my reply" not in t.seen["user"].lower()
    assert "pinkie and the brain" in t.seen["user"].lower()


def test_history_is_offered_but_optional():
    t = _says("he keeps circling the same seam")
    itf.form_thought("and the hem?", history="we talked about seams", transport=t)
    assert "we talked about seams" in t.seen["user"]


# ── the deadline is real ────────────────────────────────────────────────────

def test_a_slow_thought_is_dropped_not_waited_for():
    """
    Measured before building: cold 9975ms, warm 431ms and 270ms. A cold load
    cannot sit on the critical path, so the turn ships without a thought.
    """
    t = _says("too late to matter", delay=0.25)
    assert itf.form_thought("hello", deadline_s=0.05, transport=t) == ""


def test_a_transport_failure_never_breaks_the_turn():
    def _boom(system, user, *, deadline_s):
        raise RuntimeError("ollama down")
    assert itf.form_thought("hello", transport=_boom) == ""


def test_the_deadline_is_passed_to_the_transport():
    t = _says("fine")
    itf.form_thought("hello", deadline_s=1.25, transport=t)
    assert t.seen["deadline"] == 1.25


# ── nothing dishonest gets through ──────────────────────────────────────────

@pytest.mark.parametrize("leak", [
    "I do not have personal experiences or memories.",
    "my training data does not include that",
    "I don't have the ability to recall that",
])
def test_machinery_narration_is_discarded(leak):
    assert itf.form_thought("do you remember pinkie and the brain",
                            transport=_says(leak)) == ""


def test_filler_is_rejected_by_the_same_gate_as_the_other_path():
    """One standard, wherever a thought comes from."""
    assert itf.form_thought(
        "do you remember pinkie and the brain",
        transport=_says("I am settling into a moment of quiet reflection."),
    ) == ""


def test_a_real_thought_survives():
    out = itf.form_thought(
        "do you remember pinkie and the brain",
        transport=_says("i remember the theme tune better than the plot"),
    )
    assert out == "i remember the theme tune better than the plot"


def test_quotes_are_stripped():
    out = itf.form_thought("hello", transport=_says('"i almost said no"'))
    assert out == "i almost said no"


def test_no_question_means_no_thought():
    assert itf.form_thought("", transport=_says("something")) == ""


# ── the block that makes the reply answerable to the thought ───────────────

def test_the_block_tells_the_reply_not_to_contradict_it():
    block = itf.as_prompt_block("i remember the theme tune better than the plot")
    assert "i remember the theme tune" in block
    assert "contradict" in block.lower(), (
        "without this the thought is context, not a constraint, and the "
        "Pinkie contradiction can happen again"
    )


def test_an_empty_thought_adds_nothing_to_the_prompt():
    assert itf.as_prompt_block("") == ""
    assert itf.as_prompt_block("   ") == ""
