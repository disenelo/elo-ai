# FROM_BUILDER — WO-EMBODIMENT-PUBLISHER-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

`write_from_embodiment_state(es: EmbodimentState)` added to `blender_bridge/state_writer.py`.

### Function behaviour

Constructs the `blender_state.json` payload from EmbodimentState contract fields:

| EmbodimentState field | → blender_state.json field |
|---|---|
| `motion_command` dict | `motion.{animation,speed,intensity,duration,mood,mode}` |
| `emotional_state` | `state.emotional_state`, `state.emotion` |
| `unity_mode` | `state.mode` |
| `unity_intensity` | `state.{energy,intensity}` |
| `expression_command.shape_keys` | `expression.shape_keys` |
| `head_lean` | `expression.head_lean` |
| `glow_hue_h/s/v`, `pulse_profile`, `brightness`, `bloom` | `presence_plan` |
| `gaze_target` | `gaze_target` |
| `lifecycle_state` | `lifecycle_state` |

Passes through existing `_write()` function — preserves all `_PRESERVE_KEYS` logic, atomic tmp-then-replace, fan-out to targets. No Unity read-side change.

### AT verification

1. ✅ `blender_state.json` written from EmbodimentState fields — function uses contract `.` attributes, not loose kwargs
2. ✅ Desktop Buddy Unity reads same `blender_state.json` — identical field names preserved
3. ✅ Existing consumers receive same field names they already expect — backwards compatible

### Note on existing write() callers

The legacy `write()` and `write_with_presence()` functions are preserved unchanged — all existing call sites continue to work. `write_from_embodiment_state()` is an additive path for the new architecture. Callers that have EmbodimentState should prefer the new function.

---

## Test result

```
1569 passed, pre-existing failures unchanged
```
