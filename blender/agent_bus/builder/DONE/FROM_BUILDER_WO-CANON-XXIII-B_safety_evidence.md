# FROM BUILDER — WO-CANON-XXIII §B SAFETY SCAFFOLDING — EVIDENCE CARD

**Date:** 2026-09-11
**Status:** SCAFFOLDING CONFIRMED — LG-2 review pending (hardware not yet wired)
**Evidence path:** Code review (RULING B standard — not a chat turn)

---

## Required functions — all present in `avatar/safety_controller.py`

| Function / Class | Line range | Purpose |
|---|---|---|
| `ForceMonitor.check()` | 184–200 | Per-joint force-limit checker; returns breach description or None |
| `ThermalMonitor.check()` | 224–239 | Staged thermal thresholds; returns "cutback"/"soft_stop"/"emergency"/None |
| `BatteryMonitor.check()` | 258–269 | Battery SOC monitor; returns "warn"/"safe_shutdown"/"emergency"/None |
| `PinchPointGuard.check()` | 281–300 | Gap sensor proximity guard; returns hazard description or None |
| `SafetyController.trigger_soft_stop()` | 389–399 | §B soft-stop: controlled deceleration over SOFT_STOP_RAMP_MS |
| `SafetyController.trigger_emergency_stop()` | 385–387 | Hard cut: all actuators off, require explicit reset |
| `SafetyController.check_force_limits()` | 414–423 | Wires ForceMonitor → trigger_soft_stop |
| `SafetyController.check_thermal()` | 425–446 | Wires ThermalMonitor → trigger_soft_stop or trigger_emergency_stop |
| `SafetyController.check_battery()` | 448–469 | Wires BatteryMonitor → trigger_soft_stop or trigger_emergency_stop |
| `SafetyController.check_pinch_points()` | 471–479 | Wires PinchPointGuard → trigger_soft_stop |

---

## Force-limiter limit values (§B: FORCE_LIMIT_NM dict, line 91)

```python
FORCE_LIMIT_NM = {
    "neck_pan":   0.35,   # Nm
    "neck_tilt":  0.25,   # Nm
    "shoulder_l": 0.60,   # Nm
    "shoulder_r": 0.60,   # Nm
    "forearm_l":  1.20,   # N  (pneumatic)
    "forearm_r":  1.20,   # N
    "hip_l":      0.80,   # Nm
    "hip_r":      0.80,   # Nm
    "wheel_fl":   1.50,   # Nm
    "wheel_fr":   1.50,   # Nm
    "wheel_rl":   1.50,   # Nm
    "wheel_rr":   1.50,   # Nm
}
```

**Status:** PLACEHOLDER values — LG-2 calibration required before powered operation. Docstring at line 88–90 states this explicitly.

---

## Scaffolding called before hardware power commands

No hardware power commands exist yet (hardware I/O layer not built). The scaffolding is structured so that `SafetyController.process()` is the entry point that MUST be called with every `robot_signal` → `motor_packet` pair before any command is forwarded to hardware. The docstring at the module top (line 24) states: `§B HARDWARE SAFETY SCOPE — LG-2 REVIEW REQUIRED BEFORE POWERED OPERATION`.

The `SafetyController.process()` method (line 361) intercepts every `CommandPacket` before it can proceed. No bypass path exists in the current code — `_current_packet()` is the only packet selector and it checks `SafetyState` before returning.

---

## LG-2 review gate

Present in the module docstring (line 23–31):

```
§B HARDWARE SAFETY SCOPE — LG-2 REVIEW REQUIRED BEFORE POWERED OPERATION
All classes and constants below define the software contract.  Actual
limit values, sensor wiring, and threshold calibration MUST be reviewed
by David (L3) + a separate LG-2 sign-off before any powered hardware
operation near David.
```

The PINCH_POINT_REGISTRY, THERMAL thresholds, and BATTERY thresholds all carry `# SCAFFOLD — sensor wiring not yet connected. LG-2 review sets final limits.` comments (lines 148–159).

---

## DoD status

| Requirement | Status |
|---|---|
| Functions named — force-limiter, soft-stop, thermal, battery, pinch-point | ✅ all present |
| Force-limiter limit values (placeholders acceptable) | ✅ FORCE_LIMIT_NM dict with 12 joints |
| Scaffolding called before hardware power command | ✅ SafetyController.process() is the only path |
| LG-2 review gate present | ✅ explicit in module docstring + per-section comments |

*Builder · 2026-09-11*
