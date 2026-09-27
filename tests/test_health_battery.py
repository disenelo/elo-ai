"""
tests/test_health_battery.py — WO-HEALTH-BATTERY-001 PART A/B/D + ADDENDUM A.

Drain, restore, thresholds, physical track, game events, blender_state output.
No server, no network, no hardware.
"""
from __future__ import annotations

import json
import random

import pytest

from core import health_battery as hb


@pytest.fixture(autouse=True)
def _clean():
    hb.reset()
    yield
    hb.reset()


# ── PART A — drain / restore / thresholds ──────────────────────────────────────

def test_starts_full():
    assert hb.get_energy() == 1.0
    assert hb.get_state() == "full"   # WO: > 0.95 is full


def test_drain_and_restore_clamped_to_unit_range():
    hb.drain(5.0)
    assert hb.get_energy() == 0.0
    hb.restore(5.0)
    assert hb.get_energy() <= 1.0


def test_restore_stops_at_full_threshold():
    hb.reset(cognitive=0.96)
    before = hb.get_energy()
    hb.restore(0.50)
    assert hb.get_energy() == before, "restored past ENERGY_FULL"


def test_negative_and_zero_amounts_are_no_ops():
    hb.drain(0)
    hb.drain(-1)
    hb.restore(0)
    hb.restore(-1)
    assert hb.get_energy() == 1.0


def test_state_thresholds_match_the_wo():
    hb.reset(cognitive=0.50)
    assert hb.get_state() == "normal"
    hb.reset(cognitive=0.20)
    assert hb.get_state() == "low"
    hb.reset(cognitive=0.05)
    assert hb.get_state() == "critical"
    hb.reset(cognitive=1.0)
    assert hb.get_energy() > hb.ENERGY_FULL and hb.get_state() == "full"


def test_conversation_turn_costs_match_the_wo():
    hb.reset()
    hb.on_conversation_turn(emotional_intensity=0.0)
    assert round(1.0 - hb.get_energy(), 4) == hb.DRAIN_CONVERSATION_TURN
    hb.reset()
    hb.on_conversation_turn(emotional_intensity=0.9)
    assert round(1.0 - hb.get_energy(), 4) == 0.006


def test_energy_history_keeps_last_twenty():
    for _ in range(30):
        hb.drain(0.001)
    assert len(hb.energy_history()) == hb.HISTORY_LEN


def test_dream_restore_amounts():
    hb.reset(cognitive=0.20)
    assert hb.on_wake_from_dream("NREM+REM") == 0.30
    assert hb.get_energy() == pytest.approx(0.50, abs=1e-6)
    hb.reset(cognitive=0.20)
    assert hb.on_wake_from_dream("NREM") == 0.12


def test_calm_tick_restores_at_spec_rate():
    hb.reset(cognitive=0.50)
    hb.calm_tick(60.0)   # one minute of calm
    assert hb.get_energy() == pytest.approx(0.508, abs=1e-3)


def test_idle_tick_is_metabolic_floor_only():
    hb.reset()
    hb.tick({})
    assert round(1.0 - hb.get_energy(), 5) == hb.DRAIN_IDLE_TICK


def test_walk_and_jump_animation_drain():
    hb.reset()
    hb.tick({"animation": "walk"})
    assert round(1.0 - hb.get_energy(), 4) == hb.DRAIN_WALK_TICK
    hb.reset()
    hb.tick({"animation": "jump"})
    assert round(1.0 - hb.get_energy(), 4) == hb.DRAIN_JUMP


# ── PART B — calm to sleep ─────────────────────────────────────────────────────

def test_calm_to_sleep_requires_low_energy_idle_and_cooldown():
    hb.reset(cognitive=0.20)
    assert hb.calm_to_sleep_ready(is_calm=True, idle_seconds=700, cooldown_elapsed=True)
    assert not hb.calm_to_sleep_ready(is_calm=False, idle_seconds=700, cooldown_elapsed=True)
    assert not hb.calm_to_sleep_ready(is_calm=True, idle_seconds=100, cooldown_elapsed=True)
    assert not hb.calm_to_sleep_ready(is_calm=True, idle_seconds=700, cooldown_elapsed=False)
    hb.reset(cognitive=0.90)
    assert not hb.calm_to_sleep_ready(is_calm=True, idle_seconds=700, cooldown_elapsed=True)


# ── ADDENDUM A — physical track ────────────────────────────────────────────────

