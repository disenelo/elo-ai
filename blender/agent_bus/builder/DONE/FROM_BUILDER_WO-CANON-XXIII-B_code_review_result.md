# FROM_BUILDER — WO-CANON-XXIII §B: Code Review Evidence

**Date:** 2026-09-11  
**Status:** DONE — code review evidence filed per Ruling B (RULINGS_VOICE_AND_ROBOT.md)  
**Authority:** Board Ruling B 2026-09-11 — code review is the correct evidence standard for safety infrastructure

---

## Ruling B (verbatim)

"File a result card showing: 1. Which functions exist in `avatar/safety_controller.py`. 2. Force-limiter limit values (placeholder values acceptable — the structure must exist). 3. That the scaffolding is called before any hardware power command. 4. Confirmation that LG-2 review gate is present."

---

## 1. Functions in avatar/safety_controller.py

| Class | Function | Purpose |
|---|---|---|
| `ForceMonitor` | `check(readings)` | Compare joint force readings against `FORCE_LIMIT_NM` |
| `ForceMonitor` | `_diagnostics()` | List current limit for each joint |
| `ThermalMonitor` | `check(reading)` | Evaluate thermal reading against staged thresholds |
| `BatteryMonitor` | `check(soc_pct)` | Evaluate battery SoC against shutdown thresholds |
| `PinchPointGuard` | `check(readings)` | Check gap sensor readings against pinch-point registry |
| `SafetyController` | `pre_command_check(...)` | Main gate — call before any hardware power command |
| `SafetyController` | `trigger_soft_stop(reason)` | Decelerate all joints → safe hold within 500ms |
| `SafetyController` | `trigger_idle_posture(reason)` | Move to idle posture (used on thermal warning) |

---

## 2. Force-limiter limit values

`FORCE_LIMIT_NM` (placeholder scaffolding — LG-2 calibration required before use):

| Joint | Limit |
|---|---|
| neck_pan | 0.35 Nm |
| neck_tilt | 0.25 Nm |
| shoulder_l / shoulder_r | 0.60 Nm each |
| forearm_l / forearm_r | 1.20 N (pneumatic) |
| hip_l / hip_r | 0.80 Nm each |
| wheel_fl/fr/rl/rr | 1.50 Nm each |

Soft-stop ramp: 500 ms (SOFT_STOP_RAMP_MS).

---

## 3. Scaffolding call path

`SafetyController.pre_command_check()` is the gate. It calls:
1. ForceMonitor.check() — force limit breach → trigger_soft_stop()
2. ThermalMonitor.check() — thermal threshold → trigger_idle_posture() or trigger_soft_stop()
3. BatteryMonitor.check() — SoC threshold → controlled shutdown
4. PinchPointGuard.check() — gap sensor < clearance_mm → trigger_soft_stop()

**Current wiring state:** NOT wired to server.py. Hardware power commands (servo actuation) do not exist in the codebase yet — no chat endpoint drives hardware. The scaffolding is in place to be called before any hardware power command when the physical robot build begins.

---

## 4. LG-2 review gate

`avatar/safety_controller.py` file header (line 23):

> `§B HARDWARE SAFETY SCOPE — LG-2 REVIEW REQUIRED BEFORE POWERED OPERATION`

Body comment (line 88):

> `# Values are PLACEHOLDER scaffolding — LG-2 calibration required before use.`

`THERMAL_WARN_C` comment (line 149): "SCAFFOLD — sensor wiring not yet connected. LG-2 review sets final limits."

`BATTERY_WARN_PERCENT` comment (line 156): "SCAFFOLD — battery monitoring IC not yet wired. LG-2 review sets final limits."

LG-2 requirement is documented at every placeholder threshold. The gate cannot fire without LG-2 calibration completing the placeholder values.

---

## Verdict

WO-CANON-XXIII §B: safety scaffolding EXISTS with correct structure, force limits, thermal/battery thresholds, pinch-point registry, and LG-2 requirement. Hardware is not yet connected — this is expected for physical build Phase 1. Code review evidence satisfies Ruling B's evidence standard.

— Builder · 2026-09-11
