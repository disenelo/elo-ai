"""
tests/test_motion_state_json_read.py — WO-MOTION-STATE-READ

Designer writes blender/motion_state.json; ambient_engine._battery_tick()
ingests it and feeds the physical track of health_battery.

Test: fresh motion_state.json with physical_state=teleporting, animation=teleport
→ _battery_tick() calls → health_battery.get_physical() < 1.0.
"""
from __future__ import annotations

import json
import time

import pytest

import ambient.ambient_engine as ae
from core import health_battery as hb


@pytest.fixture(autouse=True)
def _clean():
    hb.reset()
    yield
    hb.reset()


def test_motion_state_teleport_drains_physical_battery(tmp_path, monkeypatch):
    """
    WO-MOTION-STATE-READ: a fresh motion_state.json with teleport activity
    reaches the physical battery via _battery_tick().
    """
    # Write a temp motion_state.json with a fresh timestamp.
    motion_file = tmp_path / "motion_state.json"
    motion_file.write_text(json.dumps({
        "physical_state": "teleporting",
        "animation": "teleport",
        "timestamp": time.time(),
    }))

    # Redirect the engine to our temp file.
    monkeypatch.setattr(ae, "_MOTION_STATE_PATH", str(motion_file))

    # Isolate _battery_tick from live server state: give it a clean state dict.
    monkeypatch.setattr(ae, "_read_state", lambda: {})

    # Silence the state writer — we only care about health_battery.
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda p: None)

    ae._battery_tick()

    assert hb.get_physical() < 1.0, (
        "physical battery not drained — motion_state.json teleport event not ingested"
    )
    assert hb._physical_engaged is True


def test_stale_motion_state_is_ignored(tmp_path, monkeypatch):
    """
    A motion_state.json older than 2s must NOT affect the battery
    (stale file = Unity is paused / file is from a previous session).
    """
    motion_file = tmp_path / "motion_state.json"
    motion_file.write_text(json.dumps({
        "physical_state": "teleporting",
        "animation": "teleport",
        "timestamp": time.time() - 10.0,   # 10 seconds stale
    }))
    monkeypatch.setattr(ae, "_MOTION_STATE_PATH", str(motion_file))
    monkeypatch.setattr(ae, "_read_state", lambda: {})
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda p: None)

    ae._battery_tick()

    # Stale file — physical track must not engage from this source.
    # (Cognitive idle drain still fires; we only assert the physical track.)
    assert hb._physical_engaged is False, (
        "stale motion_state.json engaged the physical track — 2s freshness guard missing"
    )
