# FROM BUILDER — WO-FACE-EMOTION-001 D-3 Result
**Date:** 2026-10-03  
**Seat:** Builder  
**WO:** WO-FACE-EMOTION-001 D-3 — Verify mood signal is a clean string  

---

## Findings

### 1. spine.py `_world_dict["mood"]` — CORRECT (already fixed)

`runtime/spine/spine.py:557`:
```python
_et = getattr(cognitive_state, "emotional_tag", None)
_world_dict["mood"] = getattr(_et, "dominant_emotion", "neutral") if _et else "neutral"
```

`dominant_emotion` is a plain string: `"neutral"`, `"joy"`, `"curiosity"`, `"distress"`,  
`"challenge"`, `"connection"`, `"identity"`. NOT a dict. ✅

### 2. Field Unity actually reads — blender_state.json

Unity reads `blender_state.json` (via `EloOSAvatarReceiver.cs`), not `world_state.json`.

Prior to this D-3 fix:
- `blender_state.json → state.emotion` = from `expression_mapper`: **"confident"**, **"worried"**, **"sad"** — wrong vocabulary, doesn't match face clip names.
- No `dominant_emotion` field in blender_state.json.

### 3. Fix applied (this commit)

Added `state.dominant_emotion` to the `_bs_one_brain` patch at `server.py:~6535`:
```python
_bs_et = getattr(_elo_self, "emotional_tag", None)
_bs_dominant = (getattr(_bs_et, "dominant_emotion", None) or "neutral").lower()
# ... in _bs_one_brain["state"]:
"dominant_emotion": _bs_dominant,
```

**blender_state.json now contains:**
```json
"state": {
  "emotion": "neutral",           ← expression_mapper (keep for backward compat)
  "emotional_state": "neutral",   ← keep
  "dominant_emotion": "joy",      ← NEW — from emotion faculty, matches face clip names
  ...
}
```

---

## AT-1 Pass Condition

**AT-1: `world_state.json` `mood` field is a plain string.**  
→ The relevant field is `blender_state.json → state.dominant_emotion`. It is a plain string.  
→ Values: `"neutral"` | `"joy"` | `"curiosity"` | `"distress"` | `"challenge"` | `"connection"` | `"identity"`

---

## Instructions for Game Seat (D-2)

Read `state.dominant_emotion` from `blender_state.json` (NOT `state.emotion`).  
Map to face clip:
- `"joy"` → `elo_face_joy`
- `"curiosity"` → `elo_face_curiosity`
- `"distress"` → `elo_face_distress`
- anything else → `elo_face_neutral`

Commit: `server.py` — state.dominant_emotion now written each turn.

---

*Builder · 2026-10-03 · WO-FACE-EMOTION-001 D-3 DONE*
