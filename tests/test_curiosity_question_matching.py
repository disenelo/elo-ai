"""
tests/test_curiosity_question_matching.py — the word that matters was the one that couldn't match.

IS ELO: — Curiosity & Exploration
    "a system capable of retaining unanswered questions?"
    "a system capable of returning to unanswered questions?"

The store holds 50 open questions and curiosity_questions_prompt_block()
returned "" for everything tried against it except the literal text of a
test row.

_match_curiosity_question() tokenises with `text.lower().split()` and no
punctuation stripping. A live question reads:

    whether 'challenge' is right here, or whether this situation differs
    from the one the lesson came from

Its tokens come out as "'challenge'" and "here," — so a turn saying
challenge cannot match the question ABOUT challenge. Measured:

    "situation lesson"      -> True     (both words sit alone)
    "challenge situation"   -> False    (quoted in the stored text)

The quoted word is the subject of the question. Quoting is exactly what
writers do to the term a question is about, so the most distinctive token
is systematically the unmatchable one.

SECOND, SEPARATE: 50 rows, 2 distinct questions. The block sorts oldest
first and takes [:2], so both slots can be the SAME question — eLo asking
himself one thing twice in a single prompt.
"""
from __future__ import annotations

import pytest

from faculties.learning.faculty import (
    _match_curiosity_question as match,
    curiosity_questions_prompt_block as block,
)

_Q = {"wants_to_know": "whether 'challenge' is right here, or whether this "
                       "situation differs from the one the lesson came from"}


# ── Punctuation must not hide a word ───────────────────────────────────────

def test_a_quoted_word_is_matchable():
    assert match(_Q, "challenge situation") is True


@pytest.mark.parametrize("stored,turn", [
    ("should I use 'build' or 'reflect' here", "build reflect"),
    ("does the servo, or the battery, matter", "servo battery"),
    ("is Blender (or Unity) better", "blender unity"),
    ("what about barkcloth; and canvas?", "barkcloth canvas"),
    ("the pattern. the seam.", "pattern seam"),
])
def test_punctuation_adjacent_words_still_match(stored, turn):
    assert match({"wants_to_know": stored}, turn) is True, (stored, turn)


def test_clean_words_still_match_as_before():
    assert match(_Q, "situation lesson") is True


# ── The threshold is not weakened ──────────────────────────────────────────

def test_one_overlapping_word_is_still_not_enough():
    """Two meaningful tokens was the bar and stays the bar."""
    assert match(_Q, "challenge") is False
    assert match(_Q, "lesson") is False


def test_stopwords_still_do_not_count():
    assert match(_Q, "whether this") is False
    assert match(_Q, "from here") is False


def test_short_words_still_do_not_count():
    assert match({"wants_to_know": "is it on or off"}, "on off") is False


def test_an_empty_turn_matches_nothing():
    assert match(_Q, "") is False


# ── One question, one slot ─────────────────────────────────────────────────

def test_the_same_question_is_not_surfaced_twice(tmp_path, monkeypatch):
    """
    50 stored rows, 2 distinct questions. Sorted oldest-first and sliced
    [:2], both slots could be the same text — eLo asking himself one thing
    twice in a single prompt.
    """
    import faculties.learning.faculty as lf
    dup = [{"_ts": i, "wants_to_know": "whether the seam allowance is right",
            "resolved": False} for i in range(5)]
    monkeypatch.setattr(lf, "_load_curiosity_questions", lambda: dup)
    out = block("seam allowance")
    assert out.count("whether the seam allowance is right") == 1, out


def test_two_different_questions_can_both_surface(tmp_path, monkeypatch):
    import faculties.learning.faculty as lf
    rows = [
        {"_ts": 1, "wants_to_know": "whether the seam allowance is right", "resolved": False},
        {"_ts": 2, "wants_to_know": "whether the seam fabric is right", "resolved": False},
    ]
    monkeypatch.setattr(lf, "_load_curiosity_questions", lambda: rows)
    out = block("seam right")
    assert out.count("[CURIOSITY") == 2, out


# ── Against the live store ─────────────────────────────────────────────────

def test_the_live_question_about_challenge_is_reachable():
    out = block("challenge situation")
    assert "challenge" in out.lower(), out or "EMPTY"
