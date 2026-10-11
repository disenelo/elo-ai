"""
tests/test_0006_open_threads_wire.py — card 0006, OPEN-THREADS-WIRE.

`has_deferred_threads` was False on every turn eLo had ever taken. Three
separate things had to be true for the reflect preference to fire, and the
card is to prove the whole chain, not one link:

    a question formed and not surfaced
      -> EloSelfState.open_threads is non-empty
        -> spine.py:1289 sets has_deferred_threads = bool(open_threads)
          -> executive_context:286 raises the "reflect" preference to 0.70

The middle link is read from spine's source rather than executed: spine.py is
Builder 1's and running a turn here would need the whole stack. Said plainly
rather than claimed as an end-to-end run.

Isolated from the live self-state throughout. A test that reads David's real
open_threads passes or fails on what he happened to be doing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runtime.executive_context import build_executive_context  # noqa: E402


def _ctx(deferred: bool, gap_h: float = 0.5) -> dict:
    ec = build_executive_context(
        intent="conversation", emotional_context={}, world=None,
        working_memory=None, capabilities=[], cognitive_state=None,
        affordances=None, attention={},
        temporal={"circadian_phase": "active",
                  "interaction_gap_hours": gap_h,
                  "has_deferred_threads": deferred},
    )
    return ec.as_dict()


def _prefs(deferred: bool, gap_h: float = 0.5) -> dict:
    return (_ctx(deferred, gap_h).get("learning_advice") or {}).get("preferences") or {}


# ── the link the card exists for ─────────────────────────────────────────────

def test_an_unfinished_thread_raises_the_reflect_preference():
    assert _prefs(True).get("reflect") == 0.70


def test_no_unfinished_thread_leaves_reflect_alone():
    """
    The other half. A preference that is always set is not a preference --
    this is what makes the one above mean something.
    """
    assert _prefs(False).get("reflect") is None


def test_the_temporal_state_reaches_the_context():
    state = _ctx(True).get("ec_temporal_state") or {}
    assert state.get("has_deferred_threads") is True


# ── the link above it, read from spine's source (Builder 1's file) ───────────

def test_spine_derives_the_flag_from_open_threads():
    """
    spine.py:1289 must set has_deferred_threads from open_threads, not from a
    constant. Asserted against source because spine is Builder 1's and a real
    turn needs the whole stack — the limitation is the point of this comment.
    """
    src = (ROOT / "runtime" / "spine" / "spine.py").read_text(encoding="utf-8", errors="replace")
    assert '"has_deferred_threads": bool(_open_threads)' in src, \
        "spine no longer derives has_deferred_threads from open_threads"
    assert "open_threads" in src.split('"has_deferred_threads"')[0][-800:], \
        "spine does not read open_threads near the flag it sets"


# ── the link below it: a stored, unsurfaced question is an open thread ───────

def test_an_unsurfaced_question_becomes_an_open_thread(monkeypatch):
    """
    Card 0006 step 1: open_threads is populated by the question-formed-but-
    not-surfaced logic, not only by restore() replaying an always-empty
    payload — which is why has_deferred_threads was False on every turn eLo
    had ever taken.

    Patches curiosity_faculty._load_questions, the source _unsurfaced() reads,
    so this never touches David's live questions.
    """
    from faculties.metacognition import deferred_threads as dt

    monkeypatch.setattr(
        "faculties.curiosity.curiosity_faculty._load_questions",
        lambda: [
            {"text": "does the seam hold?", "topic": "seam",
             "surfaced": False, "weight": 5},
            {"text": "already said out loud", "topic": "x",
             "surfaced": True, "weight": 9},
        ])

    threads = dt.current()
    assert any("seam" in t for t in threads), threads
    assert not any("already said" in t for t in threads), \
        "a surfaced question is finished, not deferred"


def test_a_thread_that_was_picked_up_stops_counting(monkeypatch):
    """Otherwise every answered question would keep preferring reflect forever."""
    from faculties.metacognition import deferred_threads as dt
    monkeypatch.setattr(
        "faculties.curiosity.curiosity_faculty._load_questions",
        lambda: [{"text": "q", "topic": "t", "surfaced": True, "weight": 5}])
    assert dt.current() == []
    assert _prefs(bool(dt.current())).get("reflect") is None


def test_threads_are_capped_so_the_phrase_keeps_meaning_something(monkeypatch):
    from faculties.metacognition import deferred_threads as dt
    monkeypatch.setattr(
        "faculties.curiosity.curiosity_faculty._load_questions",
        lambda: [{"text": f"question {i}", "topic": "t", "surfaced": False,
                  "weight": 5} for i in range(20)])
    assert len(dt.current()) <= dt.MAX_THREADS
