# eLo OS Agent Handover — Gaze Emission

## What Unity already does

`EloOSAvatarReceiver.cs` reads `blender_state.json` every 250ms. When a `gaze` block is present, it drives `FollowHead.cs` with `yaw` and `pitch` values, overriding Unity's local mouse-follow fallback. When `gaze.active = false` (or the block is absent), Unity falls back to mouse tracking.

Unity side is complete. eLo OS is not yet writing `gaze`.

---

## What eLo OS must add

### 1 — Add `gaze` to `state_writer.py`

In `write()` and `write_with_presence()` add an optional `gaze` parameter and write it to the payload.

**Add to the function signature of both `write()` and `write_with_presence()`:**
```python
gaze: dict | None = None,
```

**Add to the payload build in both functions** (after the `if presence:` block):
```python
if gaze:
    payload["gaze"] = {
        "yaw":    float(gaze.get("yaw",    0.0)),
        "pitch":  float(gaze.get("pitch",  0.0)),
        "active": bool(gaze.get("active",  True)),
    }
```

### 2 — Populate gaze in `server.py`

In the section that calls `_state_write` / `_state_write_presence` (lines ~765–771 in `server.py`), pass a gaze dict derived from the attention model or cognitive plan.

**Add a `_gaze` variable before the write block (alongside `_cmd`, `_expr`, `_emotion`):**
```python
_gaze = None
```

**Inside the try block, populate it from the attention model:**
```python
_gaze_dir = attention_model.get("gaze_direction", {})
if _gaze_dir:
    _gaze = {
        "yaw":   float(_gaze_dir.get("yaw",   0.0)),
        "pitch": float(_gaze_dir.get("pitch",  0.0)),
        "active": True,
    }
```

**Then pass it to the write calls:**
```python
# in the isolated write try block:
_state_write_presence(_cmd, _expr, _presence, _emotion, _pp, gaze=_gaze)
# or:
_state_write(_cmd, _expr, _presence, _emotion, gaze=_gaze)
```

### 3 — Populate `gaze_direction` in the attention model

The attention model (`attention_model` dict in `server.py`) needs a `gaze_direction` key. Source options in priority order:

1. **Cognitive plan** — if `plan.gaze` is set by the Executive Faculty, use it
2. **Relationship / focus state** — if user is actively typing (recent message < 2s), look forward/slight-down (yaw=0, pitch=-8); if idle and wander allowed, allow Unity fallback (`active: false`)
3. **Presence plan mode** — map `presence_plan.emotional_state` to a base gaze posture:
   - `calm` / `reflection` → pitch=-12 (looking down, meditative)
   - `curiosity` / `exploring` / `wonder` → pitch=+5, yaw varies slowly
   - `connection` / `listening` → yaw=0, pitch=0 (looking straight at user)
   - all others → yaw=0, pitch=-5 (soft resting gaze)

**Minimal first pass** (no cognitive plan integration yet):
```python
# In the attention model build, after emotional context:
_pp_state = (_plan.presence_plan or {}).get("emotional_state", "neutral") if _plan else "neutral"
_GAZE_MAP = {
    "calm":        (-15, 0), "reflection": (-12, 0), "waiting": (-8, 0),
    "curiosity":   (  5, 0), "exploring":  ( 5, 0),  "wonder":  (5, 0),
    "connection":  (  0, 0), "listening":  ( 0, 0),
}
_pitch, _yaw = _GAZE_MAP.get(_pp_state, (-5, 0))
attention_model["gaze_direction"] = {"yaw": _yaw, "pitch": _pitch}
```

---

## What NOT to touch

- `EloOSAvatarReceiver.cs` — Unity side is complete
- `FollowHead.cs` — Unity side is complete
- Any file not listed above

---

## Result in `blender_state.json`

```json
"gaze": {
  "yaw":   0.0,
  "pitch": -5.0,
  "active": true
}
```

When `active: false`, Unity falls back to mouse tracking. When `active: true`, eLo's head is driven by eLo OS, not Unity's brain.

---
Architecture authority: `12_presence_faculty.md`, `17_behaviour_faculty.md`
Written: 2026-07-05
