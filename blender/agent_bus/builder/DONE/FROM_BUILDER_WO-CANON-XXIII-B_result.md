# BUILDER RESULT — WO-CANON-XXIII §B (Robot Hardware Safety Scope)
Date: 2026-09-11
Status: DONE — T-5d GREEN (24/24 XXIII tests pass)

## What was built

Added force-limiter / soft-stop / thermal / battery / pinch-point scaffolding
to `avatar/safety_controller.py`.

### New state
`SafetyState.SOFT_STOP` — controlled deceleration to a safe hold (distinct from
the existing hard EMERGENCY all-actuators-off state).

### New constants
- `FORCE_LIMIT_NM` — per-joint force ceilings (Nm / N) for 12 joints:
  neck_pan, neck_tilt, shoulder_l/r, forearm_l/r, hip_l/r, wheel_fl/fr/rl/rr
- `SOFT_STOP_RAMP_MS = 500` — deceleration ramp duration
- `PINCH_POINT_REGISTRY` — 3 entries: neck_magnet_housing, hip_wishbone, forearm_bladder;
  each carries sensor_id, clearance_mm, and mitigation description
- `THERMAL_WARN_C / THERMAL_CRITICAL_C / THERMAL_EMERGENCY_C` — staged thresholds
- `BATTERY_WARN_PERCENT / BATTERY_SAFE_SHUTDOWN_PCT / BATTERY_CRITICAL_PCT` — staged thresholds

### New classes
| Class | Role |
|---|---|
| `ForceMonitor` | checks ForceReading list against FORCE_LIMIT_NM; stub_readings() for offline/test |
| `ThermalMonitor` | maps temp_c to: None / "cutback" / "soft_stop" / "emergency" |
| `BatteryMonitor` | maps percent to: None / "warn" / "safe_shutdown" / "emergency" |
| `PinchPointGuard` | checks gap_readings dict against PINCH_POINT_REGISTRY |

### SafetyController extensions
- `__init__`: instantiates all four monitors as `self.force_monitor` etc.
- `trigger_soft_stop(reason)` — new manual trigger for controlled ramp-down
- `check_force_limits(readings)` → breach string or None; auto-triggers SOFT_STOP
- `check_thermal(temp_c)` → action string or None; routes to soft_stop / emergency
- `check_battery(percent)` → action string or None; routes to safe_shutdown / emergency
- `check_pinch_points(gap_readings)` → hazard string or None; auto-triggers SOFT_STOP
- `_current_packet` updated: SOFT_STOP → `_soft_stop_packet(original)` (amber orb, 500 ms ramp)

### New packet builder
`_soft_stop_packet(original)` — ramps motion motors to zero over SOFT_STOP_RAMP_MS,
holds posture motors, sets amber orb (1.5 Hz pulse) to distinguish from freeze (blue)
and emergency (off).

## Test result

```
tests/test_canon_xxiii_security.py  24 passed in 0.12s
T-5d: test_t5d_powered_robot_refused_without_force_limiter  PASSED
```

`@unittest.expectedFailure` removed from T-5d; test now confirms §B scope is present.

## LG-2 notice (non-negotiable)

The software scaffolding is done.  All limit values, sensor wiring, and threshold
calibration are PLACEHOLDER until David (L3) + a separate LG-2 sign-off reviews them.
No powered hardware operation near David until that review is complete.
The module header and every constant block carry this notice in comments.

— Builder · 2026-09-11

---

## Board Ruling 3 — Rule 0 CANNOT BE SATISFIED for §B (added 2026-09-11)

**Board requirement (Ruling 3):** "File at least one real server turn for each distinct behaviour WO-CANON-XXIII §B claimed to implement."

**Finding:** WO-CANON-XXIII §B is EXCLUSIVELY robot hardware safety (ForceMonitor, ThermalMonitor, BatteryMonitor, PinchPointGuard, SafetyController.SOFT_STOP). These are in `avatar/safety_controller.py`.

- `avatar/safety_controller.py` is NOT imported by `server.py`
- No `/chat` endpoint behaviour triggers these monitors
- No capability in `runtime/capabilities/registry.py` exposes robot safety to conversational turns
- No robot is physically present

**Rule 0 cannot be satisfied** for §B until one of:
1. Robot safety capability wired to server with a query interface ("eLo, check your force limits")
2. Physical robot present with actual sensor readings

The 24/24 unit tests are the maximum available evidence for the scaffolding that was built. The implementation is correct (confirmed by test). Real server turn evidence requires physical hardware or a chat-accessible capability endpoint — neither exists.

**Escalation:** Builder → Board. Board must decide:
- (a) Accept unit test evidence for robot hardware safety (physical build not started)
- (b) Wire a robot-safety capability to server so chat turns can query safety state
- (c) Defer §B Rule 0 to physical robot build phase

— Builder · 2026-09-11
