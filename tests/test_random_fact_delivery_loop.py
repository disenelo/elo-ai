"""
tests/test_random_fact_delivery_loop.py — WO-B1-0110, delivery integration.

Builder 2 built the daemon-side raise-hand (maybe_signal → self/state/
random_fact.json). Builder 1 wired the delivery hook in server.py:1374-1388
(commit 8d1d4e3): poll is_pending → pick_random_fact → _voice_speak →
clear_pending.

This pins the API seam the two halves meet at. server.py itself is not
imported — exercising that would need a live server. Instead the delivery
block is reconstructed in-process from the exact three callables Builder 1
imports there, so a rename on either side fails this test rather than
silently breaking the loop at 02:00 while David is asleep.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faculties.inner_thought import random_fact as rf  # noqa: E402

NOW = 1_800_000_000.0


class _Roll:
    def __init__(self, v): self._v = v
    def random(self): return self._v


ALWAYS = _Roll(0.0)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(rf, "SIGNAL_PATH", tmp_path / "random_fact.json")
    monkeypatch.setattr(rf, "_david_is_present", lambda now: True)
    monkeypatch.setattr(rf, "_eLo_is_free", lambda: True)


def _server_delivery_block(spoken: list[str]) -> None:
    """
    Reconstructs server.py:1374-1388. If an import name changes on either
    side of the seam, this stops importing — which is the point.
    """
    from faculties.inner_thought.random_fact import (
        is_pending as _rf_is_pending,
        clear_pending as _rf_clear,
    )
    if _rf_is_pending():
        from runtime.wkg_faculty import pick_random_fact as _rf_pick
        text = _rf_pick()
        if text:
            spoken.append(text)
        _rf_clear()


def test_the_full_loop_delivers_and_clears(monkeypatch):
    """Daemon fires → delivery block speaks → flag cleared."""
    monkeypatch.setattr(
        "runtime.wkg_faculty.pick_random_fact",
        lambda entity_id=None: "Did you know — fact.",
    )

    assert rf.maybe_signal("RESTING", now=NOW, rng=ALWAYS) is True
    assert rf.is_pending() is True

    spoken: list[str] = []
    _server_delivery_block(spoken)

    assert spoken == ["Did you know — fact."]
    assert rf.is_pending() is False


def test_an_empty_pool_still_clears_the_flag(monkeypatch):
    """A pending flag that cannot be fulfilled must still be released,
    or the next 15 minutes do nothing."""
    monkeypatch.setattr(
        "runtime.wkg_faculty.pick_random_fact",
        lambda entity_id=None: None,
    )

    assert rf.maybe_signal("RESTING", now=NOW, rng=ALWAYS) is True
    spoken: list[str] = []
    _server_delivery_block(spoken)

    assert spoken == []
    assert rf.is_pending() is False


def test_delivery_is_a_no_op_when_no_flag_is_set():
    """Nothing to say → nothing is said, and the selector is never asked."""
    calls = {"n": 0}

    def _picker(entity_id=None):
        calls["n"] += 1
        return "x"

    import runtime.wkg_faculty as _wkg
    _orig = _wkg.pick_random_fact
    _wkg.pick_random_fact = _picker
    try:
        spoken: list[str] = []
        _server_delivery_block(spoken)
    finally:
        _wkg.pick_random_fact = _orig

    assert spoken == []
    assert calls["n"] == 0


def test_the_seam_names_builder_1_imports_still_exist():
    """A rename of these three breaks the live delivery hook. Guard it."""
    from faculties.inner_thought.random_fact import is_pending, clear_pending
    from runtime.wkg_faculty import pick_random_fact

    assert callable(is_pending)
    assert callable(clear_pending)
    assert callable(pick_random_fact)


def test_15_minute_clock_starts_from_delivery_not_fire(monkeypatch):
    """
    clear_pending() stamps last_random_fact_ts. The next fact is gated on
    that stamp, so if delivery lagged the daemon write by 10 minutes, the
    next window still has to wait a full 15 from when he actually spoke.
    """
    monkeypatch.setattr(
        "runtime.wkg_faculty.pick_random_fact",
        lambda entity_id=None: "ok.",
    )

    assert rf.maybe_signal("RESTING", now=NOW, rng=ALWAYS) is True

    # 10 minutes between daemon raising a hand and ambient tick delivering.
    delivery_ts = NOW + 600.0
    import time
    _orig_time = time.time
    time.time = lambda: delivery_ts
    try:
        spoken: list[str] = []
        _server_delivery_block(spoken)
    finally:
        time.time = _orig_time

    d = json.loads(Path(rf.SIGNAL_PATH).read_text())
    assert d["last_random_fact_ts"] == delivery_ts

    # Next tick 14 minutes after delivery: still inside the 15m clock.
    assert rf.maybe_signal(
        "RESTING", now=delivery_ts + 14 * 60, rng=ALWAYS
    ) is False
    # 16 minutes after delivery: clear.
    assert rf.maybe_signal(
        "RESTING", now=delivery_ts + 16 * 60, rng=ALWAYS
    ) is True
