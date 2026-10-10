"""
tests/test_random_fact_signal.py — WO-B1-0110, Builder 2's half.

eLo raises a hand to say a WKG fact unprompted. Builder 1 owns the selector
and the speaking; this owns WHEN, and these pin all four of their gates.

The roll is 12%, so every test injects `rng` and `now`. A probabilistic branch
checked by "I ran it and it did the right thing" is checked by luck.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faculties.inner_thought import random_fact as rf  # noqa: E402

# Captured before the autouse fixture stubs them, so the gate tests below can
# exercise the real thing.
_REAL_PRESENT = rf._david_is_present
_REAL_FREE = rf._eLo_is_free

NOW = 1_800_000_000.0


class _Roll:
    """A pinned die."""
    def __init__(self, value): self._v = value
    def random(self): return self._v


ALWAYS = _Roll(0.0)     # below CHANCE — fires
NEVER = _Roll(0.99)     # above CHANCE — does not


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Own signal file, David present, eLo free. Tests turn these off."""
    monkeypatch.setattr(rf, "SIGNAL_PATH", tmp_path / "random_fact.json")
    monkeypatch.setattr(rf, "_david_is_present", lambda now: True)
    monkeypatch.setattr(rf, "_eLo_is_free", lambda: True)


# ── gate 1: David present ────────────────────────────────────────────────────

def test_it_does_not_speak_to_an_empty_room(monkeypatch):
    monkeypatch.setattr(rf, "_david_is_present", lambda now: False)
    assert rf.maybe_signal("RESTING", now=NOW, rng=ALWAYS) is False


def test_nobody_having_spoken_this_boot_reads_as_away(monkeypatch):
    """Absent last_user_ts is not evidence David is here."""
    monkeypatch.setattr("ambient.ambient_engine._read_state", lambda: {})
    assert _REAL_PRESENT(NOW) is False


# ── gate 2: state ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("state", ["RESTING", "AWAKE"])
def test_it_fires_in_an_eligible_state(state):
    assert rf.maybe_signal(state, now=NOW, rng=ALWAYS) is True
    assert rf.is_pending() is True


@pytest.mark.parametrize("state", ["SLEEP", "", "DREAM", None])
def test_it_never_fires_outside_those_two(state):
    assert rf.maybe_signal(state, now=NOW, rng=ALWAYS) is False


def test_it_does_not_interrupt_a_dream(monkeypatch):
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: True)
    assert _REAL_FREE() is False


def test_it_does_not_talk_over_him(monkeypatch):
    monkeypatch.setattr("ambient.ambient_engine._is_speaking", lambda: True)
    assert _REAL_FREE() is False


# ── gate 3: the 15-minute clock ──────────────────────────────────────────────

def test_it_waits_fifteen_minutes(monkeypatch):
    assert rf.maybe_signal("RESTING", now=NOW, rng=ALWAYS) is True
    rf.clear_pending(now=NOW)
    assert rf.maybe_signal("RESTING", now=NOW + 60, rng=ALWAYS) is False
    assert rf.maybe_signal("RESTING", now=NOW + rf.MIN_INTERVAL_S + 1,
                           rng=ALWAYS) is True


def test_the_clock_starts_when_he_says_it_not_when_he_decides_to():
    """clear_pending stamps the time, so a fact waiting all night is not free."""
    rf.maybe_signal("RESTING", now=NOW, rng=ALWAYS)
    rf.clear_pending(now=NOW)
    d = json.loads(Path(rf.SIGNAL_PATH).read_text())
    assert d["pending"] is False and d["last_random_fact_ts"] > 0


# ── gate 4: the roll ─────────────────────────────────────────────────────────

def test_the_roll_can_decline():
    assert rf.maybe_signal("RESTING", now=NOW, rng=NEVER) is False
    assert rf.is_pending() is False


# ── not stacking up ──────────────────────────────────────────────────────────

def test_one_pending_fact_at_a_time():
    assert rf.maybe_signal("RESTING", now=NOW, rng=ALWAYS) is True
    assert rf.maybe_signal("RESTING", now=NOW + 1, rng=ALWAYS) is False


# ── the life_tick seam Builder 1 reads ───────────────────────────────────────

def test_life_tick_carries_the_flag(monkeypatch):
    from faculties.inner_thought import life_tick
    monkeypatch.setattr(rf, "maybe_signal", lambda s: True)
    out = life_tick("RESTING")
    assert out["random_fact"] is True
    assert "random_fact" in out["actions"]


def test_life_tick_is_unharmed_when_the_check_explodes(monkeypatch):
    """eLo's life continuing is not worth crashing a daemon over."""
    from faculties.inner_thought import life_tick
    def _boom(_s): raise RuntimeError("nope")
    monkeypatch.setattr(rf, "maybe_signal", _boom)
    out = life_tick("RESTING")
    assert out["ok"] is True
    assert "random_fact" not in out
