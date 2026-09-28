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


def test_the_ambient_tick_is_the_only_battery_owner(monkeypatch):
    """
    The tick briefly moved to server.py's ambient_thought() (ea2d8c5, fixing a
    real double-tick). That was the wrong half to keep: ambient_thought is the
    registered CALLBACK and fires every 8-20 minutes. elo_battery is preserved
    across state writes, so between firings a stale value LOOKS live —
    observed on a 2.6-minute-old server reading 0.0 "critical", carried over
    from the previous night and never written once that boot.
    """
    from pathlib import Path as _P
    server = (_P(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")
    assert "_hb_tick" not in server, "server.py still ticks the battery — two owners"


def test_the_tick_drains_the_battery(monkeypatch):
    hb.reset()
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda f: None)
    monkeypatch.setattr(ae, "_read_state", lambda: {"motion": {"animation": "idle"}})
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)
    for _ in range(5):
        ae._last_battery_ts = time.time() - 1.0
        ae._battery_tick()
    assert hb.get_cognitive() < 1.0


def test_the_tick_always_emits_the_battery_fields(monkeypatch):
    """A preserved key written only sometimes goes stale and looks live."""
    written: list = []
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda f: written.append(f))
    monkeypatch.setattr(ae, "_read_state", lambda: {"motion": {}})
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)
    ae._last_battery_ts = time.time() - 1.0
    ae._battery_tick()
    for key in ("elo_battery", "elo_battery_state", "physical_state"):
        assert key in written[-1]


def test_idle_comes_from_published_last_user_ts(monkeypatch):
    """
    The loop has no access to server's session state, so server publishes
    last_user_ts. Absent means nobody has spoken this boot — idle then grows
    from loop start, never 0.0 forever.
    """
    src = open(ae.__file__.replace(".pyc", ".py"), encoding="utf-8").read()
    assert 'state.get("last_user_ts")' in src
    assert "_LOOP_START_TS" in src

    server = open(
        __file__.replace("tests/test_s4_ambient_tick.py", "server.py"), encoding="utf-8"
    ).read() if False else None  # server side asserted below

    from pathlib import Path as _P
    server = (_P(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")
    assert '_lut_patch({"last_user_ts": _state["last_user_ts"]})' in server


def test_hard_idle_restores_once_eLo_has_been_alone(monkeypatch):
    """The overnight flatline: without real idle this never fired."""
    hb.reset(cognitive=0.50)
    long_ago = time.time() - 4000.0
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda f: None)
    monkeypatch.setattr(ae, "_read_state",
                        lambda: {"motion": {}, "last_user_ts": long_ago})
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)
    for _ in range(10):
        ae._last_battery_ts = time.time() - 60.0
        ae._battery_tick()
    assert hb.get_cognitive() > 0.50, "hard idle did not restore"


def test_calm_mode_is_published_for_designer(monkeypatch):
    """Board 2026-09-27: Designer needs calm_mode for the conscious-rest anim."""
    written: list = []
    monkeypatch.setattr("blender_bridge.state_writer.patch", lambda f: written.append(f))
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)

    for calm in (True, False):
        monkeypatch.setattr(ae, "_is_calm", lambda c=calm: c)
        ae._last_battery_ts = time.time() - 1.0
        ae._battery_tick()
        assert written[-1]["calm_mode"] is calm


def test_calm_mode_shares_its_source_with_the_battery_restore():
    """
    The animation and the restore must never disagree about whether eLo is
    resting, so both read presence_state.json via _is_calm().
    """
    src = open(ae.__file__.replace(".pyc", ".py"), encoding="utf-8").read()
    idx = src.index('fields["calm_mode"]')
    assert "_is_calm()" in src[idx:idx + 120]


def test_calm_mode_survives_a_full_state_write():
    from blender_bridge import state_writer as sw
    assert "calm_mode" in sw._PRESERVE_KEYS


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


# ── Dream-state coherence ─────────────────────────────────────────────────────
# The dream fields are in state_writer._PRESERVE_KEYS and are only cleared on
# a clean dream exit, so they freeze. Observed live 2026-09-27: blender_state
# carried dream_cycle 5 / dream_phase "rem" / dream_intensity 1.0 while
# intent was "conversation" and state.mode was "idle" — eLo awake and talking,
# with Unity told he was in maximum-intensity REM sleep.

def test_awake_fields_clear_the_dream_state():
    from faculties.dream.sleep_cycle import awake_fields
    assert awake_fields() == {
        "dream_cycle": 0, "dream_phase": None, "dream_intensity": 0.0}


def test_tick_asserts_the_awake_case_when_not_dreaming(monkeypatch):
    written: list = []
    monkeypatch.setattr("blender_bridge.state_writer.patch",
                        lambda fields: written.append(fields))
    monkeypatch.setattr(ae, "_read_state", lambda: {"motion": {}})
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)

    ae._last_battery_ts = time.time() - 1.0
    ae._battery_tick()

    assert written, "tick wrote nothing"
    fields = written[-1]
    assert fields["dream_phase"] is None
    assert fields["dream_cycle"] == 0
    assert fields["dream_intensity"] == 0.0


def test_tick_does_not_clear_the_dream_state_mid_dream(monkeypatch):
    """A running dream owns those fields; the tick must not stamp over it."""
    written: list = []
    monkeypatch.setattr("blender_bridge.state_writer.patch",
                        lambda fields: written.append(fields))
    monkeypatch.setattr(ae, "_read_state", lambda: {"motion": {}})
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: True)

    ae._last_battery_ts = time.time() - 1.0
    ae._battery_tick()

    assert "dream_phase" not in written[-1]


def test_the_tick_makes_exactly_one_state_write(monkeypatch):
    """One read-modify-write pass over the live file per tick, not several."""
    written: list = []
    monkeypatch.setattr("blender_bridge.state_writer.patch",
                        lambda fields: written.append(fields))
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)

    ae._last_battery_ts = time.time() - 1.0
    ae._battery_tick()

    assert len(written) == 1
    assert "dream_phase" in written[0] and "calm_mode" in written[0]
    assert "elo_battery" in written[0]
