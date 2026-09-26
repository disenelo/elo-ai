"""
tests/test_s4_ambient_tick.py — WO-HEALTH-BATTERY-001 PART A.1 / PART B.

The battery tick runs on the ambient engine's 0.5s poll loop. That is the only
real per-cycle loop in the system — the registered ambient callback fires every
8-20 minutes and is far too coarse to carry a per-minute restore rate.

Functional: drives _battery_tick() with a stubbed state reader, so no live
blender_state.json is touched.
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
    # never write to the live state file from a test
    monkeypatch.setattr(hb, "publish", lambda: True)
    yield
    hb.reset()
    ae._last_battery_ts = 0.0


def _drive(motion: dict, *, calm: bool = False, dt: float = 1.0, ticks: int = 1,
           idle: float = 0.0, monkeypatch=None):
    monkeypatch.setattr(ae, "_read_state", lambda: {"motion": motion})
    monkeypatch.setattr(ae, "_is_calm", lambda: calm)
    monkeypatch.setattr(ae, "_user_idle_secs", idle, raising=False)
    monkeypatch.setattr(ae, "_user_is_idle", idle > 0, raising=False)
    for _ in range(ticks):
        ae._last_battery_ts = time.time() - dt
        ae._battery_tick()


def test_tick_is_called_from_the_poll_loop_not_the_coarse_callback():
    src = (ae.__file__).replace(".pyc", ".py")
    with open(src, encoding="utf-8") as f:
        text = f.read()
    loop = text.index("while not _stop_ev.is_set():")
    poll = text.index("_read_events()", loop)
    call = text.index("_battery_tick()", loop)
    assert call < poll, "_battery_tick must run before the loop's early-exit branches"


def test_walking_drains_both_tracks(monkeypatch):
    _drive({"animation": "walk", "physical": "walking"}, ticks=3, monkeypatch=monkeypatch)
    assert hb.get_cognitive() < 1.0
    assert hb.get_physical() < 1.0
    assert hb.snapshot()["activity_recent"] == "walking"


def test_idle_tick_is_metabolic_floor_only(monkeypatch):
    _drive({"animation": "idle"}, ticks=1, monkeypatch=monkeypatch)
    assert round(1.0 - hb.get_cognitive(), 5) == hb.DRAIN_IDLE_TICK


def test_calm_restores_instead_of_draining(monkeypatch):
    hb.reset(cognitive=0.50)
    _drive({"animation": "idle"}, calm=True, dt=60.0, monkeypatch=monkeypatch)
    assert hb.get_cognitive() > 0.50, "calm did not restore"


def test_calm_rate_is_measured_not_assumed(monkeypatch):
    """dt is real elapsed time, so the rate holds at any poll interval."""
    hb.reset(cognitive=0.50)
    _drive({}, calm=True, dt=60.0, monkeypatch=monkeypatch)
    one_minute = hb.get_cognitive()
    hb.reset(cognitive=0.50)
    ae._last_battery_ts = 0.0
    _drive({}, calm=True, dt=30.0, ticks=2, monkeypatch=monkeypatch)
    assert hb.get_cognitive() == pytest.approx(one_minute, abs=1e-4)


def test_hard_idle_restores(monkeypatch):
    hb.reset(cognitive=0.50)
    _drive({"animation": "idle"}, idle=3600.0, dt=60.0, monkeypatch=monkeypatch)
    assert hb.get_cognitive() > 0.50 - hb.DRAIN_IDLE_TICK


def test_dt_is_clamped_after_a_suspend_gap(monkeypatch):
    """A laptop sleeping overnight must not restore the battery in one tick."""
    hb.reset(cognitive=0.20)
    _drive({}, calm=True, dt=86400.0, monkeypatch=monkeypatch)
    assert hb.get_cognitive() < 0.23, "unclamped dt let a whole night restore at once"


def test_tick_is_fail_quiet(monkeypatch):
    """The battery must never be able to stop ambient presence."""
    def boom():
        raise RuntimeError("state unreadable")
    monkeypatch.setattr(ae, "_read_state", boom)
    ae._battery_tick()          # must not raise


def test_is_calm_reads_presence_state_not_server(monkeypatch, tmp_path):
    """
    server.py runs as __main__, so importing it here would load a second copy
    of the module. _is_calm reads the same file server._is_calm_mode does.
    """
    src = open(ae.__file__.replace(".pyc", ".py"), encoding="utf-8").read()
    assert "from server import" not in src
    assert "presence_state.json" in src

    p = tmp_path / "presence_state.json"
    monkeypatch.setattr(ae, "_PRESENCE_STATE_PATH", str(p))
    p.write_text('{"state": "MEDITATION"}', encoding="utf-8")
    assert ae._is_calm() is True
    p.write_text('{"state": "IDLE"}', encoding="utf-8")
    assert ae._is_calm() is False, "IDLE is not calm"
    p.unlink()
    assert ae._is_calm() is False
