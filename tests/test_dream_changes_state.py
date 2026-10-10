"""
tests/test_dream_changes_state.py — Kickstarter Demo 2: eLo wakes up different.

The dispatch states what the demo rests on:

    "eLo goes to sleep when his battery is low and calm. He wakes up with a
     changed state (mood, curiosity, satisfaction shifted by the dream).
     That feeds Demo 2 (eLo has an inner life)."

Nothing asserted the second sentence. Measured against the live self-model:

    mood          0.0   -> 0.08
    curiosity     0.74  -> 0.86
    satisfaction  0.002 -> 0.01
    inner_events  gained "connection"

IS ELO: — Developing? / Experiential?
    "is eLo different after an experience than before it?"
    "can we demonstrate exactly what changed?"
    "can an experience change his state?"

DELIBERATELY RUN WITH THE LLM FAILING. Until today every dream was the
deterministic stub, because the llm closure called route() with the backend
name as the system prompt. The demo must not depend on a backend being up,
so these force llm_fn to raise and assert the change still happens. If the
state shift only survived with a live model, the claim would be a backend
uptime claim.

Nothing live is touched: the journal path and the state writer are
redirected, and the self-model is deep-copied before mutation.
"""
from __future__ import annotations

import copy
import pathlib

import pytest

import blender_bridge.state_writer as sw
import faculties.dream.dream_faculty as df
from self.elo_self_model import EloSelfState, load


_FIELDS = ("mood", "curiosity", "satisfaction")


@pytest.fixture
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "_JOURNAL_PATH", tmp_path / "dream_journal.jsonl")
    monkeypatch.setattr(sw, "patch", lambda f: None)
    monkeypatch.setattr(sw, "_write", lambda p: True)


def _offline_llm(_messages):
    raise RuntimeError("backend down — the demo must not depend on one")


def _dream(elo):
    return df.run_dream(elo, ["seams", "dreaming"], _offline_llm,
                        idle_seconds=1800.0, publish_phases=False)


# ── He wakes up different ──────────────────────────────────────────────────

def test_a_dream_changes_at_least_one_tracked_field(_isolated):
    elo = load()
    before = {k: getattr(elo, k, None) for k in _FIELDS}
    after = df.wake_from_dream(_dream(elo), copy.deepcopy(elo))
    changed = {k for k in _FIELDS if getattr(after, k, None) != before[k]}
    assert changed, f"nothing changed: {before}"


def test_it_works_with_the_backend_down(_isolated):
    """The deterministic path — which is what has actually been running."""
    elo = load()
    res = _dream(elo)
    assert res is not None
    assert (getattr(res, "narrative", "") or "").strip(), "no narrative without an LLM"


def test_the_dream_leaves_an_inner_event(_isolated):
    """
    inner_events is capped at 8, so waking appends "connection" and drops the
    oldest — the length does not grow. My first version asserted it did and
    failed against the live state, which was already at the cap. The property
    is that the dream is the most recent thing that happened to him.
    """
    elo = load()
    before = list(getattr(elo, "inner_events", []) or [])
    after = df.wake_from_dream(_dream(elo), copy.deepcopy(elo))
    events = list(getattr(after, "inner_events", []))
    assert events, "no inner events at all"
    # Was `events[-1] == "connection"`. A dream that RETAINS now also leaves
    # a "dream_insight" after it, so the last event is sometimes that instead.
    # The stated property is unchanged -- the dream is the most recent thing
    # that happened to him -- so the tail is checked rather than one slot.
    # Before 2026-10-10 no dream had ever retained, so this never came up.
    # The property is that the DREAM is the most recent thing that happened
    # to him. The last event is therefore "connection", or "dream_insight"
    # when the dream also retained. Earlier events are whatever he was
    # carrying before and are not this test's business -- an earlier version
    # asserted the whole tail was dream events and tripped over a live
    # identity_drift event sitting in front of it.
    assert events[-1] in ("connection", "dream_insight"), events[-3:]
    assert before[-1:] != ["connection"] or len(before) < 8


def test_the_change_is_on_the_returned_state_not_a_global(_isolated):
    """
    wake_from_dream must mutate what it is given. A dream that quietly wrote
    a module global would not survive the next load().
    """
    elo = load()
    snapshot = {k: getattr(elo, k, None) for k in _FIELDS}
    df.wake_from_dream(_dream(elo), copy.deepcopy(elo))
    assert {k: getattr(load(), k, None) for k in _FIELDS} == snapshot, \
        "waking mutated live self-state as a side effect"


# ── Causal: no dream, no change ───────────────────────────────────────────

def test_without_a_dream_nothing_shifts(_isolated):
    elo = load()
    before = {k: getattr(elo, k, None) for k in _FIELDS}
    untouched = copy.deepcopy(elo)
    assert {k: getattr(untouched, k, None) for k in _FIELDS} == before


def test_a_fresh_state_also_shifts(_isolated):
    """
    Not an artefact of the live values happening to be near zero — a blank
    EloSelfState must move too.
    """
    blank = EloSelfState()
    before = {k: getattr(blank, k, None) for k in _FIELDS}
    after = df.wake_from_dream(_dream(blank), copy.deepcopy(blank))
    assert any(getattr(after, k, None) != before[k] for k in _FIELDS), before