def test_physical_track_stays_disengaged_on_desktop():
    """No motion reported -> elo_battery IS cognitive, thresholds unaffected."""
    hb.reset(cognitive=0.05)
    assert hb.get_physical() == 1.0
    assert hb.get_energy() == 0.05
    assert hb.get_state() == "critical"
    # Emitted but explicitly untracked — these keys are preserved across full
    # state writes, so omitting them would freeze stale values in live state.
    assert hb.snapshot()["physical_state"] == hb.PHYSICAL_UNTRACKED
    assert hb.snapshot()["physical_battery"] is None


def test_physical_engages_once_motion_is_reported():
    hb.reset()
    hb.tick({"physical": "walking"})
    snap = hb.snapshot()
    assert "physical_battery" in snap
    assert snap["physical_state"] in {s for _f, s in hb.PHYSICAL_STATES}
    assert snap["activity_recent"] == "walking"
    assert "activity_duration_minutes" in snap


def test_physical_tick_rates_match_the_addendum():
    for activity, rate in hb.PHYSICAL_TICK_RATES.items():
        hb.reset(physical=0.50)
        hb.tick({"physical": activity})
        delta = hb.get_physical() - 0.50
        assert delta == pytest.approx(rate, abs=1e-6), activity


def test_running_drains_faster_than_walking_than_standing():
    assert (abs(hb.PHYSICAL_TICK_RATES["running"])
            > abs(hb.PHYSICAL_TICK_RATES["walking"])
            > abs(hb.PHYSICAL_TICK_RATES["standing"]))


def test_jump_and_parkour_charge_once_per_event_not_per_tick():
    hb.reset()
    hb.tick({"physical": "jumping"})
    after_first = hb.get_physical()
    hb.tick({"physical": "jumping"})
    hb.tick({"physical": "jumping"})
    assert hb.get_physical() == after_first, "discrete event charged per tick"
    assert round(1.0 - after_first, 4) == hb.PHYSICAL_EVENT_COSTS["jumping"]


def test_explicit_jump_and_parkour_helpers_drain_both_tracks():
    hb.reset()
    hb.jump()
    assert hb.get_physical() < 1.0 and hb.get_cognitive() < 1.0
    hb.reset()
    hb.parkour_burst()
    assert round(1.0 - hb.get_physical(), 4) == hb.PHYSICAL_EVENT_COSTS["parkour"]


def test_sitting_and_lying_down_restore_physical():
    hb.reset(physical=0.30)
    hb.tick({"physical": "sitting"})
    assert hb.get_physical() > 0.30
    hb.reset(physical=0.30)
    hb.tick({"physical": "lying_down"})
    assert hb.get_physical() == pytest.approx(0.315, abs=1e-6)


def test_physical_state_bands_match_the_addendum():
    for value, expected in (
        (0.90, "rested"), (0.75, "rested"),
        (0.50, "normal"), (0.40, "normal"),
        (0.30, "tired"), (0.20, "tired"),
        (0.15, "fatigued"), (0.10, "fatigued"),
        (0.05, "exhausted"), (0.00, "exhausted"),
    ):
        hb.reset(physical=value)
        assert hb.get_physical_state() == expected, value


def test_exhausted_triggers_auto_calm():
    hb.reset()
    hb.drain_physical(0.95)
    assert hb.get_physical_state() == "exhausted"
    assert hb.should_auto_calm() is True


def test_physical_conditioning_carries_the_canonical_david_line():
    hb.reset()
    hb.drain_physical(0.85)       # -> 0.15, fatigued
    cond = hb.physical_conditioning(recovery_window_s=0.0)
    assert cond["physical_state"] == "fatigued"
    assert cond["response"] == (
        "I've been standing all day — let me sit for a bit to reset my legs.")
    assert cond["inner_thought"] == "Legs are heavy. Time to sit."


def test_physical_conditioning_is_none_when_body_has_nothing_to_say():
    hb.reset()
    assert hb.physical_conditioning() is None      # never engaged
    hb.tick({"physical": "standing"})
    assert hb.physical_conditioning(recovery_window_s=0.0) is None  # still rested


def test_high_intensity_recovery_conditioning_after_a_burst():
    hb.reset()
    hb.parkour_burst()
    cond = hb.physical_conditioning(recovery_window_s=300.0)
    assert cond["inner_thought"] == "That took it out of me."


def test_combined_battery_uses_both_tracks_once_engaged():
    hb.reset(cognitive=1.0)
    hb.drain_physical(0.50)
    expected = 1.0 * hb.WEIGHT_COGNITIVE + 0.50 * hb.WEIGHT_PHYSICAL
    assert hb.get_energy() == pytest.approx(round(expected, 3), abs=1e-3)


