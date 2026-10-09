"""
tests/test_s4_auto_calm_on_exhaustion.py — ADDENDUM A: exhausted triggers calm.

health_battery.should_auto_calm() has existed since the physical track was
built. Production callers: zero. Only a test ever called it, and the docstring
"Exhausted triggers calm mode automatically (ADDENDUM A)" described something
that had never happened.

It could not have happened. should_auto_calm() is
`_physical_engaged and get_physical_state() == "exhausted"`, and
_physical_engaged was permanently False because nothing fed the track. The
function was unwired AND unreachable, which is why nobody noticed either.

Both halves are fixed now, so the rule can finally run. The entry point is
ambient_engine._calm_on_low_battery(), which already owns calm: it holds the
hard rule that the battery must NEVER reach sleep, and it yields to dreams,
speech and commands. Rest needed for a spent body is the same decision from a
different cause, so it belongs there rather than in a second calm path that
could disagree with the first.

Order matters: this depends on calm restoring the physical track (Part C 1/2).
Without that, entering calm on exhaustion is a one-way door.
"""
from __future__ import annotations

import pytest

import ambient.ambient_engine as ae
from core import health_battery as hb


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    hb.reset()
    ae._brain_calm_asserted = False
    monkeypatch.setattr(ae, "_is_calm", lambda: False)
    monkeypatch.setattr(ae, "_is_speaking", lambda: False)
    monkeypatch.setattr(ae, "_is_commanded", lambda: False)
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: False)
    yield
    hb.reset()
    ae._brain_calm_asserted = False


def _exhaust_the_body():
    hb.drain_physical(1.0)
    assert hb.snapshot()["physical_state"] == "exhausted"


_WALK = {"animation": "walk", "mode": "walk"}


# ── The rule ──────────────────────────────────────────────────────────────────

def test_a_spent_body_enters_calm_on_a_full_cognitive_battery():
    """
    The whole point. The mind is fine; the legs are done. Nothing in the
    cognitive battery can express that, which is why the physical track
    exists.
    """
    _exhaust_the_body()
    out = ae._calm_on_low_battery("full", _WALK)
    assert out["calm_mode"] is True
    assert out["motion"]["mode"] == "calm"


def test_a_rested_body_on_a_full_battery_stays_out_of_calm():
    out = ae._calm_on_low_battery("full", _WALK)
    assert out.get("calm_mode") is False
    assert "motion" not in out


def test_low_battery_still_enters_calm():
    """The original trigger must survive the new one."""
    out = ae._calm_on_low_battery("low", _WALK)
    assert out["calm_mode"] is True
    assert out["motion"]["mode"] == "calm"


def test_calm_is_held_while_the_body_is_still_spent():
    _exhaust_the_body()
    ae._calm_on_low_battery("full", _WALK)
    held = ae._calm_on_low_battery("full", {"animation": "calm", "mode": "calm"})
    assert held["calm_mode"] is True
    assert "motion" not in held, "calm must not restart its own animation every tick"


def test_calm_releases_once_the_body_recovers():
    _exhaust_the_body()
    ae._calm_on_low_battery("full", _WALK)
    assert ae._brain_calm_asserted
    hb.restore_physical(1.0)
    out = ae._calm_on_low_battery("full", {"animation": "calm", "mode": "calm"})
    assert out["motion"]["mode"] == "idle", "recovered — CalmExit should play"
    assert ae._brain_calm_asserted is False


# ── The hard rule ─────────────────────────────────────────────────────────────

def test_it_never_writes_a_sleep_or_dream_field():
    """
    "The battery must NEVER reach sleep." Sleep=Dream is one coupled state
    gated on dream_phase, and a second route into it would disconnect sleep
    from dreaming — the one thing David ruled out.
    """
    _exhaust_the_body()
    out = ae._calm_on_low_battery("critical", _WALK)
    blob = repr(out).lower()
    for forbidden in ("dream_phase", "asleep", "sleep", "nrem", "rem"):
        assert forbidden not in blob, (forbidden, out)


@pytest.mark.parametrize("yielding", ["_is_speaking", "_is_commanded"])
def test_it_yields_rather_than_taking_the_body(monkeypatch, yielding):
    _exhaust_the_body()
    monkeypatch.setattr(ae, yielding, lambda: True)
    out = ae._calm_on_low_battery("full", _WALK)
    assert "motion" not in out, yielding


def test_a_dream_in_progress_keeps_the_body(monkeypatch):
    _exhaust_the_body()
    monkeypatch.setattr("faculties.dream.dream_faculty.is_dreaming", lambda: True)
    out = ae._calm_on_low_battery("full", _WALK)
    assert "motion" not in out


# ── End to end ───────────────────────────────────────────────────────────────

def test_walking_to_exhaustion_lands_in_calm_through_the_real_tick(monkeypatch):
    published: list[dict] = []
    monkeypatch.setattr("blender_bridge.state_writer.patch", published.append)
    monkeypatch.setattr(ae, "_read_state", lambda: {"motion": _WALK})
    # Seal the tick off from David's actual desktop. _battery_tick ingests
    # blender/motion_state.json whenever it is fresher than 2s and that
    # OVERRIDES _read_state — so while eLo is running, this test asserted on
    # `walk` and the tick silently saw whatever eLo was really doing.
    # Observed 2026-10-09: live file said `sitting`, so he never drained and
    # the test failed with "walked to rested". Green when eLo was off, red
    # when he was on; nothing to do with the code under test.
    monkeypatch.setattr(ae, "_MOTION_STATE_PATH", "/nonexistent/motion_state.json")
    monkeypatch.setattr("self.elo_self_model.update", lambda fn: None)

    import time
    # Rates are per-minute (Board ruling 2026-10-04). Use 30s simulated dt per
    # tick so 2400 ticks = 1200 min — enough to drain to exhausted at 0.003/min.
    for _ in range(2400):
        ae._last_battery_ts = time.time() - 30.0
        ae._battery_tick()
        if published and (published[-1].get("motion") or {}).get("mode") == "calm":
            break
    assert published, "the tick published nothing"
    assert any((p.get("motion") or {}).get("mode") == "calm" for p in published), (
        f"walked to {hb.snapshot()['physical_state']} and never rested")
