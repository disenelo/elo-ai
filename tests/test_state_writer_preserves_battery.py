"""
tests/test_state_writer_preserves_battery.py — WO-HEALTH-BATTERY-001 /
WO-DREAM-ENGINE-001 PHASE 9.

state_writer._write() REPLACES blender_state.json wholesale, carrying over
only the keys in _PRESERVE_KEYS. Anything else is dropped.

health_battery.publish() writes via patch() (a merge), so the fields land —
but the next full _write() would delete them again. Unity's battery indicator
would flicker on and off every cycle, and the dream schedule signals would
vanish mid-dream.

The file already documents this trap: "absent from this set = droppable on any
patch". WO-MOBILE-PHASE2 hit it before this WO did.
"""
from __future__ import annotations

import json

import pytest

from blender_bridge import state_writer as sw

_BATTERY_KEYS = (
    "elo_battery", "elo_battery_state",
    "physical_battery", "physical_state",
    "activity_recent", "activity_duration_minutes",
)
_DREAM_KEYS = ("dream_cycle", "dream_phase", "dream_intensity")


@pytest.mark.parametrize("key", _BATTERY_KEYS + _DREAM_KEYS)
def test_key_is_in_the_preserve_set(key):
    assert key in sw._PRESERVE_KEYS, (
        f"{key} would be dropped by the next full state write"
    )


def test_intent_is_preserved_so_the_dream_pose_survives():
    """S3 writes intent='dream'; a state write mid-dream must not clear it."""
    assert "intent" in sw._PRESERVE_KEYS


def test_write_actually_carries_the_fields_over(tmp_path, monkeypatch):
    """Behavioural, not just membership: round-trip through _write()."""
    state_path = tmp_path / "blender_state.json"
    prior = {
        "state": {"mode": "idle"},
        "motion": {"animation": "idle"},
        "intent": "dream",
        "elo_battery": 0.42,
        "elo_battery_state": "normal",
        "physical_battery": 0.31,
        "physical_state": "tired",
        "activity_recent": "walking",
        "activity_duration_minutes": 12.5,
        "dream_cycle": 3,
        "dream_phase": "rem",
        "dream_intensity": 0.6,
    }
    state_path.write_text(json.dumps(prior), encoding="utf-8")
    monkeypatch.setattr(sw, "_STATE_PATH", str(state_path))
    monkeypatch.setattr(sw, "_dispatch_to_targets", lambda payload: None)

    # a full write that knows nothing about the battery or the dream
    sw._write({"state": {"mode": "listening"}, "motion": {"animation": "walk"}})

    after = json.loads(state_path.read_text(encoding="utf-8"))
    assert after["state"]["mode"] == "listening"        # the write applied
    for key in _BATTERY_KEYS + _DREAM_KEYS + ("intent",):
        assert key in after, f"{key} was dropped by _write()"
        assert after[key] == prior[key], f"{key} changed value"


def test_a_real_publish_then_write_keeps_the_battery(tmp_path, monkeypatch):
    """End to end: health_battery.publish() -> full write -> fields still there."""
    from core import health_battery as hb

    state_path = tmp_path / "blender_state.json"
    state_path.write_text(json.dumps({"state": {"mode": "idle"}}), encoding="utf-8")
    monkeypatch.setattr(sw, "_STATE_PATH", str(state_path))
    monkeypatch.setattr(sw, "_dispatch_to_targets", lambda payload: None)

    hb.reset(cognitive=0.33)
    hb.publish()
    assert json.loads(state_path.read_text())["elo_battery"] == 0.33

    sw._write({"state": {"mode": "speaking"}})
    after = json.loads(state_path.read_text())
    assert after["elo_battery"] == 0.33, "battery wiped by the next state write"
    hb.reset()
