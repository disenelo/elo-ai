"""
tests/test_open_question_capture.py — eLo keeps the questions he forms.

Builder 2 brief, three NO verdicts in a row:

    recognising unanswered questions?  NO
    retaining unanswered questions?    NO
    returning to unanswered questions? NO
    "No unanswered_questions store."

Half of that is wrong, and it is the useful half. The store exists —
faculties/curiosity keeps self/state/open_questions.json, and server.py:5571
already READS it to surface a question back to David.

Measured 2026-10-06: the file held 0 questions, and nothing in production
called store_question() or detect_gap(). The read side was wired; the write
side never was. eLo could surface a question he was never able to keep.
"""
from __future__ import annotations

import json

import pytest

import faculties.curiosity.curiosity_faculty as cf
from faculties.metacognition import open_question_capture as oqc


@pytest.fixture(autouse=True)
def _own_store(tmp_path, monkeypatch):
    """Never eLo's real question queue."""
    monkeypatch.setattr(cf, "_QUESTIONS_PATH", str(tmp_path / "open_questions.json"))


def _stored():
    try:
        with open(cf._QUESTIONS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ── recognising ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("thought", [
    "I wonder how plotters function.",
    "Skipping this song, huh?",
    "Drift?",
    "why does the light shift around now",
    "no idea what a capybara sounds like",
])
def test_a_wondering_is_recognised(thought):
    assert oqc.is_wondering(thought), thought


@pytest.mark.parametrize("thought", [
    "need calendar.",
    "buenos días",
    "the light's different in here",
    "Demo. Here we go.",
])
def test_a_statement_is_not_a_question(thought):
    assert not oqc.is_wondering(thought), thought


# ── retaining ───────────────────────────────────────────────────────────────

def test_a_wondering_is_kept():
    rec = oqc.capture("I wonder how plotters function.",
                      asked="what is a plotter")
    assert rec is not None
    held = _stored()
    assert len(held) == 1
    assert held[0]["text"] == "I wonder how plotters function."
    assert held[0]["reason"] == "inner_thought"


def test_a_statement_leaves_nothing_behind():
    assert oqc.capture("need calendar.") is None
    assert _stored() == []


def test_the_turn_that_raised_it_is_kept_with_it():
    """'Returning to it' is weaker without knowing what prompted it."""
    oqc.capture("I wonder how plotters function.", asked="what is a plotter")
    assert _stored()[0]["asked"] == "what is a plotter"


def test_the_same_wondering_twice_is_one_question():
    """curiosity_faculty dedupes by topic, so the topic must be stable."""
    oqc.capture("I wonder how plotters function.")
    oqc.capture("I wonder how plotters function.")
    assert len(_stored()) == 1


def test_a_question_with_no_subject_is_not_stored():
    assert oqc.capture("why?") is None


# ── returning ───────────────────────────────────────────────────────────────

def test_a_kept_question_comes_back_through_the_existing_path():
    """
    The whole point of not building a second store: top_question() and the
    server read that uses it already work. Storing closes the loop.
    """
    oqc.capture("I wonder how plotters function.")
    top = cf.top_question()
    assert top is not None
    assert top["text"] == "I wonder how plotters function."


def test_a_surfaced_question_does_not_return_forever():
    oqc.capture("I wonder how plotters function.")
    cf.mark_surfaced("I wonder how plotters function.")
    assert cf.top_question() is None


# ── it never costs a turn ───────────────────────────────────────────────────

def test_a_failing_store_is_absorbed(monkeypatch):
    def _boom(q):
        raise RuntimeError("disk full")
    monkeypatch.setattr(cf, "store_question", _boom)
    assert oqc.capture("I wonder how plotters function.") is None


def test_the_generator_captures_without_a_second_store():
    """
    One behaviour with two stores is the mistake this codebase keeps making.
    The capture must go through curiosity_faculty, not beside it.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "faculties" / "metacognition" / "open_question_capture.py").read_text()
    assert "from faculties.curiosity.curiosity_faculty import store_question" in src
    assert "open_questions.json" not in src.split('"""', 2)[-1], (
        "a second path to the file would bypass dedupe, prioritisation and cap"
    )


def test_form_thought_captures_what_it_produced():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "runtime" / "inner_thought_first.py").read_text()
    assert "open_question_capture import capture" in src
    gate = src.index("reject_reason")
    cap = src.index("open_question_capture import capture")
    assert gate < cap, "a rejected thought must not leave a question behind"
