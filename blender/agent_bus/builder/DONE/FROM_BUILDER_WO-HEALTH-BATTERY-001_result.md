# WO-HEALTH-BATTERY-001 — Result: eLo Health Battery (S4)

**Date:** 2026-09-26 / 27
**WO:** WO-HEALTH-BATTERY-001 PART A/B/D + ADDENDUM A (Physical Activity)
**Source:** `blender/agent_bus/builder/FROM_ARCHITECT_2026-09-22_HEALTH_BATTERY.md`
· `_intake/SOURCE_2026-09-24_DAVID_physical_activity_energy.md`
**Seat:** Builder 2
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` — 3.13.13, pytest 9.1.1
**Evidence:** `engineering/evidence/HEALTH/WO-HEALTH-BATTERY-001-ADDENDUM-A_evidence.md`

**STATUS: PARTIAL** — module built, all six integration points wired.
Nothing LIVE VERIFIED. Robot path never run on hardware.

---

## REQUESTED

`core/health_battery.py` with the full drain/restore/tick API, the physical
fatigue track from Addendum A, and six integration points.

## CHANGED

| Commit | File | What |
|---|---|---|
| `644876d` | `core/health_battery.py` | new — PART A/B/D + Addendum A |
| `9c69801` | `server.py:3678` | per-turn drain + publish |
| `8bb9a90` | `faculties/dream/dream_faculty.py` | `should_dream()` reads the battery |
| `963e5f4` | `faculties/dream/dream_faculty.py` | wake restores +0.30 / +0.12 |
| `967793f` | `ambient/ambient_engine.py` | battery tick on the 0.5s poll loop |
| `6d62e96` | `blender_bridge/state_writer.py` | battery fields survive a full state write |
| `274a980` | `tests/` | stop the suite writing to live state |

### Integration points

| WO point | Where | Commit |
|---|---|---|
| ambient loop → `tick(motion_state)` | `ambient_engine.py` 0.5s poll | `967793f` |
| after each turn → `on_conversation_turn()` | `server.py:3678` | `9c69801` |
| `wake_from_dream()` → restore | `dream_faculty.py` | `963e5f4` |
| calm tick → `calm_tick()` | inside `_battery_tick()` | `967793f` |
| `should_dream()` → `get_energy()` | `dream_faculty.py` | `8bb9a90` |
| `blender_state.json` each tick → `publish()` | ambient + per turn | `967793f` / `9c69801` |

## TEST RESULTS

```
test_health_battery                     49 passed
test_s4_battery_wiring                   6 passed
test_s4_should_dream_battery             8 passed
test_s4_wake_restore                     8 passed
test_s4_ambient_tick                     9 passed
test_state_writer_preserves_battery     12 passed
test_no_live_state_writes                5 passed
                                        -----------
                                        97 passed
