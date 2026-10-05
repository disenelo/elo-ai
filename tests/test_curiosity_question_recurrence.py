"""
tests/test_curiosity_question_recurrence.py — 50 rows, 2 questions.

"a system capable of retaining unanswered questions?"
"a system capable of noticing repeated signals?"

_persist_curiosity_question() appended a full record every time, so the
live store holds 50 rows carrying 2 distinct questions. 48 of them are
byte-identical repeats of something already open.

Two things wrong, and they pull in opposite directions:
  - the store grows a full record per repeat
  - the repetition is REAL SIGNAL and must not be thrown away. eLo asking
    himself the same thing 49 times is the strongest evidence that it
    matters, exactly the way claim recurrence turned out to be the only
    discriminating input for SPG significance.

So dedupe does not mean discard. A repeat appends a compact re-ask marker
instead of a full duplicate, the open-question read counts them into
times_asked, and the prompt block says so. Append-only and the resolution
tombstones are untouched.

A count that nothing reads would be write-only data — the defect this
stack keeps finding — so it reaches the prompt.
"""
from __future__ import annotations

import json

import pytest

import faculties.learning.faculty as lf


@pytest.fixture
def _store(tmp_path, monkeypatch):
    p = tmp_path / "curiosity_questions.jsonl"
    monkeypatch.setattr(lf, "_CURIOSITY_Q_PATH", str(p))
    return p


class _Advice:
    def __init__(self, q):
        self.wants_to_know = q
        self.fit = "fits"
        self.confidence = 0.5
        self.curiosity = 0.6
        self.lesson_ids = []


def _rows(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


# ── A repeat does not duplicate the record ─────────────────────────────────

def test_asking_the_same_thing_twice_writes_one_full_record(_store):
    for _ in range(5):
        lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    full = [r for r in _rows(_store) if r.get("wants_to_know")]
    assert len(full) == 1, full


def test_a_different_question_gets_its_own_record(_store):
    lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    lf._persist_curiosity_question(_Advice("whether the canvas weight is right"))
    assert len([r for r in _rows(_store) if r.get("wants_to_know")]) == 2


# ── The repetition is kept, not discarded ──────────────────────────────────

def test_the_repeats_are_still_counted(_store):
    for _ in range(5):
        lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    q = lf._open_curiosity_questions(lf._load_curiosity_questions())[0]
    assert q["times_asked"] == 5, q


def test_asked_once_counts_once(_store):
    lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    q = lf._open_curiosity_questions(lf._load_curiosity_questions())[0]
    assert q["times_asked"] == 1


def test_the_count_reaches_the_prompt(_store):
    """A count nothing reads would be write-only data."""
    for _ in range(4):
        lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    out = lf.curiosity_questions_prompt_block("seam allowance")
    assert "4" in out, out


def test_a_single_asking_does_not_announce_a_count(_store):
    lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    out = lf.curiosity_questions_prompt_block("seam allowance")
    assert out and "times" not in out.lower(), out


# ── Resolution still works ─────────────────────────────────────────────────

def test_resolving_closes_a_repeated_question(_store):
    for _ in range(3):
        lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    lf.resolve_curiosity_question("whether the seam allowance is right")
    assert lf._open_curiosity_questions(lf._load_curiosity_questions()) == []


def test_a_question_asked_again_after_resolution_reopens(_store):
    lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    lf.resolve_curiosity_question("whether the seam allowance is right")
    lf._persist_curiosity_question(_Advice("whether the seam allowance is right"))
    open_qs = lf._open_curiosity_questions(lf._load_curiosity_questions())
    assert len(open_qs) == 1, "a resolved question asked again must come back"


# ── The existing store still reads ─────────────────────────────────────────

def test_legacy_rows_without_a_count_still_work():
    """The 50 live rows predate times_asked and must not break."""
    rows = lf._open_curiosity_questions(lf._load_curiosity_questions())
    assert all(isinstance(q.get("times_asked", 1), int) for q in rows)