# ── PART D — game events ───────────────────────────────────────────────────────

def test_item_energy_values_match_the_wo():
    assert hb.item_energy("food") == 0.20
    assert hb.item_energy("unknown_widget") == hb.ITEM_ENERGY_DEFAULT
    crate = hb.item_energy("crate", rng=random.Random(1))
    assert hb.CRATE_RANGE[0] <= crate <= hb.CRATE_RANGE[1]


def test_game_events_consumed_once_and_cursor_persists(tmp_path, monkeypatch):
    events = tmp_path / "game_events.jsonl"
    cursor = tmp_path / "game_events_cursor.json"
    monkeypatch.setattr(hb, "GAME_EVENTS_PATH", events)
    monkeypatch.setattr(hb, "GAME_EVENTS_CURSOR", cursor)

    events.write_text(
        json.dumps({"type": "item_collected", "item": "food", "ts": 1.0}) + "\n"
        + json.dumps({"type": "item_collected", "item": "food", "ts": 2.0}) + "\n",
        encoding="utf-8",
    )

    hb.reset(cognitive=0.10)
    applied = hb.consume_game_events()
    assert [a["item"] for a in applied] == ["food", "food"]
    assert hb.get_energy() == pytest.approx(0.50, abs=1e-6)

    # second poll consumes nothing — cursor persisted
    assert hb.consume_game_events() == []
    assert hb.get_energy() == pytest.approx(0.50, abs=1e-6)
    assert json.loads(cursor.read_text())["line"] == 2


def test_malformed_and_unrelated_game_events_are_skipped(tmp_path, monkeypatch):
    events = tmp_path / "game_events.jsonl"
    monkeypatch.setattr(hb, "GAME_EVENTS_PATH", events)
    monkeypatch.setattr(hb, "GAME_EVENTS_CURSOR", tmp_path / "cursor.json")
    events.write_text(
        "not json\n"
        + json.dumps({"type": "something_else", "item": "food"}) + "\n"
        + json.dumps({"type": "item_collected", "item": "food"}) + "\n",
        encoding="utf-8",
    )
    hb.reset(cognitive=0.10)
    applied = hb.consume_game_events()
    assert len(applied) == 1


def test_missing_game_events_file_is_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(hb, "GAME_EVENTS_PATH", tmp_path / "nope.jsonl")
    assert hb.consume_game_events() == []


# ── PART A section 5 — blender_state output ────────────────────────────────────

def test_snapshot_always_carries_the_two_required_fields():
    snap = hb.snapshot()
    assert {"elo_battery", "elo_battery_state"} <= set(snap)
    assert 0.0 <= snap["elo_battery"] <= 1.0
    assert snap["elo_battery_state"] in ("full", "normal", "low", "critical")


def test_tick_returns_the_snapshot():
    assert hb.tick({}) == hb.snapshot()


