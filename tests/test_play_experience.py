"""
tests/test_play_experience.py — card 0009: what eLo does for fun is
experience, not telemetry.

Presence fires `water_play` and `auto_action` when eLo dives, leaps,
wall-jumps or stomps of his own accord. Board verified 2026-10-08: **zero
consumers** — no grep hits for water_play or auto_action in server.py,
spine.py or ambient_engine. The events were sent and discarded, so none of it
had ever reached WKG, SPG, or anything that shapes a later turn.
"""
from __future__ import annotations

import json

import pytest

import memory.spg_graph as spgg
import runtime.wkg_faculty as wkg
from core import play_experience as px


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Never the live cursor, never the live WKG."""
    monkeypatch.setattr(px, "CURSOR_PATH", str(tmp_path / "play_cursor.json"))

    wkg_dir = tmp_path / "wkg"
    wkg_dir.mkdir()
    import os
    import shutil
    src = os.path.join(os.path.dirname(wkg.__file__), "..", "memory", "wkg")
    for vocab in ("relationship_types.json", "entity_types.json"):
        p = os.path.join(src, vocab)
        if os.path.exists(p):
            shutil.copy2(p, wkg_dir / vocab)
    for data in ("claims.json", "entities.json", "sources.json"):
        (wkg_dir / data).write_text(json.dumps([]))
    monkeypatch.setattr(wkg, "_WKG_DIR", str(wkg_dir))
    monkeypatch.setattr(wkg, "_link_claim_to_spg", lambda c: None)
    monkeypatch.setattr(spgg, "_GRAPH_PATH", tmp_path / "spg_graph.json")


def _fun(subject="dive", seq=1):
    return {"seq": seq, "type": "water_play", "subject": subject,
            "payload": {"fun": True}, "_ts": 1791000000.0}


def _auto(subject="stomp", seq=2):
    return {"seq": seq, "type": "auto_action", "subject": subject,
            "payload": {"issued_by": "timer"}, "_ts": 1791000001.0}


# ── the two kinds are different facts about him ────────────────────────────

def test_fun_and_self_initiated_are_not_flattened():
    """
    A record that says the same thing for both cannot answer "what does he do
    when nobody asks" — which is the more interesting of the two.
    """
    assert px.describe(_fun("dive")) == "eLo had fun — dive"
    assert px.describe(_auto("stomp")) == "eLo chose stomp for himself"


def test_choosing_something_outranks_enjoying_it():
    assert px.SIGNIFICANCE[px.AUTO_ACTION] > px.SIGNIFICANCE[px.WATER_PLAY]


def test_self_initiation_is_marked_on_the_record():
    assert px.record(_auto(), apply=False)["self_initiated"] is True
    assert px.record(_fun(), apply=False)["self_initiated"] is False


# ── only the Designer's subjects ───────────────────────────────────────────

@pytest.mark.parametrize("subj", sorted(px.FUN_SUBJECTS))
def test_every_relayed_fun_subject_is_accepted(subj):
    assert px.is_play(_fun(subj))


@pytest.mark.parametrize("subj", sorted(px.SELF_SUBJECTS))
def test_every_relayed_auto_subject_is_accepted(subj):
    assert px.is_play(_auto(subj))


def test_an_unlisted_subject_is_ignored_not_guessed():
    assert not px.is_play(_fun("backflip"))


def test_an_unrelated_event_is_ignored():
    assert not px.is_play({"seq": 9, "type": "gaze_target_changed"})


def test_the_subject_can_arrive_in_the_payload():
    assert px.is_play({"seq": 1, "type": "water_play",
                       "payload": {"subject": "dive", "fun": True}})


# ── simulated, non-negotiably ──────────────────────────────────────────────

def test_play_is_recorded_as_simulated_experience():
    """
    WO-CAP-EMB-051: "SIMULATED EXPERIENCE != PHYSICAL EXPERIENCE ... they must
    be labelled differently. Otherwise 'I already know how this works' could
    mean 'I tested it in Unity' when it has never physically done it."

    eLo diving in Presence did not get wet.
    """
    from runtime.memory_origin import MemoryOrigin
    rec = px.record(_fun("dive"))
    assert rec is not None and rec.get("claim_id")

    claim = next(c for c in wkg.all_claims() if c["claim_id"] == rec["claim_id"])
    assert claim["memory_origin"] == MemoryOrigin.SIMULATED_EXPERIENCE.value
    assert claim["memory_origin"] != MemoryOrigin.PHYSICAL_EXPERIENCE.value


def test_the_claim_is_an_observation_of_him_not_an_identity():
    rec = px.record(_auto("chimney"))
    claim = next(c for c in wkg.all_claims() if c["claim_id"] == rec["claim_id"])
    assert claim["relationship_type"] == "OBSERVED_AS"
    assert claim["significance_score"] == px.SIGNIFICANCE[px.AUTO_ACTION]


def test_the_significance_reaches_the_claim():
    rec = px.record(_fun("leap"))
    claim = next(c for c in wkg.all_claims() if c["claim_id"] == rec["claim_id"])
    assert claim["significance_score"] == px.SIGNIFICANCE[px.WATER_PLAY]


# ── the cursor ─────────────────────────────────────────────────────────────

def test_a_play_event_is_not_recorded_twice():
    px.drain_pending(events=[_fun(seq=5)])
    before = len(wkg.all_claims())
    px.drain_pending(events=[])
    assert len(wkg.all_claims()) == before


def test_the_cursor_advances_past_unrelated_events():
    res = px.drain_pending(events=[{"seq": 77, "type": "gaze_target_changed"}])
    assert res["recorded"] == 0 and res["consumed_seq"] == 77


def test_a_burst_is_bounded():
    res = px.drain_pending(events=[_fun(seq=i) for i in range(100)], apply=False)
    assert res["seen"] == 100


def test_it_never_writes_the_shared_cursor(monkeypatch):
    import runtime.unity_events_cursor as uec
    monkeypatch.setattr(uec, "write_cursor",
                        lambda *a, **k: pytest.fail("wrote the shared cursor"))
    px.drain_pending(events=[_fun()])


# ── it never costs a tick ──────────────────────────────────────────────────

def test_a_wkg_failure_is_absorbed(monkeypatch):
    monkeypatch.setattr(wkg, "record_claim",
                        lambda **k: (_ for _ in ()).throw(RuntimeError("wkg down")))
    assert px.record(_fun()) is None


def test_a_malformed_event_is_skipped():
    assert px.record(None) is None
    assert px.record({}) is None


# ── and it is actually called ──────────────────────────────────────────────

def test_the_ambient_tick_consumes_it():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "ambient" / "ambient_engine.py").read_text()
    assert "from core.play_experience import drain_pending" in src
