"""
tests/test_deferred_threads_chain.py — card 0006: the whole chain, not the
first link.

`fba4167` made eLo decide a thread was unfinished and write
`EloSelfState.open_threads`. That proved the WRITE. The card asks for the rest:

    question formed, not surfaced
      -> EloSelfState.open_threads            (fba4167, tested there)
      -> spine.py:1264 reads it
      -> temporal_state["has_deferred_threads"] = True
      -> executive_context:281 prefers "reflect" at 0.70

Every link existed before fba4167 except the first, which is why
has_deferred_threads had been False on every turn eLo has ever taken. A test
of the write alone would pass while the chain stayed dead — that is the
failure mode this whole codebase keeps producing, so the chain is asserted
end to end here.

spine.py and server.py are Builder 1's. They are exercised, never edited.
"""
from __future__ import annotations

import pytest

import faculties.curiosity.curiosity_faculty as cf
from faculties.metacognition import deferred_threads as dt


@pytest.fixture(autouse=True)
def _own_store(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "_QUESTIONS_PATH", str(tmp_path / "open_questions.json"))


def _q(text, *, surfaced=False, weight=6):
    return {"question_id": f"q-{text[:8]}", "topic": text.split()[-1],
            "text": text, "reason": "inner_thought", "confidence": 0.0,
            "weight": weight, "ts": 1.0, "surfaced": surfaced}


def _spine_reads(open_threads: list) -> dict:
    """
    spine.py:1264 verbatim in shape: read open_threads off the self-state,
    turn its truthiness into has_deferred_threads.
    """
    return {"circadian_phase": "active", "interaction_gap_hours": 0.1,
            "has_deferred_threads": bool(open_threads)}


def _exec_prefs(temporal: dict) -> dict:
    from runtime.executive_context import ExecutiveContext
    ec = ExecutiveContext()
    ec.temporal_state = temporal
    d = ec.as_dict() if hasattr(ec, "as_dict") else {}
    return dict((d.get("learning_advice") or {}).get("preferences") or {})


# ── link 1: a question not surfaced is an unfinished thread ────────────────

def test_an_unsurfaced_question_becomes_an_open_thread():
    cf.store_question(_q("I wonder how plotters function"))
    assert dt.current() == ["I wonder how plotters function"]


# ── link 2: spine turns it into the flag ───────────────────────────────────

def test_spine_reads_it_as_has_deferred_threads():
    cf.store_question(_q("I wonder how plotters function"))
    assert _spine_reads(dt.current())["has_deferred_threads"] is True


def test_nothing_deferred_leaves_the_flag_false():
    assert _spine_reads(dt.current())["has_deferred_threads"] is False


# ── link 3: the Executive prefers reflect ──────────────────────────────────

def test_the_reflect_preference_fires():
    """
    The end of the chain, and the reason any of it matters:
    executive_context:281 raises "reflect" to 0.70 when threads are open. It
    has never fired, because has_deferred_threads has never been True.
    """
    cf.store_question(_q("I wonder how plotters function"))
    prefs = _exec_prefs(_spine_reads(dt.current()))
    assert prefs.get("reflect", 0.0) >= 0.70, (
        f"reflect preference did not fire with an open thread: {prefs}"
    )


def test_no_open_thread_means_no_reflect_preference():
    """Causal: the ONLY difference between this and the test above."""
    prefs = _exec_prefs(_spine_reads(dt.current()))
    assert prefs.get("reflect", 0.0) < 0.70


def test_picking_the_thread_up_turns_the_flag_off_again():
    cf.store_question(_q("I wonder how plotters function"))
    assert _spine_reads(dt.current())["has_deferred_threads"] is True

    dt.mark_picked_up("I wonder how plotters function")
    assert _spine_reads(dt.current())["has_deferred_threads"] is False
    assert _exec_prefs(_spine_reads(dt.current())).get("reflect", 0.0) < 0.70


# ── the read path spine actually uses ──────────────────────────────────────

def test_spine_still_reads_the_field_this_writes():
    """
    If spine stops reading open_threads, the chain breaks silently and every
    test above still passes — they model spine rather than call it.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "runtime" / "spine" / "spine.py").read_text()
    assert 'getattr(_load_self_temp(), "open_threads"' in src
    assert '"has_deferred_threads": bool(_open_threads)' in src
