"""
tests/test_learning_loop_leak.py — eLo was speaking his own telemetry.

Board P0, 2026-10-05, from David's live debug log. Two variants:

    eLo  {'id': 'L-20261005151905', 'lesson_key': '7d20ac65e9f2aa75',
          'statement': 'Partial progress on witness — ...', ...}

    eLo  Partial progress on reflect — check dependencies before next attempt.

The brief proposed four root causes: the lesson passed as a string to
elo_final, the learning pipeline writing to the response field, a stray str()
in output assembly, a debug statement feeding the buffer. It is none of them.
Nothing in learning/ touches the response.

The actual path, reproduced exactly:

    self/elo_self_state.json holds
        last_reflection_lesson = "Partial progress on reflect — check
                                  dependencies before next attempt."
        focal_thread           = ""          (fails the word floor)
    identity_guard._from_accumulated_state() returned the lesson,
    scrub_ai_leakage() emits that whenever a WHOLE response is scrubbed.

So the leak surfaces only on turns where the model produced pure AI-identity
leakage — which is why it looked intermittent and unrelated to learning.
"""
from __future__ import annotations

import pytest

import runtime.identity_guard as ig


class _State:
    def __init__(self, focal="", lesson="", read=""):
        self.focal_thread = focal
        self.last_reflection_lesson = lesson
        self.session_read = read


@pytest.fixture
def state(monkeypatch):
    holder = {}

    def _install(st):
        holder["st"] = st
        import self.elo_self_model as m
        monkeypatch.setattr(m, "load", lambda: st)

    return _install


# ── the leak ────────────────────────────────────────────────────────────────

LESSON = "Partial progress on reflect — check dependencies before next attempt."


def test_a_lesson_record_is_never_spoken(state):
    """The exact live value, with focal empty as it was."""
    state(_State(focal="", lesson=LESSON, read="steady presence"))
    assert ig._from_accumulated_state() == "", (
        "eLo is reading David his own Learning Loop telemetry"
    )


def test_a_whole_response_scrub_does_not_emit_the_lesson(state):
    state(_State(focal="", lesson=LESSON, read="steady presence"))
    out = ig.scrub_ai_leakage("I'm just an AI assistant without real feelings.")
    assert "Partial progress on" not in out
    assert "lesson_key" not in out


def test_the_dict_variant_is_not_spoken_either(state):
    dict_form = (
        "{'id': 'L-20261005151905', 'lesson_key': '7d20ac65e9f2aa75', "
        "'statement': 'Partial progress on witness — check dependencies.'}"
    )
    state(_State(focal="", lesson=dict_form, read=""))
    assert ig._from_accumulated_state() == ""


# ── what the function is still for ──────────────────────────────────────────

def test_real_accumulated_state_still_speaks(state):
    """
    The point of this function survives: a focal thread is a fragment of what
    actually passed between them, so it is still eLo's to say. Only the
    machine-written lesson is gone.
    """
    state(_State(focal="the seams pattern pieces", lesson=LESSON))
    assert ig._from_accumulated_state() == "the seams pattern pieces"


def test_session_read_still_speaks_when_long_enough(state):
    state(_State(focal="", lesson=LESSON, read="a steady kind of presence"))
    assert ig._from_accumulated_state() == "a steady kind of presence"


def test_nothing_accumulated_means_silence_not_invention(state):
    """
    The designed floor. server.py:7775 handles an empty response with a
    WARNING and a short truthful beat, so this is not eLo going mute.
    """
    state(_State(focal="", lesson=LESSON, read=""))
    assert ig._from_accumulated_state() == ""
