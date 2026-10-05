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


# ── the surface guard ───────────────────────────────────────────────────────
#
# 851e3ae closed the source. This is the brief's second ask: a guard at the
# output boundary, so the next internal structure that reaches a response
# field does not reach David either.

from runtime.telemetry_guard import strip_internal_records as tg

LIVE_DICT = (
    "{'id': 'L-20261005151905', 'lesson_key': '7d20ac65e9f2aa75', "
    "'statement': 'Partial progress on witness — check dependencies before "
    "next attempt.', 'evidence': [], 'scope': 'behaviour'}"
)


def test_the_live_dict_is_suppressed_entirely():
    assert tg(LIVE_DICT) == ""


def test_no_scrap_of_the_record_survives():
    """
    Splitting on "." cuts a dict mid-structure and leaves fragments like "'}"
    that match nothing. The first version of this guard spoke that scrap.
    """
    out = tg(LIVE_DICT)
    for scrap in ("'}", "lesson_key", "L-2026", "behaviour"):
        assert scrap not in out


def test_a_record_embedded_in_speech_loses_only_itself():
    out = tg("I looked into it. Partial progress on reflect — check "
             "dependencies before next attempt. Anyway, it is fine.")
    assert out == "I looked into it. Anyway, it is fine."


# ── what must NOT be eaten ──────────────────────────────────────────────────
#
# eLo talks about code and JSON with David constantly. A guard that eats a
# snippet he was asked for is worse than the leak it prevents.

@pytest.mark.parametrize("line", [
    "I made partial progress on the seams today.",
    "Your lesson_key idea makes sense — store it next to the claim.",
    "That went well. Completed a big milestone today.",
    "When David meets an obstacle he usually sleeps on it.",
])
def test_ordinary_speech_survives(line):
    assert tg(line) == line


def test_a_fenced_code_block_is_never_touched():
    """Fenced code is eLo showing David something on purpose."""
    text = 'Here is the shape:\n```json\n{"lesson_key": "abc"}\n```\nthat is it.'
    assert tg(text) == text


# ── drift ratchet ───────────────────────────────────────────────────────────

def test_every_lesson_template_is_caught():
    """
    Generated from reflection_faculty._derive_statement itself, so changing
    the wording there fails HERE rather than silently reopening the leak.
    """
    from runtime.reflection_faculty import _derive_statement

    produced = [
        _derive_statement("summary", "reflect", "partial", "behaviour"),
        _derive_statement("summary", "build", "failed", "behaviour"),
        _derive_statement("a build summary", "build", "done", "behaviour"),
    ]
    produced = [p for p in produced if p]
    assert produced, "_derive_statement produced nothing — templates moved"

    for statement in produced:
        assert tg(statement) == "", (
            f"lesson template not caught by telemetry_guard: {statement!r}"
        )


def test_the_outbound_conditioner_runs_the_guard():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent / "server.py").read_text()
    i = src.index("def _condition_outbound")
    window = src[i:i + 2200]
    assert "from runtime.telemetry_guard import" in window
    for field in ('"response"', '"inner_thought"', '"bubbles"'):
        assert field in window, f"{field} not guarded"
