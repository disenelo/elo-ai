"""
tests/test_dream_latch.py — a dream request must survive the next thing David says.

David, 2026-10-05: "How would it work if it isn't triggered and eLo is active?"

It did not. Measured on the live server: intent="dream" injected at 16:51:12,
and twenty-five turns were spoken before the ambient callback next ran. By
then `intent` read "conversation" and the request was gone.

The chain carries the request in blender_state's `intent`, which every turn
overwrites, and the gate reading it runs every 8-20 minutes. So the request
survived only if eLo stayed completely idle for up to twenty minutes. Builder
1's trigger fires on "battery low + calm", and calm does not stop David
speaking — so the drain-to-sleep chain was unreliable by construction, not by
accident.

Latch fast, consume slow: the 0.5s poll loop copies the request somewhere a
turn cannot reach, and the slow callback consumes the latch.
"""
from __future__ import annotations

import json
import time

import pytest

import runtime.dream_latch as dl
import runtime.dream_request as dr


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(dl, "_PATH", str(tmp_path / "dream_request.json"))
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda f: None)


# ── The latch itself ───────────────────────────────────────────────────────

def test_a_latched_request_is_pending():
    assert dl.latch() is True
    assert dl.pending() is True


def test_latching_twice_does_not_queue_two():
    assert dl.latch() is True
    assert dl.latch() is False
    assert dl.take() is True
    assert dl.take() is False


def test_taking_consumes_it():
    dl.latch()
    assert dl.take() is True
    assert dl.pending() is False


def test_nothing_latched_is_not_pending():
    assert dl.pending() is False
    assert dl.take() is False


def test_a_stale_request_is_dropped():
    """
    Waking eLo for a request from an hour ago is worse than missing it — his
    battery and calm state have moved on.
    """
    dl.latch()
    with open(dl._PATH, "w", encoding="utf-8") as f:
        json.dump({"_ts": time.time() - dl._MAX_AGE_S - 60}, f)
    assert dl.pending() is False
    assert dl.take() is False


def test_a_corrupt_latch_does_not_raise():
    with open(dl._PATH, "w", encoding="utf-8") as f:
        f.write("{not json")
    assert dl.pending() is False


# ── The request survives a turn ───────────────────────────────────────────

def test_a_latched_request_survives_intent_being_overwritten():
    """The exact failure: intent is now 'conversation', the request stands."""
    dl.latch("intent")
    assert dr.dream_requested({"intent": "conversation"}, consume=False) is True


def test_without_the_latch_an_overwritten_intent_is_lost():
    """Causal: no latch, and the turn has erased the request."""
    assert dr.dream_requested({"intent": "conversation"}, consume=False) is False


def test_a_live_intent_still_works_on_its_own():
    assert dr.dream_requested({"intent": "dream"}, consume=False) is True


def test_a_dream_in_flight_still_blocks_a_latched_request():
    """
    The re-entry guard must outrank the latch, or the dream re-enters itself
    every tick off its own published intent.
    """
    dl.latch()
    assert dr.dream_requested({"intent": "dream", "dream_phase": "NREM"},
                              consume=False) is False


def test_the_latch_is_consumed_when_the_request_is_accepted():
    dl.latch()
    assert dr.dream_requested({"intent": "conversation"}, consume=False) is True
    assert dl.pending() is False, "accepted twice would dream twice"


# ── The poll loop latches it ──────────────────────────────────────────────

def test_the_fast_tick_latches_before_a_turn_can_erase_it():
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "ambient" / "ambient_engine.py").read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert "from runtime.dream_latch import latch" in code
    assert '_battery_tick' in code
    # it must sit in the 0.5s battery tick, not the slow callback
    i_tick = code.index("def _battery_tick")
    i_latch = code.index("from runtime.dream_latch import latch")
    nxt = code.find("\ndef ", i_tick + 1)
    assert i_tick < i_latch < (nxt if nxt != -1 else len(code)), "latch is not inside the fast tick"
