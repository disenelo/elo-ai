"""
tests/test_collectible_intake.py — WO-GAME-002, Builder 2's half.

The WO gives the Designer the spawning and pickup, and names one thing as
mine:

    "Signal feeds Health Battery (Builder 2) — collecting food restores
     energy."
    Done when: ... Health Battery receives signal and responds.

Signal shape, verbatim from the WO:

    {"type": "collectible", "item": "apple", "count": N, "timestamp": ...}

The Unity side does not exist yet. The honest failure mode for that is a
module that works and is called by nothing, so this is consumed by
ambient_engine's existing tick from the moment it lands.
"""
from __future__ import annotations

import json

import pytest

from core import collectible_intake as ci


@pytest.fixture(autouse=True)
def _own_cursor(tmp_path, monkeypatch):
    """Never the live cursor — it belongs to a running system."""
    monkeypatch.setattr(ci, "CURSOR_PATH", str(tmp_path / "collectible_cursor.json"))


def _apple(seq=1, count=1):
    return {"seq": seq, "type": "collectible", "item": "apple",
            "count": count, "timestamp": 1790000000.0}


# ── the battery responds ────────────────────────────────────────────────────

def test_an_apple_restores_the_body(monkeypatch):
    got = {}
    import core.health_battery as hb
    monkeypatch.setattr(hb, "restore_physical", lambda a: got.update(amount=a))

    res = ci.drain_pending(events=[_apple()])

    assert res["items"] == 1
    assert got["amount"] == pytest.approx(ci.ITEM_RESTORE["apple"])


def test_food_restores_the_physical_track_not_the_cognitive(monkeypatch):
    """
    Walking to an apple is physical effort and eating it is physical
    recovery. It does not make eLo less tired of thinking, and health_battery
    keeps those tracks apart.
    """
    import core.health_battery as hb
    calls = []
    monkeypatch.setattr(hb, "restore_physical", lambda a: calls.append(("physical", a)))
    monkeypatch.setattr(hb, "restore", lambda a: calls.append(("cognitive", a)))

    ci.drain_pending(events=[_apple()])

    assert [c[0] for c in calls] == ["physical"]


def test_count_is_honoured():
    assert ci.amount_for_events([_apple(count=3)]) == pytest.approx(
        ci.ITEM_RESTORE["apple"] * 3)


def test_an_unknown_item_still_feeds_something():
    assert ci.amount_for_events(
        [{"type": "collectible", "item": "pear"}]) == ci.DEFAULT_RESTORE


# ── it cannot be farmed ─────────────────────────────────────────────────────

def test_a_burst_cannot_refill_the_whole_battery():
    flood = [_apple(seq=i) for i in range(200)]
    assert ci.amount_for_events(flood) == ci.MAX_RESTORE_PER_DRAIN


def test_a_hostile_count_is_clamped():
    assert ci.amount_for_events([_apple(count=10_000)]) <= ci.MAX_RESTORE_PER_DRAIN


def test_a_malformed_count_is_treated_as_one():
    assert ci.amount_for_events(
        [{"type": "collectible", "item": "apple", "count": "lots"}]
    ) == pytest.approx(ci.ITEM_RESTORE["apple"])


# ── the cursor ──────────────────────────────────────────────────────────────

def test_an_event_is_not_eaten_twice(monkeypatch):
    import core.health_battery as hb
    total = []
    monkeypatch.setattr(hb, "restore_physical", lambda a: total.append(a))

    ci.drain_pending(events=[_apple(seq=7)])
    # The same row again: already below the cursor, so nothing happens.
    second = ci.drain_pending(events=[])

    assert len(total) == 1
    assert second["restored"] == 0.0


def test_the_cursor_advances_past_unrelated_events(monkeypatch):
    import core.health_battery as hb
    monkeypatch.setattr(hb, "restore_physical", lambda a: None)

    res = ci.drain_pending(events=[{"seq": 42, "type": "sit_complete"}])

    assert res["items"] == 0
    assert res["consumed_seq"] == 42, (
        "a log full of body ACKs would be rescanned forever"
    )


def test_it_never_writes_the_shared_cursor(monkeypatch):
    """
    server.py tracks its own consumed_seq against the same append-log. Sharing
    one cursor would mean each reader silently eating the other's events.
    """
    import runtime.unity_events_cursor as uec
    monkeypatch.setattr(uec, "write_cursor",
                        lambda *a, **k: pytest.fail("wrote the shared cursor"))
    import core.health_battery as hb
    monkeypatch.setattr(hb, "restore_physical", lambda a: None)
    ci.drain_pending(events=[_apple()])


# ── it fails quietly ────────────────────────────────────────────────────────

def test_a_broken_battery_does_not_break_the_tick(monkeypatch):
    import core.health_battery as hb

    def _boom(a):
        raise RuntimeError("battery unavailable")
    monkeypatch.setattr(hb, "restore_physical", _boom)

    res = ci.drain_pending(events=[_apple()])
    assert res["restored"] == 0.0


def test_no_events_is_a_no_op():
    assert ci.drain_pending(events=[])["restored"] == 0.0


# ── and it is actually called ───────────────────────────────────────────────

def test_the_ambient_tick_consumes_it():
    """A module nothing calls is the defect this codebase keeps making."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "ambient" / "ambient_engine.py").read_text()
    assert "from core.collectible_intake import drain_pending" in src
