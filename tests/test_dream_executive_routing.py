"""
tests/test_dream_executive_routing.py — WO-DREAM-ENGINE-001 PHASE 8, final half.

"Executive decides what surfaces to waking cognition. Dream Faculty does not
speak directly."

A dream reaches waking cognition by PROPOSING, through
self.emergent_cognition.internal_intents() — which WO-INGRESS-32 makes the
sole proposer. No bypass is added. The Executive arbitrates as it already
does for every other intent.

Only a dream that cleared DREAM_RETENTION_THRESHOLD proposes. An unretained
dream stays in the journal and never reaches this path.
"""
from __future__ import annotations

import pytest

import faculties.dream.dream_faculty as df
from self.elo_self_model import EloSelfState
from self.emergent_cognition import internal_intents


def _state():
    st = EloSelfState()
    st.focal_thread = "the arm stops at the same angle"
    st.session_turns = 5
    st.inner_events = ["creative_spark"]
    return st


def _wake(retained: bool):
    st = _state()
    result = df.DreamResult(
        insight="the arm stalls at the same angle",
        journal_entry={"phase": "NREM+REM", "retained": retained},
    )
    df.wake_from_dream(result, st)
    return st


def _kinds(st, idle=1200.0):
    return [i["kind"] for i in internal_intents(st, idle_seconds=idle)]


# ── The retention gate decides whether anything surfaces ──────────────────────

def test_a_retained_dream_proposes():
    assert "dream_insight" in _kinds(_wake(True))


def test_an_unretained_dream_proposes_nothing():
    """Below the gate it stays in the journal. It does not reach the Executive."""
    assert "dream_insight" not in _kinds(_wake(False))


def test_the_marker_is_only_set_on_retention():
    assert "dream_insight" in _wake(True).inner_events
    assert "dream_insight" not in _wake(False).inner_events


def test_a_dream_with_no_journal_entry_does_not_propose():
    st = _state()
    df.wake_from_dream(df.DreamResult(insight="x"), st)
    assert "dream_insight" not in _kinds(st)


# ── It proposes; it does not decide ───────────────────────────────────────────

def test_the_proposal_is_advisory_like_every_other_intent():
    intents = internal_intents(_wake(True), idle_seconds=1200)
    dream = [i for i in intents if i["kind"] == "dream_insight"][0]
    assert dream["priority"] == "low"
    assert dream["source"] == "dream_review"
    assert set(dream) == {"kind", "priority", "salience", "source", "trigger"}


def test_it_does_not_crowd_out_the_other_proposers():
    """The dream joins the intent list; it does not replace it."""
    kinds = _kinds(_wake(True))
    assert "exploration" in kinds
    assert len(kinds) > 1


def test_no_bypass_was_added_to_the_faculty():
    """
    internal_intents is the sole proposer (WO-INGRESS-32). The dream faculty
    and the review must still have no way to address David directly.
    """
    from faculties.dream import dream_review as dr
    for forbidden in ("speak", "emit", "say", "surface"):
        assert not hasattr(dr, forbidden)
        assert not hasattr(df, forbidden)


def test_the_review_still_declares_it_does_not_surface_directly():
    from faculties.dream import dream_review as dr
    payload = dr.review({"dream_id": "d1", "insight": "x"}).for_executive()
    assert payload["surfaces_directly"] is False


# ── The proposer's own rules still hold ───────────────────────────────────────

def test_a_bare_state_still_proposes_nothing():
    """'Returns [] for an empty/bare state — no fabricated urgency.'"""
    bare = EloSelfState()
    bare.inner_events = []
    bare.focal_thread = ""
    bare.lifetime_threads = []
    assert internal_intents(bare, idle_seconds=99999) == []


def test_the_marker_alone_is_not_enough_without_the_insight():
    """A stale marker with no dream read must not fire a proposal."""
    st = _wake(True)
    st.session_read = "something else entirely"
    assert "dream_insight" not in _kinds(st)


def test_the_marker_ages_out_of_the_event_window():
    st = _wake(True)
    st.inner_events = list(st.inner_events) + ["a", "b", "c", "d", "e", "f", "g", "h"]
    assert "dream_insight" not in _kinds(st)


# ── Existing wake behaviour preserved ─────────────────────────────────────────

def test_wake_still_does_everything_it_did_before():
    """Assert the deltas, not absolutes — the state defaults are not mine."""
    before = _state()
    c0, m0 = before.curiosity, before.mood
    st = _wake(True)
    assert "connection" in st.inner_events
    assert st.session_read.startswith("woke from dream")
    assert st.curiosity == pytest.approx(min(1.0, c0 + 0.12), abs=1e-6)
    assert st.mood == pytest.approx(min(1.0, m0 + 0.08), abs=1e-6)


# ── Salience: the dream can actually win, and does not bypass ─────────────────
# server.py used to take _intents[0], so precedence was the order the
# proposers happen to be written in. A dream needs >= 600s idle, so
# `exploration` (>= 300s) was always ahead of it — the retained insight was
# proposed and silently discarded every time. It never reached the Executive.

from self import emergent_cognition as ec


def _top(st):
    intents = internal_intents(st, idle_seconds=1200)
    return max(intents, key=lambda i: float(i.get("salience", 0.0)))


def test_every_intent_carries_a_salience():
    for intent in internal_intents(_wake(True), idle_seconds=1200):
        assert isinstance(intent.get("salience"), float)


def test_a_retained_dream_wins_selection():
    assert _top(_wake(True))["kind"] == "dream_insight"


def test_without_a_retained_dream_nothing_changes():
    """Behaviour-preserving for the existing intents."""
    assert _top(_wake(False))["kind"] == "exploration"


def test_existing_relative_order_is_preserved():
    """Defaults descend in the previous list order."""
    assert (ec._SALIENCE_EXPLORATION
            > ec._SALIENCE_RETURN_THREAD
            > ec._SALIENCE_MICRO_GOAL)


def test_the_dream_competes_rather_than_bypasses():
    """
    It wins on a comparable axis, not by skipping the contest. Its margin
    over routine idle curiosity is small and it is still 'low' priority.
    """
    dream = [i for i in internal_intents(_wake(True), idle_seconds=1200)
             if i["kind"] == "dream_insight"][0]
    assert dream["priority"] == "low"
    assert ec._SALIENCE_DREAM_INSIGHT > ec._SALIENCE_EXPLORATION
    assert ec._SALIENCE_DREAM_INSIGHT - ec._SALIENCE_EXPLORATION <= 0.25
    assert ec._SALIENCE_DREAM_INSIGHT < 1.0


def test_server_selects_by_salience_not_list_position():
    from pathlib import Path
    src = Path(__file__).resolve().parent.parent / "server.py"
    text = src.read_text(encoding="utf-8")
    assert "_top_intent: dict = dict(_intents[0])" not in text, (
        "server.py still takes the first intent — a dream can never win"
    )
    assert 'max(_intents, key=lambda i: float(i.get("salience", 0.0)))' in text


def test_an_unknown_intent_without_salience_still_selects():
    """A proposer that predates salience must not break selection."""
    intents = [{"kind": "legacy", "priority": "low"},
               {"kind": "dream_insight", "priority": "low", "salience": 0.75}]
    assert max(intents, key=lambda i: float(i.get("salience", 0.0)))["kind"] == "dream_insight"
