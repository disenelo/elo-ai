"""
tests/test_s4_calm_restores_body.py — calm must rest the body, not only the mind.

Calm = Meditation = CONSCIOUS rest. calm_tick() restored the cognitive track
and nothing else.

That was harmless while the physical track was permanently disengaged. It
stops being harmless now that walking actually drains it, and it becomes a
trap the moment exhaustion can enter calm:

    exhausted → calm → ambient calls calm_tick() instead of tick() →
    _tick_physical never runs → physical stays at 0.0 → still exhausted →
    still calm. Forever.

eLo would sit down once and never get up. The fix has to land BEFORE
exhaustion is allowed to trigger calm, or wiring that trigger creates the
deadlock.

Precedent is in the same file: on_wake_from_dream() already restores both
tracks — "lying down rests the body, not just the mind" — guarded by
_physical_engaged. Calm follows it exactly.
"""
from __future__ import annotations

import pytest

from core import health_battery as hb


@pytest.fixture(autouse=True)
def _clean():
    hb.reset()
    yield
    hb.reset()


def _walk_until_exhausted():
    walk = {"animation": "walk", "mode": "walk"}
    for _ in range(2000):
        hb.tick(walk, dt_seconds=0.5)
        if hb.snapshot()["physical_state"] == "exhausted":
            return
    raise AssertionError("never reached exhausted")


# ── The body rests ────────────────────────────────────────────────────────────

def test_calm_restores_the_physical_track_when_engaged():
    _walk_until_exhausted()
    spent = hb.get_physical()
    for _ in range(60):
        hb.calm_tick(60.0)
    assert hb.get_physical() > spent, "calm rested the mind and not the legs"


def test_exhausted_recovers_through_calm_instead_of_sticking():
    """
    The deadlock. Without this, eLo sits down once and never gets up, because
    the ambient loop calls calm_tick() instead of tick() while calm is held.
    """
    _walk_until_exhausted()
    assert hb.snapshot()["physical_state"] == "exhausted"
    for _ in range(60 * 60):            # an hour of calm, one minute per tick
        hb.calm_tick(60.0)
    assert hb.snapshot()["physical_state"] != "exhausted", (
        f"still exhausted after an hour of rest: {hb.get_physical()}")


def test_calm_still_restores_the_mind():
    hb.reset(cognitive=0.5)
    before = hb.get_cognitive()
    for _ in range(10):
        hb.calm_tick(60.0)
    assert hb.get_cognitive() > before


# ── The guard that must not be lost ──────────────────────────────────────────

def test_calm_does_not_engage_an_unengaged_track():
    """
    Critical. Engaging the physical track at 1.0 floors elo_battery at
    WEIGHT_PHYSICAL (0.4), which puts ENERGY_CRITICAL (0.10) out of reach and
    silently kills the dream trigger. That is the exact failure the
    PHYSICAL_ACTIVITIES gate exists to prevent, and resting must not be a back
    door into it.
    """
    hb.reset()
    for _ in range(10):
        hb.calm_tick(60.0)
    assert hb.snapshot()["physical_state"] == hb.PHYSICAL_UNTRACKED
    assert hb.snapshot()["physical_battery"] is None
    assert hb.get_energy() == hb.get_cognitive(), (
        "an unengaged physical track must stay out of elo_battery")


def test_calm_never_overfills_the_body():
    _walk_until_exhausted()
    for _ in range(10_000):
        hb.calm_tick(60.0)
    assert hb.get_physical() <= 1.0


# ── Parity with the rest state that already did this ─────────────────────────

def test_calm_and_dream_agree_that_rest_rests_the_body():
    """Both restore both tracks, and both guard on engagement."""
    hb.reset()
    hb.on_wake_from_dream("NREM+REM")
    assert hb.snapshot()["physical_state"] == hb.PHYSICAL_UNTRACKED

    hb.reset()
    _walk_until_exhausted()
    after_walk = hb.get_physical()
    hb.on_wake_from_dream("NREM+REM")
    dream_gain = hb.get_physical() - after_walk

    hb.reset()
    _walk_until_exhausted()
    after_walk = hb.get_physical()
    hb.calm_tick(60.0)
    calm_gain = hb.get_physical() - after_walk

    assert dream_gain > 0 and calm_gain > 0