def test_publish_is_best_effort_and_never_raises(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def boom(name, *args, **kwargs):
        if name == "blender_bridge.state_writer":
            raise ImportError("bridge unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", boom)
    assert hb.publish() is False


# ── Section 6 — hardware override ──────────────────────────────────────────────

def test_hardware_override_is_off_by_default():
    """Must not track the MacBook battery on desktop."""
    hb.reset(cognitive=0.42)
    assert hb.get_energy() == 0.42


def test_hardware_override_used_when_explicitly_enabled(monkeypatch):
    import sys
    import types

    fake = types.ModuleType("psutil")
    fake.sensors_battery = lambda: types.SimpleNamespace(percent=64.0)
    monkeypatch.setitem(sys.modules, "psutil", fake)
    monkeypatch.setenv(hb.HARDWARE_BATTERY_ENV, "1")

    hb.reset(cognitive=0.42)
    assert hb.get_energy() == 0.64


# ── Physical track engages only on a RECOGNISED activity ──────────────────────
# Regression: any non-empty string used to engage the track. physical then sat
# at 1.0 with no rate to drain it and elo_battery was floored at
# WEIGHT_PHYSICAL (0.4), making ENERGY_CRITICAL unreachable — silently killing
# the dream trigger, which is the exact failure the weighting exists to avoid.

@pytest.mark.parametrize("value", ["idle", "floating", "perched", "unknown", ""])
def test_unrecognised_motion_does_not_engage_physical(value):
    hb.reset()
    hb.tick({"physical": value})
    assert hb.get_physical() == 1.0
    assert hb.snapshot()["physical_state"] == hb.PHYSICAL_UNTRACKED


@pytest.mark.parametrize("value", sorted(hb.PHYSICAL_ACTIVITIES))
def test_every_recognised_activity_engages_physical(value):
    hb.reset()
    hb.tick({"physical": value})
    assert "physical_battery" in hb.snapshot()
    assert hb.snapshot()["activity_recent"] == value


def test_critical_stays_reachable_when_unity_reports_idle():
    """The floor bug: elo_battery could not drop below 0.4."""
    hb.reset(cognitive=0.05)
    hb.tick({"physical": "idle"})
    assert hb.get_state() == "critical"
    assert hb.get_energy() < hb.ENERGY_CRITICAL


def test_activity_vocabulary_covers_rates_and_events():
    assert hb.PHYSICAL_ACTIVITIES == (
        frozenset(hb.PHYSICAL_TICK_RATES) | frozenset(hb.PHYSICAL_EVENT_COSTS)
    )
    for name in ("standing", "walking", "running", "sitting",
                 "lying_down", "sleeping", "jumping", "parkour"):
        assert name in hb.PHYSICAL_ACTIVITIES


# ── Cognitive drain must be cadence-independent ───────────────────────────────
# Live defect 2026-09-27: _tick_cognitive applied the full per-tick constant
# every tick while _tick_physical scaled by elapsed time. At the ambient
# loop's 0.5s poll that doubled every cognitive rate, and idle drained
# 0.0004/s = 1.44/hour — a full battery gone in 41 minutes of doing nothing.
# Observed live: server up 68 min, elo_battery 0.0 "critical".

def test_idle_drain_is_the_same_per_second_at_any_poll_rate():
    hb.reset()
    for _ in range(60):
        hb.tick({}, dt_seconds=1.0)
    slow = hb.get_cognitive()

    hb.reset()
    for _ in range(120):
        hb.tick({}, dt_seconds=0.5)
    fast = hb.get_cognitive()

    assert slow == pytest.approx(fast, abs=1e-6), (
        "idle drain depends on poll cadence"
    )


def test_walk_drain_is_the_same_per_second_at_any_poll_rate():
    hb.reset()
    for _ in range(30):
        hb.tick({"animation": "walk"}, dt_seconds=1.0)
    slow = hb.get_cognitive()

    hb.reset()
    for _ in range(60):
        hb.tick({"animation": "walk"}, dt_seconds=0.5)
    assert slow == pytest.approx(hb.get_cognitive(), abs=1e-6)


def test_idle_metabolic_floor_does_not_flatten_the_battery_in_an_hour():
    """A 'base metabolic drain only' floor must not empty eLo while idle."""
    hb.reset()
    for _ in range(3600):
        hb.tick({}, dt_seconds=1.0)          # one hour of pure idle
    assert hb.get_energy() > hb.ENERGY_LOW, (
        f"one idle hour took the battery to {hb.get_energy()}"
    )


def test_jump_animation_held_across_ticks_charges_once():
    hb.reset()
    for _ in range(6):
        hb.tick({"animation": "jump"}, dt_seconds=0.5)
    assert round(1.0 - hb.get_cognitive(), 4) == hb.DRAIN_JUMP


def test_separate_jumps_each_charge():
    hb.reset()
    hb.tick({"animation": "jump"}, dt_seconds=0.5)
    hb.tick({"animation": "idle"}, dt_seconds=0.5)
    hb.tick({"animation": "jump"}, dt_seconds=0.5)
    drained = 1.0 - hb.get_cognitive()
    assert drained > hb.DRAIN_JUMP * 1.9


def test_physical_fields_are_always_emitted_so_they_cannot_go_stale():
    """
    They are in state_writer._PRESERVE_KEYS, so a key written once survives
    every later full state write. Observed live: physical_battery 0.7 /
    physical_state normal frozen in blender_state.json while the track was
    not being driven at all.
    """
    keys = {"physical_battery", "physical_state",
            "activity_recent", "activity_duration_minutes"}
    hb.reset()
    assert keys <= set(hb.snapshot()), "disengaged snapshot omits physical keys"
    hb.tick({"physical": "walking"})
    assert keys <= set(hb.snapshot()), "engaged snapshot omits physical keys"


def test_untracked_is_distinct_from_rested():
    """'no body signal' and 'a rested body' are different claims."""
    hb.reset()
    assert hb.snapshot()["physical_state"] == hb.PHYSICAL_UNTRACKED
    assert hb.PHYSICAL_UNTRACKED not in {s for _f, s in hb.PHYSICAL_STATES}
    hb.tick({"physical": "standing"})
    assert hb.snapshot()["physical_state"] == "rested"
