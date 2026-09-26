# WO-HEALTH-BATTERY-001 + ADDENDUM A — build evidence

**Filed by:** Builder 2 · 2026-09-26
**Slice:** S4 (START_HERE_B2.md)
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` — Python 3.13.13, pytest 9.1.1
**Commit:** `644876d`

---

## STATE (TESTING_STANDARD state machine)

```
MISSING → IMPLEMENTED → WIRED → TESTED → LIVE VERIFIED → BOARD VERIFIED → RELEASED
                ^^^^^^^^^^^^           ^^^^^^
                reached                unit only
```

- **IMPLEMENTED** — `core/health_battery.py`, full API.
- **TESTED** — unit level only, 34 tests.
- **NOT WIRED** — nothing calls it. Tier 3 (REAL RUNTIME PATH) of the 7-tier
  standard is **NOT** satisfied. Every integration point below is outstanding:
  - `server.py` ambient loop → `tick(motion_state)` — NOT DONE
  - after each conversation turn → `on_conversation_turn()` — NOT DONE
  - `dream_faculty.wake_from_dream()` → `on_wake_from_dream()` — NOT DONE
  - calm mode tick → `calm_tick()` — NOT DONE
  - `should_dream()` → `get_energy()` replacing `energy_history` — NOT DONE
  - `blender_state.json` write each tick → `publish()` — NOT DONE
- **NOT LIVE VERIFIED** — no live server run, no Pi hardware run.

All six wiring points live in `server.py` / `dream_faculty.py`. `server.py`
is Builder 1's file for COG-004 RR20 and the Builder 2 brief sequences it
last. RR20 has since landed (`3e8dd0c`), so these are unblocked and
outstanding, not blocked.

**Do not read this file as PASS.** Board crosschecks.

---

## THREE BUILDER DECISIONS — flagged for confirmation

### 1. Combination weights (ADDENDUM A left these "TBD by Builder")

The physical track is folded into `elo_battery` **only once motion has
actually been reported**. Rationale: on desktop there is no motion sensor, so
`physical_battery` sits at 1.0. Averaging it in unconditionally at any fixed
weight would floor `elo_battery` and make `ENERGY_CRITICAL` (0.10)
unreachable on desktop — silently breaking the parent WO's dream trigger.

- No motion reported → `elo_battery` **IS** `cognitive_battery`.
- Motion reported → `0.6 × cognitive + 0.4 × physical`.

Observed: section A below reaches `critical` at 0.08 on desktop. Section D
shows the physical fields appearing only after motion is reported.

### 2. Hardware override gated, default OFF

WO PART A section 6 says `psutil.sensors_battery()` overrides the simulated
value "on Pi". Applied literally that also fires on David's MacBook, and
eLo's energy would track the laptop charge. Gated behind
`ELO_HARDWARE_BATTERY=1`, default off. The robot opts in; the desktop does
not. Test `test_hardware_override_is_off_by_default` pins this.

### 3. jumping / parkour charged per event, not per tick

The addendum specifies `−0.015 per jump` and `−0.020 per burst` — discrete
events. Charged on the transition INTO the activity. A tick loop sitting in
`"jumping"` for 30 frames would otherwise drain 0.45. Observed in section F.

---

## ONE DEFECT FOUND IN MY OWN CODE DURING TESTING

Getters rounded to 3 decimal places, which erased every rate below 0.001 —
that is most of the spec's per-tick rates (`idle −0.0002`,
`standing −0.0015`). A single idle tick was invisible. Getters now carry 4dp;
`snapshot()` rounds to 3dp for the wire. Caught by
`test_idle_tick_is_metabolic_floor_only` and
`test_physical_tick_rates_match_the_addendum`.

---

## ACCEPTANCE — WO PART A/B/D

| Criterion | Status |
|---|---|
| `core/health_battery.py` created with full API | DONE |
| `server.py` calls `tick()` each ambient loop | **NOT DONE** — server.py |
| `blender_state.json` includes elo_battery + state | `snapshot()`/`publish()` built, **NOT CALLED** |
| Calm mode tick wires restore rate | `calm_tick()` built, **NOT CALLED** |
| Calm → sleep transition threshold active | `calm_to_sleep_ready()` built, **NOT CALLED** |
| Dream faculty uses `get_energy()` for exhaustion | **NOT DONE** — dream_faculty.py |
| Game events consumed correctly | DONE — section below |
| Robot: `psutil` hardware override works on Pi | Implemented + unit tested with a fake psutil. **NOT verified on Pi hardware** |
| Commit hash filed | `644876d` |

## ACCEPTANCE — ADDENDUM A

| Criterion | Status |
|---|---|
| `physical_battery` separate from cognitive | DONE |
| `physical_state` written to blender_state each tick | in `snapshot()`, **NOT CALLED** |
| standing/walking/running/jumping/parkour/sitting rates | DONE — section D/F/G |
| `activity_recent` + `activity_duration_minutes` | DONE — see note below |
| Physical state feeds `inner_thought` conditioning | `physical_conditioning()` built, **NOT CONSUMED** — needs WO-INNER-THOUGHTS-001 Phase 2 |
| Designer: seated posture, recovery animation | Designer lane — not Builder |
| On `"exhausted"`: calm mode auto-triggers | `should_auto_calm()` built, **NOT CALLED** |
| Commit hash filed | `644876d` |

**Note on `activity_duration_minutes`:** reads `0.0` in section D because all
600 simulated ticks ran inside the same wall-clock second. It measures real
elapsed time, so it is correct under a real 1 Hz ambient loop. Not verified
against a real loop.

---

## COMMAND OUTPUT — verbatim

### Runtime simulation

```
=== A. COGNITIVE DRAIN / THRESHOLDS (desktop, no motion sensor) ===
start                      elo_battery=1.0  state=full
turn 1 (intensity 0.9)    elo_battery=0.994  state=full
turn 2 (intensity 0.0)    elo_battery=0.99  state=full
turn 3 (intensity 0.9)    elo_battery=0.984  state=full
turn 4 (intensity 0.0)    elo_battery=0.98  state=full
turn 5 (intensity 0.9)    elo_battery=0.974  state=full

