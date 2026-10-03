"""
tests/test_s4_physical_activity_source.py — S4 · WO-TIRED-SIT-001 root cause.

David: "Can eLo walk, get tired, and sit down?"

The drain chain in core/health_battery.py is correct and fully covered. It is
also, in production, never fed. health_battery.tick() reads the activity from
motion["physical"] (or motion["motion_state"]). Nothing in the running system
writes either key — the only callers that supply "physical" are the tests in
tests/test_health_battery.py. So _tick_physical() returns on its first line
every tick, _physical_engaged stays False forever, and live blender_state.json
has sat at `physical_state: "untracked", physical_battery: null` since the
track was built.

A hundred passing tests, zero production input. The tests supplied the one
thing the real system never supplies.

These tests feed the EXACT dicts the production writers emit — captured from
ambient_engine._wander_animation() rather than retyped — so they cannot pass
on an input production does not produce.
"""
from __future__ import annotations

import threading

import pytest

from core import health_battery as hb


@pytest.fixture(autouse=True)
def _clean():
    hb.reset()
    yield
    hb.reset()


def _captured_wander_motions(monkeypatch) -> list[dict]:
    """Run the real ambient wander writer and capture what it actually emits."""
    import ambient.ambient_engine as ae

    seen: list[dict] = []
    monkeypatch.setattr(ae, "_patch_state", lambda p: seen.append(p))
    # Pre-set so the in-function wait returns immediately instead of sleeping.
    done = threading.Event()
    done.set()
    monkeypatch.setattr(ae, "_stop_ev", done)
    ae._wander_animation()
    return [p["motion"] for p in seen if "motion" in p]


# ── The shape of the real producers ───────────────────────────────────────────

def test_production_writers_emit_no_physical_key(monkeypatch):
    """
    Documents the gap rather than asserting it away: the production motion
    dict carries animation/mode, never "physical". If a future change starts
    writing "physical" at one call site only, the translator still has to
    cover the rest, so this stays a statement of fact, not a requirement.
    """
    motions = _captured_wander_motions(monkeypatch)
    assert motions, "wander writer emitted no motion at all"
    for m in motions:
        assert "physical" not in m
        assert "motion_state" not in m
        assert m.get("animation"), "every production motion names an animation"


# ── The chain, driven by production input ─────────────────────────────────────

def test_production_walk_motion_engages_physical_track(monkeypatch):
    """The first clip ambient actually writes must engage the physical track."""
    walk = next(m for m in _captured_wander_motions(monkeypatch)
                if m.get("animation") in ("walk", "run"))
    before = hb.get_physical()
    hb.tick(walk, dt_seconds=1.0)
    assert hb.snapshot()["physical_state"] != hb.PHYSICAL_UNTRACKED
    assert hb.get_physical() < before, "walking did not drain the physical track"


def test_server_explore_walk_dict_engages_physical_track():
    """server.py:1424 — the movement='explore' branch, verbatim."""
    hb.tick({"animation": "walk", "speed": 0.5, "intensity": 0.6,
             "duration": 8.0, "mood": "exploring", "mode": "walk"}, dt_seconds=1.0)
    assert hb.get_physical() < 1.0


def test_running_drains_faster_than_walking():
    hb.reset()
    hb.tick({"animation": "walk", "mode": "walk"}, dt_seconds=10.0)
    walked = 1.0 - hb.get_physical()
    hb.reset()
    hb.tick({"animation": "run", "mode": "run"}, dt_seconds=10.0)
    ran = 1.0 - hb.get_physical()
    assert ran > walked


def test_sustained_walking_reaches_the_tired_band():
    """
    The question David actually asked. Walk long enough and physical_state
    must land in a band PHYSICAL_EXPRESSIONS has words for.
    """
    walk = {"animation": "walk", "speed": 0.5, "intensity": 0.6,
            "duration": 8.0, "mood": "exploring", "mode": "walk"}
    for _ in range(600):              # 600 x 0.5s = five minutes of walking
        hb.tick(walk, dt_seconds=0.5)
    assert hb.snapshot()["physical_state"] in ("tired", "fatigued", "exhausted")
    assert hb.physical_conditioning() is not None, (
        "tired but the inner_thought pipeline was handed nothing to say")


def test_sitting_restores_what_walking_spent():
    walk = {"animation": "walk", "mode": "walk"}
    for _ in range(200):
        hb.tick(walk, dt_seconds=0.5)
    spent = hb.get_physical()
    sit = {"animation": "sit", "mode": "sit"}
    for _ in range(100):
        hb.tick(sit, dt_seconds=0.5)
    assert hb.get_physical() > spent, "sitting did not restore the physical track"


# ── Guards that must survive the fix ──────────────────────────────────────────

def test_idle_does_not_engage_physical_track():
    """
    Deliberate. "idle" is not mapped to "standing": a metabolic floor charged
    for merely existing makes eLo tired ~9 minutes after every boot, and
    health_battery.py:338 already rules idle out by name. Tiredness follows
    activity.
    """
    for _ in range(200):
        hb.tick({"animation": "idle", "speed": 0.5, "intensity": 0.5,
                 "duration": 4.0, "mood": "open", "mode": "idle"}, dt_seconds=0.5)
    assert hb.snapshot()["physical_state"] == hb.PHYSICAL_UNTRACKED
    assert hb.snapshot()["physical_battery"] is None


def test_unrecognised_animation_does_not_engage_physical_track():
    """
    Regression guard for the documented elo_battery floor: an unknown clip
    must not engage a track that has no rate to drain it. The translator adds
    names, it does not remove the PHYSICAL_ACTIVITIES gate.
    """
    for anim in ("floating", "perched", "look_around", "wave", "calm"):
        hb.reset()
        hb.tick({"animation": anim, "mode": anim}, dt_seconds=5.0)
        assert hb.snapshot()["physical_state"] == hb.PHYSICAL_UNTRACKED, anim


def test_explicit_physical_key_still_takes_precedence():
    """A caller that knows the real body state overrides the animation guess."""
    hb.tick({"animation": "walk", "mode": "walk", "physical": "sitting"},
            dt_seconds=1.0)
    assert hb.snapshot()["activity_recent"] == "sitting"