```

`state_writer.py` is shared, so every dependent suite was re-run after
`6d62e96`: `test_wo_mobile_phase2_preserve_keys`, `test_fa_preserve_keys`,
`test_sp38_target_registry`, `test_lifecycle`, `test_wo_unity_gaze` — 36
passed; plus `test_wo064_move_words`, `test_wo_pres004b_nav_fail_state_write`,
`test_canon_xiii_spatial`, `test_canon_xi_motor`,
`test_wo064_conversing_field` — all PASS.

## LIVE EVIDENCE

**NONE.** Tier 5 is not satisfied. Server PID 28626 is on pre-fix code; a
restart was attempted and correctly refused by the host permission layer.

Observed out of process, verbatim in the evidence file: cognitive drain and
thresholds, dream restore (0.10 → 0.40 full cycle / 0.22 NREM), calm restore,
the "standing all day" arc reaching `fatigued` and emitting David's verbatim
line, per-event jump/parkour charging, sitting restore, and game events
(`food +0.20`, `crate +0.159` randomised, unknown `+0.10`, cursor persisted).

## THE ONE THAT WOULD HAVE BITTEN — `6d62e96`

With all six points wired but before this fix, **S4 would have appeared to
work and then visibly failed in front of David.**

`state_writer._write()` REPLACES `blender_state.json` wholesale, keeping only
`_PRESERVE_KEYS`. `publish()` writes via `patch()` (a merge), so the fields
landed — and the next full `_write()` deleted them. The ambient tick
republishes every 0.5s, so the indicator would have flickered on and off with
nothing wrong in Unity. Designer would have debugged their own code.

The file documents the trap — *"absent from this set = droppable"* — and
WO-MOBILE-PHASE2 hit it first and fixed it the same way.

## A TEST SUITE WAS WRITING INTO THE RUNNING SYSTEM — `274a980`

Live `elo_battery` read `0.4` when it had been set to `1.0` by hand.
`test_s4_wake_restore.py` → `wake_from_dream()` → real `publish()` → live
`blender_state.json`. `0.4` is exactly `0.10 + 0.30` from
`test_full_cycle_restores_thirty`.

Had it not been caught, the live-evidence run would have captured values this
suite had partly written and filed them as a live result. Guard added:
`tests/test_no_live_state_writes.py`.

## THE SECOND ONE THAT WOULD HAVE BITTEN — `e6edd9d`

Found by self-review of my own diff, not by a test.

`_tick_physical()` engaged the physical track on **any** non-empty motion
string. Unity writing `physical="idle"` — or `"floating"`, `"perched"`, or
anything added later — engaged it permanently. Those values have no entry in
`PHYSICAL_TICK_RATES`, so physical sat at 1.0 with nothing to drain it, and
`elo_battery` became `0.6*cognitive + 0.4*1.0`.

That **floors `elo_battery` at 0.4**. `ENERGY_CRITICAL` is 0.10, so it becomes
unreachable and the dream trigger dies silently — the exact failure the
combination-weight decision above was written to prevent. The guard was
defeated by any unrecognised string.

Not theoretical: live state already carries `motion.mode="idle"` and
`state.pose="standing"`, so an `"idle"` physical value is a plausible thing
for Unity to send.

Fix: `PHYSICAL_ACTIVITIES`, derived from
`PHYSICAL_TICK_RATES | PHYSICAL_EVENT_COSTS` so it cannot drift from the rate
tables. Anything outside it is ignored. Verified `CRITICAL` reachable again
(0.0498) with `physical="idle"`.

---

## DECISIONS NEEDING BOARD CONFIRMATION

1. **Combination weights** were "TBD by Builder". Physical folds into
   `elo_battery` **only once motion is reported**. On desktop there is no
   motion sensor, so physical sits at 1.0; averaging it in unconditionally
   would floor `elo_battery` and make `ENERGY_CRITICAL` (0.10) unreachable,
   silently breaking the parent WO's dream trigger. No motion → `elo_battery`
   IS cognitive. 0.6 / 0.4 once live.
2. **Hardware override gated** behind `ELO_HARDWARE_BATTERY=1`, default OFF.
   Section 6 applied literally also fires on David's MacBook and eLo's energy
   would track the laptop charge.
3. **Tick location.** PART A.1 says "server's ambient loop", but
   `ambient_thought()` is the ambient *callback* and fires every 8–20 minutes
   — it cannot carry a per-minute rate. The tick went on the ambient engine's
   0.5s poll loop. Confirm or relocate.
4. **`emotional_intensity` has no source.** `emotional_context` carries
   `energy` and `valence`, no intensity field. `energy` used as the magnitude.
5. **All Addendum A rates are `[ESTIMATE]`** per the addendum itself.

## KNOWN, NOT FIXED

**`drain()` / `restore()` are not lock-guarded.** The ambient thread ticks the
battery every 0.5s while a request thread drains it per turn. Both do a
read-modify-write on a module-level float, so a concurrent pair can lose one
update. Consequence is a very occasional missed 0.004 drain — harmless, and
adding a lock was not asked for. Flagging rather than fixing.

## ⚠ NOTE FOR DESIGNER

`state.energy` (live, 0.35) is **not** the battery. It is
`attention_model.emotional_context.energy` — David's conversational affect,
also feeding `presence_plan.voice_energy`. eLo's battery is the new
top-level **`elo_battery`**. Binding the indicator to `state.energy` will look
plausible and be wrong. `test_battery_is_not_wired_into_state_energy` pins
them apart.

Related: `should_dream()` was deciding whether *eLo* needed sleep by reading
*David's* energy history. That is now eLo's own battery.

## REMAINING

- LIVE VERIFICATION — needs a server restart (David).
- Pi hardware path never run on hardware.
- Designer: battery indicator + calm animation (Part C).
- Game: `game_events.jsonl` writes on item collection (Part D) — the reader
  is built and tested, nothing writes the file yet.

## BUILDER STATUS

**PARTIAL.** Built, wired, unit-tested, evidence filed. Not live verified.
Not declaring PASS — Board crosschecks.

---

# UPDATE — 2026-09-28: partially LIVE VERIFIED, and three defects

## LIVE VERIFIED

Confirmed on the running server: `elo_battery` and `elo_battery_state`
writing every 0.3s, `physical_state` reporting `untracked` rather than a
frozen stale value, `calm_mode` published for Designer.

That closes tier 5 for the battery fields themselves.

## Three defects the live run exposed

**1. Cadence — `ff98065`.** `_tick_physical` scaled by elapsed time,
`_tick_cognitive` did not, so every cognitive rate was a function of the poll
interval. At 0.5s the idle "metabolic floor" ran at 1.44/hour and emptied a
full battery in 41 minutes. Observed: server up 68 min, `elo_battery` 0.0.
Rates are now per-second and cadence-independent; `jump` is per event.

**2. Two tickers — `ea2d8c5`.** `server.py:947` and `ambient_engine` both
ticked the same module-level battery (`f7a597e` and `967793f`, same day,
neither aware of the other). server.py owns it now.

**3. Idle from "now" — `b9f29fe`.** The one that actually kept eLo at zero.
`last_user_ts` is absent on a fresh server and every reader defaulted to
`time.time()`, so idle read 0.0 forever and hard-idle restore never fired.
Four instances; the fourth was found by my own test being broader than my
fix.

## Also fixed

**Stale physical fields — `ac994f2`.** Preserved keys that are only
conditionally emitted freeze. `physical_state` now always emitted, reporting
`untracked` when no body signal exists — a different claim from "rested".

**Unrecognised motion engaged the physical track — `e6edd9d`.** Any non-empty
string engaged it, so `physical="idle"` pinned physical at 1.0 and floored
`elo_battery` at 0.4, making `ENERGY_CRITICAL` unreachable and silently
killing the dream trigger. `PHYSICAL_ACTIVITIES` is now derived from the rate
tables so it cannot drift.

## Still open

- **Calibration is yours.** Rates are correct and cadence-independent; the
  absolute values are all `[ESTIMATE]` per the addendum. Whether eLo should
  get sleepy after an idle hour is a feel decision.
- Pi hardware path never run on hardware.
- Designer: battery indicator + calm animation.
- Game: nothing writes `game_events.jsonl` yet; the reader is built and tested.