cognitive=0.26             state=normal
after drain 0.02           elo_battery=0.24  state=low  (LOW=0.25)
after drain 0.16           elo_battery=0.08  state=critical  (CRITICAL=0.1)
snapshot                   {'elo_battery': 0.08, 'elo_battery_state': 'critical'}
  ^ physical fields absent — physical track not engaged on desktop

=== B. DREAM RESTORE (WO PHASE 11) ===
before                     elo_battery=0.08  state=critical
wake NREM+REM (+0.3)     elo_battery=0.38  state=normal
wake NREM only (+0.12)    elo_battery=0.2  state=low

=== C. CALM MODE + CALM->SLEEP TRANSITION (PART B) ===
 1 min calm              elo_battery=0.208
 5 min calm              elo_battery=0.24
10 min calm              elo_battery=0.28
calm+low+idle700+cooldown  sleep_ready=True
same but not calm          sleep_ready=False
calm but energy 0.90       sleep_ready=False

=== D. PHYSICAL TRACK — 'standing all day' (ADDENDUM A) ===
tick    1  physical=0.9985  physical_state=rested
tick  167  physical=0.7495  physical_state=normal
tick  401  physical=0.3985  physical_state=tired
tick  534  physical=0.1990  physical_state=fatigued
snapshot                   {'elo_battery': 0.568, 'elo_battery_state': 'normal', 'physical_battery': 0.1, 'physical_state': 'fatigued', 'activity_recent': 'standing', 'activity_duration_minutes': 0.0}
conditioning inner_thought : Legs are heavy. Time to sit.
conditioning response      : I've been standing all day — let me sit for a bit to reset my legs.
auto_calm                  : False  should_auto_calm=False

=== E. HIGH-INTENSITY BURST ===
after parkour burst        physical=0.98  cognitive=0.992
conditioning inner_thought : That took it out of me.
conditioning response      : That changed my energy levels — need a moment.

=== F. JUMP CHARGED PER EVENT, NOT PER TICK ===
tick 1 physical=0.985
tick 2 physical=0.985
tick 3 physical=0.985
  ^ one charge on entry, flat thereafter

