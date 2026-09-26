"""
tests/test_no_live_state_writes.py — guard: the test suite must not mutate
live runtime state.

Found the hard way. tests/test_s4_wake_restore.py called wake_from_dream(),
which calls health_battery.publish(), which deep-merges into the REAL
blender/blender_state.json. Running the suite wrote elo_battery=0.4 into the
running system (0.10 + 0.30 from test_full_cycle_restores_thirty).

blender_state.json is live: a running server writes it every cycle and
DesktopBuddy reads it every frame. Tests writing to it corrupt whatever the
avatar is doing and poison any live evidence captured afterwards.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LIVE_STATE = ROOT / "blender" / "blender_state.json"

# Test modules whose code paths can reach health_battery.publish().
_PUBLISHERS = (
    "test_s4_wake_restore.py",
    "test_s4_ambient_tick.py",
)


@pytest.mark.parametrize("name", _PUBLISHERS)
def test_publishing_suites_stub_publish(name):
    """Any suite that can reach publish() must stub it."""
    src = (Path(__file__).parent / name).read_text(encoding="utf-8")
    assert 'monkeypatch.setattr(hb, "publish"' in src, (
        f"{name} can reach health_battery.publish() but does not stub it — "
        "it will write to the live blender_state.json"
    )


def test_live_state_is_untouched_by_importing_the_battery():
    """Importing the module must not have a side effect on live state."""
    if not LIVE_STATE.exists():
        pytest.skip("no live blender_state.json on this machine")
    before = LIVE_STATE.read_bytes()
    import importlib

    import core.health_battery as hb
    importlib.reload(hb)
    assert LIVE_STATE.read_bytes() == before


def test_battery_reset_and_snapshot_do_not_write():
    """reset()/snapshot()/tick() are pure — only publish() writes."""
    if not LIVE_STATE.exists():
        pytest.skip("no live blender_state.json on this machine")
    from core import health_battery as hb

    before = LIVE_STATE.read_bytes()
    hb.reset()
    hb.tick({"animation": "walk"})
    hb.snapshot()
    hb.get_energy()
    hb.get_state()
    assert LIVE_STATE.read_bytes() == before, "a non-publish call wrote live state"
    hb.reset()


def test_live_state_stays_valid_json():
    """A half-written state file would break DesktopBuddy's reader."""
    if not LIVE_STATE.exists():
        pytest.skip("no live blender_state.json on this machine")
    data = json.loads(LIVE_STATE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "state" in data and "motion" in data
