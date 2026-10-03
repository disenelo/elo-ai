"""
tests/test_s4_tired_signal.py — S4 · WO-TIRED-SIT-001 Part A.

physical_state reaches "tired" and lands in blender_state.json, and nothing
downstream ever hears about it. Part A emits the signal.

The dispatch's pseudo-code calls _queue_inner_event() and names a
"blender_state inner_events queue", "same pattern as idea_event,
gesture_event". Read against the source: there is no _queue_inner_event, no
inner_events queue in blender_state.json, and no gesture_event anywhere in the
repo. The real inner-events store is EloSelfState.inner_events — a list[str]
read by four live consumers (dream symbol_engine, dream_faculty,
emotional_processing_faculty, window_event_faculty) and rendered into the
prompt by elo_self_model.prompt_block(). That is where the signal goes.

Inventing a blender_state key no reader consumes would be write-only output,
which is the defect this stack keeps finding, not a fix for it.

The Board's constraint is tested here directly: the ambient tick emits a
SIGNAL and never a motion command. eLo decides whether to sit.
"""
from __future__ import annotations

import time

import pytest

import ambient.ambient_engine as ae
from core import health_battery as hb


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    hb.reset()
    ae._last_battery_ts = 0.0
    ae._tired_signal_ts.clear()
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda f: None)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)
    yield
    hb.reset()
    ae._last_battery_ts = 0.0
    ae._tired_signal_ts.clear()


def _drive(monkeypatch, motion: dict, *, ticks: int = 1, dt: float = 1.0,
           calm: bool = False) -> list[dict]:
    """Run the real battery tick; return every field dict it published."""
    published: list[dict] = []
    monkeypatch.setattr("blender_bridge.state_writer.patch", published.append)
    monkeypatch.setattr(ae, "_read_state", lambda: {"motion": motion})
    monkeypatch.setattr(ae, "_is_calm", lambda: calm)
    for _ in range(ticks):
        ae._last_battery_ts = time.time() - dt
        ae._battery_tick()
    return published


def _events(monkeypatch) -> list[str]:
    """Capture what the tick appends to EloSelfState.inner_events."""
    seen: list[str] = []

    class _S:
        inner_events: list = []

    def _fake_update(fn):
        st = _S()
        st.inner_events = list(seen)
        out = fn(st) or st
        seen[:] = list(out.inner_events)
        return out

    monkeypatch.setattr("self.elo_self_model.update", _fake_update)
    return seen


_WALK = {"animation": "walk", "speed": 0.5, "intensity": 0.6,
         "duration": 8.0, "mood": "exploring", "mode": "walk"}


# ── The signal ────────────────────────────────────────────────────────────────

def test_walking_to_tired_emits_an_inner_event(monkeypatch):
    seen = _events(monkeypatch)
    hb.reset(physical=0.21)                    # one tick above the tired floor
    _drive(monkeypatch, _WALK, ticks=3, dt=1.0)
    assert any(e.startswith("physical_tired") for e in seen), seen


def test_rested_emits_nothing(monkeypatch):
    seen = _events(monkeypatch)
    hb.reset()
    _drive(monkeypatch, _WALK, ticks=3, dt=1.0)
    assert not [e for e in seen if e.startswith("physical_tired")]


def test_the_band_is_named_in_the_event(monkeypatch):
    seen = _events(monkeypatch)
    hb.reset(physical=0.11)                    # fatigued band
    _drive(monkeypatch, _WALK, ticks=2, dt=1.0)
    assert any(e == "physical_tired:fatigued" for e in seen), seen


# ── Rate limit ────────────────────────────────────────────────────────────────

def test_rate_limited_to_once_per_minute_per_band(monkeypatch):
    seen = _events(monkeypatch)
    hb.reset(physical=0.21)
    _drive(monkeypatch, _WALK, ticks=40, dt=0.5)      # 20s of tired walking
    tired = [e for e in seen if e == "physical_tired:tired"]
    assert len(tired) == 1, f"spammed {len(tired)} events in 20s: {seen}"


def test_a_deeper_band_is_a_new_signal(monkeypatch):
    seen = _events(monkeypatch)
    hb.reset(physical=0.21)
    _drive(monkeypatch, _WALK, ticks=2, dt=1.0)
    hb.reset(physical=0.11)
    _drive(monkeypatch, _WALK, ticks=2, dt=1.0)
    bands = {e.split(":", 1)[1] for e in seen if e.startswith("physical_tired:")}
    assert bands == {"tired", "fatigued"}, seen


# ── The Board's constraint ────────────────────────────────────────────────────

def test_the_ambient_tick_never_issues_a_motion_command(monkeypatch):
    """
    "DO NOT issue a direct motion command from the ambient tick — eLo decides
    whether to sit, not the health battery." Asserted on what is published.
    """
    _events(monkeypatch)
    hb.reset(physical=0.05)                    # exhausted — strongest pull to sit
    published = _drive(monkeypatch, _WALK, ticks=4, dt=1.0)
    for fields in published:
        motion = fields.get("motion") or {}
        assert motion.get("mode") not in ("sit", "sitting"), fields
        assert "sit_command" not in fields, fields


def test_suppressed_while_already_resting(monkeypatch):
    seen = _events(monkeypatch)
    for mode in ("calm", "sit", "sitting", "sleeping", "dream"):
        ae._tired_signal_ts.clear()
        seen.clear()
        hb.reset(physical=0.05)
        hb.drain_physical(0.001)      # engage the track without leaving the band
        assert hb.snapshot()["physical_state"] == "exhausted"
        _drive(monkeypatch, {"animation": mode, "mode": mode}, ticks=3, dt=1.0)
        assert not [e for e in seen if e.startswith("physical_tired")], mode


# ── Causal: the signal actually reaches eLo ───────────────────────────────────

def test_the_event_reaches_the_prompt(monkeypatch):
    """
    Deleting the state must remove the influence. prompt_block() renders the
    last four inner_events, so an event that never arrives is an event eLo
    never sees.
    """
    from self.elo_self_model import EloSelfState, prompt_block
    with_ev = EloSelfState()
    with_ev.inner_events = ["physical_tired:fatigued"]
    without = EloSelfState()
    without.inner_events = []
    assert "physical_tired:fatigued" in prompt_block(with_ev)
    assert "physical_tired" not in prompt_block(without)
