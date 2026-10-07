"""
tests/test_mind_body_split.py — David's 70/30 body/mind ruling, 2026-10-07.

    "The 60% mind / 40% body blend is WRONG. Mind is not more than body."
    "Split confirmed by David: 70% body / 30% mind."
    "Mind battery stays internal, drives dreaming only — correct as-is."

The last line was not correct as-is, and the first makes it worse. The dream
trigger read elo_battery — the BLEND — so at 70/30 a rested body floors it at
0.70 against an ENERGY_LOW of 0.25:

    cog   phys | blend @60/40 | blend @70/30 | dream fires
    0.05  1.00 |    0.430     |    0.715     | no  -> no
    0.10  1.00 |    0.460     |    0.730     | no  -> no
    0.20  0.30 |    0.240     |    0.270     | YES -> no

A mentally exhausted eLo with working legs would never dream.
"""
from __future__ import annotations

import pytest

import core.health_battery as hb


# ── the ruling ──────────────────────────────────────────────────────────────

def test_body_outweighs_mind():
    assert hb.WEIGHT_PHYSICAL == pytest.approx(0.7)
    assert hb.WEIGHT_COGNITIVE == pytest.approx(0.3)


def test_the_weights_still_sum_to_one():
    assert hb.WEIGHT_PHYSICAL + hb.WEIGHT_COGNITIVE == pytest.approx(1.0)


def test_mind_is_never_weighted_above_body_again():
    """The thing David actually objected to."""
    assert hb.WEIGHT_PHYSICAL >= hb.WEIGHT_COGNITIVE


# ── dreaming reads the mind, not the blend ─────────────────────────────────

def test_the_mind_battery_is_exposed_unblended():
    assert "mind_battery" in hb.snapshot()


def test_a_spent_mind_can_dream_with_a_rested_body(monkeypatch):
    """
    The case the ruling cares about and the blend forbids: mentally
    exhausted, physically fine.
    """
    import ambient.ambient_engine as ae
    monkeypatch.setattr(ae, "_dream_trigger_ts", 0.0)

    out = ae._maybe_emit_dream_intent(
        {"mind_battery": 0.05, "elo_battery": 0.715, "physical_battery": 1.0},
        {"is_calm": True},
    )
    assert out == {"intent": "dream"}, (
        "a mentally spent eLo with working legs could not dream — the "
        "trigger is reading the blend again"
    )


def test_a_rested_mind_does_not_dream(monkeypatch):
    import ambient.ambient_engine as ae
    monkeypatch.setattr(ae, "_dream_trigger_ts", 0.0)
    assert ae._maybe_emit_dream_intent(
        {"mind_battery": 0.9, "elo_battery": 0.3}, {"is_calm": True}) == {}


def test_an_old_snapshot_degrades_to_the_previous_behaviour(monkeypatch):
    """
    A state file written before this field should fall back to elo_battery,
    not never dream.
    """
    import ambient.ambient_engine as ae
    monkeypatch.setattr(ae, "_dream_trigger_ts", 0.0)
    assert ae._maybe_emit_dream_intent(
        {"elo_battery": 0.05}, {"is_calm": True}) == {"intent": "dream"}


def test_dreaming_still_requires_calm(monkeypatch):
    import ambient.ambient_engine as ae
    monkeypatch.setattr(ae, "_dream_trigger_ts", 0.0)
    assert ae._maybe_emit_dream_intent(
        {"mind_battery": 0.05}, {"is_calm": False}) == {}


# ── the blend itself ────────────────────────────────────────────────────────

def test_an_untracked_body_leaves_the_blend_alone(monkeypatch):
    """
    On desktop there is no motion sensor, so physical sits at 1.0. Folding it
    in unconditionally would floor elo_battery at 0.70 and make
    ENERGY_CRITICAL unreachable — the reason this guard exists.
    """
    monkeypatch.setattr(hb, "_physical_engaged", False)
    monkeypatch.setattr(hb, "_cognitive_battery", 0.1)
    monkeypatch.setattr(hb, "_physical_battery", 1.0)
    assert hb._combined() == pytest.approx(0.1)


def test_an_engaged_body_dominates_the_blend(monkeypatch):
    monkeypatch.setattr(hb, "_physical_engaged", True)
    monkeypatch.setattr(hb, "_cognitive_battery", 1.0)
    monkeypatch.setattr(hb, "_physical_battery", 0.0)
    assert hb._combined() == pytest.approx(0.3), (
        "a spent body should pull the blend down hard — it is 70% of it"
    )
