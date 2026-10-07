"""
tests/test_deferred_threads.py — something set down is not something dropped.

Builder 2 brief:

    capable of deferring something without losing it?  NO  "No deferral store."
    capable of recovering unfinished thoughts?         NO  "No deferred_threads
                                                            store — your WO."

There are TWO deferral stores and neither has ever held anything:

    EloSelfState.open_threads            read by spine.py:1264, value []
    conversation_tracker._open_threads   filled only by restore()

spine turns the first into has_deferred_threads and executive_context:281
uses it to prefer "reflect" — pick up the open thread. It has been False on
every turn eLo has ever taken. The tracker's store is worse: open_thread() is
called from exactly one place, restore(), replaying a payload whose
open_threads is always empty. A closed loop on nothing.

So the gap was never storage. Nothing ever DECIDED a thread was unfinished.
"""
from __future__ import annotations

import json

import pytest

import faculties.curiosity.curiosity_faculty as cf
from faculties.metacognition import deferred_threads as dt


@pytest.fixture(autouse=True)
def _own_store(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "_QUESTIONS_PATH", str(tmp_path / "open_questions.json"))


def _q(text, *, weight=5, surfaced=False):
    return {"question_id": f"q-{text[:6]}", "topic": text.split()[-1],
            "text": text, "reason": "inner_thought", "confidence": 0.0,
            "weight": weight, "ts": 1.0, "surfaced": surfaced}


# ── deciding something is unfinished ───────────────────────────────────────

def test_an_unsurfaced_question_is_a_deferred_thread():
    cf.store_question(_q("I wonder how plotters function"))
    assert dt.current() == ["I wonder how plotters function"]


def test_a_surfaced_question_is_not_deferred():
    """Picked up is not set down."""
    cf.store_question(_q("already asked this one", surfaced=True))
    assert dt.current() == []


def test_nothing_deferred_is_an_honest_empty():
    """Empty means nothing was set down, not that deferral is broken."""
    assert dt.current() == []


def test_the_most_significant_thread_leads():
    cf.store_question(_q("minor wondering about hems", weight=2))
    cf.store_question(_q("the robot shell question", weight=9))
    assert dt.current()[0] == "the robot shell question"


def test_the_list_stays_short_enough_to_mean_something():
    for i in range(12):
        cf.store_question(_q(f"question number {i} about topic{i}", weight=i))
    assert len(dt.current()) == dt.MAX_THREADS


# ── reaching the field that makes the Executive act ────────────────────────

def test_it_writes_the_field_spine_actually_reads(monkeypatch):
    """
    spine.py:1264 reads EloSelfState.open_threads and nothing has ever
    written it. This is the first link in a chain that was otherwise complete.
    """
    written = {}

    class _State:
        open_threads: list = []

    import self.elo_self_model as m

    def _update(fn):
        st = _State()
        fn(st)
        written["open_threads"] = st.open_threads
        return st

    monkeypatch.setattr(m, "update", _update)

    cf.store_question(_q("I wonder how plotters function"))
    out = dt.sync_to_self_state()

    assert out == ["I wonder how plotters function"]
    assert written["open_threads"] == out


def test_a_failing_write_never_costs_the_tick(monkeypatch):
    import self.elo_self_model as m

    def _boom(fn):
        raise RuntimeError("state unavailable")
    monkeypatch.setattr(m, "update", _boom)

    cf.store_question(_q("I wonder how plotters function"))
    assert dt.sync_to_self_state() == []


# ── picking one back up ────────────────────────────────────────────────────

def test_a_thread_picked_up_stops_being_deferred():
    cf.store_question(_q("I wonder how plotters function"))
    assert dt.mark_picked_up("I wonder how plotters function") is True
    assert dt.current() == []


def test_picking_up_goes_through_the_store_that_owns_it():
    """
    One question must not be open in curiosity and closed here. mark_surfaced
    is curiosity_faculty's own call.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "faculties" / "metacognition" / "deferred_threads.py").read_text()
    assert "from faculties.curiosity.curiosity_faculty import" in src
    assert "mark_surfaced" in src


def test_an_unknown_thread_is_not_silently_marked():
    assert dt.mark_picked_up("never existed") is False
    assert dt.mark_picked_up("") is False


# ── no third store ─────────────────────────────────────────────────────────

def test_it_does_not_invent_another_store():
    """Two empty stores are the problem; a third is the same mistake."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "faculties" / "metacognition" / "deferred_threads.py").read_text()
    body = src.split('"""', 2)[-1]
    assert "open(" not in body and "json.dump" not in body, (
        "deferred_threads is writing a file of its own"
    )


def test_the_ambient_tick_syncs_it():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "ambient" / "ambient_engine.py").read_text()
    assert "deferred_threads import sync_to_self_state" in src