=== G. SITTING RESTORES ===
start                      physical=0.12  state=fatigued
tick  30                  physical=0.3600  state=tired
tick  60                  physical=0.6000  state=normal
tick 120                  physical=1.0000  state=rested
```

### Game events consumed (PART D)

```
before            elo_battery=0.1
  consumed food         +0.2
  consumed crate        +0.159
  consumed mystery_box  +0.1
after             elo_battery=0.559
second poll       []   <- cursor persisted, nothing re-applied
cursor file       {"line": 3}
```

### pytest — verbatim, not truncated

```
============================= test session starts ==============================
platform darwin -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- /Users/Disenelo/miniconda3/bin/python3
cachedir: .pytest_cache
rootdir: /Users/Disenelo/elo-ai
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 34 items

tests/test_health_battery.py::test_starts_full PASSED                    [  2%]
tests/test_health_battery.py::test_drain_and_restore_clamped_to_unit_range PASSED [  5%]
tests/test_health_battery.py::test_restore_stops_at_full_threshold PASSED [  8%]
tests/test_health_battery.py::test_negative_and_zero_amounts_are_no_ops PASSED [ 11%]
tests/test_health_battery.py::test_state_thresholds_match_the_wo PASSED  [ 14%]
tests/test_health_battery.py::test_conversation_turn_costs_match_the_wo PASSED [ 17%]
tests/test_health_battery.py::test_energy_history_keeps_last_twenty PASSED [ 20%]
tests/test_health_battery.py::test_dream_restore_amounts PASSED          [ 23%]
tests/test_health_battery.py::test_calm_tick_restores_at_spec_rate PASSED [ 26%]
tests/test_health_battery.py::test_idle_tick_is_metabolic_floor_only PASSED [ 29%]
tests/test_health_battery.py::test_walk_and_jump_animation_drain PASSED  [ 32%]
tests/test_health_battery.py::test_calm_to_sleep_requires_low_energy_idle_and_cooldown PASSED [ 35%]
tests/test_health_battery.py::test_physical_track_stays_disengaged_on_desktop PASSED [ 38%]
tests/test_health_battery.py::test_physical_engages_once_motion_is_reported PASSED [ 41%]
tests/test_health_battery.py::test_physical_tick_rates_match_the_addendum PASSED [ 44%]
tests/test_health_battery.py::test_running_drains_faster_than_walking_than_standing PASSED [ 47%]
tests/test_health_battery.py::test_jump_and_parkour_charge_once_per_event_not_per_tick PASSED [ 50%]
tests/test_health_battery.py::test_explicit_jump_and_parkour_helpers_drain_both_tracks PASSED [ 52%]
tests/test_health_battery.py::test_sitting_and_lying_down_restore_physical PASSED [ 55%]
tests/test_health_battery.py::test_physical_state_bands_match_the_addendum PASSED [ 58%]
tests/test_health_battery.py::test_exhausted_triggers_auto_calm PASSED   [ 61%]
tests/test_health_battery.py::test_physical_conditioning_carries_the_canonical_david_line PASSED [ 64%]
tests/test_health_battery.py::test_physical_conditioning_is_none_when_body_has_nothing_to_say PASSED [ 67%]
tests/test_health_battery.py::test_high_intensity_recovery_conditioning_after_a_burst PASSED [ 70%]
tests/test_health_battery.py::test_combined_battery_uses_both_tracks_once_engaged PASSED [ 73%]
tests/test_health_battery.py::test_item_energy_values_match_the_wo PASSED [ 76%]
tests/test_health_battery.py::test_game_events_consumed_once_and_cursor_persists PASSED [ 79%]
tests/test_health_battery.py::test_malformed_and_unrelated_game_events_are_skipped PASSED [ 82%]
tests/test_health_battery.py::test_missing_game_events_file_is_not_an_error PASSED [ 85%]
tests/test_health_battery.py::test_snapshot_always_carries_the_two_required_fields PASSED [ 88%]
tests/test_health_battery.py::test_tick_returns_the_snapshot PASSED      [ 91%]
tests/test_health_battery.py::test_publish_is_best_effort_and_never_raises PASSED [ 94%]
tests/test_health_battery.py::test_hardware_override_is_off_by_default PASSED [ 97%]
tests/test_health_battery.py::test_hardware_override_used_when_explicitly_enabled PASSED [100%]

============================== 34 passed in 0.09s ==============================
```
