# eLo OS Agent Handover — Glow / Mood Emission

## What Unity already does

`EloBodyGlow.cs` reads `blender_state.json` every 250ms.

- **Body glow hue** → read from `presence_plan.primary_hue_h` (0–360 HSV)
- **Glow saturation / value** → `presence_plan.primary_hue_s`, `presence_plan.primary_hue_v`
- **Bloom intensity** → `presence_plan.bloom`
- **Fallback mode colour** → `state.mode` (idle/calm/thinking etc.) when `presence_plan` absent

`EloOSChatTMP.cs` reads `presence_plan.primary_hue_h` for the chat bubble accent colour.

Unity side is complete. The issue is eLo OS reliability.

---

## Current state

`state_writer.write_with_presence()` writes the full `presence_plan` block when the Emotional Light Engine fires. Looking at the current `blender_state.json`:

```json
"state": {
    "energy": 0.33,
    "mode": "exploring",
    "emotion": "confident",
    "intensity": 0.65
},
"presence_plan": {
    "primary_hue_h": 162.0,
    ...
}
```

This is correct when the full spine fires. The problem is that on short/fallback paths (tool calls, nav events, greeting patches), `write()` (not `write_with_presence()`) is called with no `presence_plan`, so Unity drops back to the fallback colour palette.

---

## What eLo OS must fix

### 1 — Never call `write()` when a `presence_plan` exists

In `server.py`, the isolated write block (lines ~767–773):

```python
# Currently:
if _pp:
    _state_write_presence(_cmd, _expr, _presence, _emotion, _pp)
else:
    _state_write(_cmd, _expr, _presence, _emotion)
```

Add: before falling back to `_state_write`, check whether the last known `presence_plan` can be preserved. Add a module-level `_last_pp: dict | None = None` and after every successful write_with_presence, cache the plan:

```python
_last_pp: dict | None = None   # module-level

# In the write block:
if _pp:
    _last_pp = _pp
    _state_write_presence(_cmd, _expr, _presence, _emotion, _pp)
elif _last_pp:
    _state_write_presence(_cmd, _expr, _presence, _emotion, _last_pp)
else:
    _state_write(_cmd, _expr, _presence, _emotion)
```

This ensures the glow colour never resets to fallback on a tool-call turn.

### 2 — Ensure `state.emotion` and `state.intensity` are always populated

In `state_writer.write()` and `write_with_presence()`, the emotion block:
```python
"emotion":   emotion.get("emotion",   "neutral") if emotion else "neutral",
"intensity": emotion.get("intensity", 0.3)       if emotion else 0.3,
```

This is correct. The issue is upstream: ensure `_emotion` in `server.py` is always populated before the write. The safe default is already:
```python
_emotion = None
```

If `_expr_map_emotion()` fails or returns `None`, Unity gets `"neutral"` / `0.3` — acceptable. No change needed here.

### 3 — Ambient / greeting patches must also carry the last known plan

In `server.py`, the greeting patch function (`_patch_greeting`) writes to blender_state.json directly, bypassing `state_writer.py`. This drops `presence_plan`.

Refactor `_patch_greeting` to read the current `blender_state.json`, merge the greeting event into it, and write back — preserving `presence_plan`:

```python
def _patch_greeting(event: str) -> None:
    try:
        with open(_BLENDER_STATE_PATH, encoding="utf-8") as f:
            current = json.load(f)
    except Exception:
        current = {}
    current["greeting_event"] = {"type": event, "_ts": round(time.time(), 3)}
    tmp = _BLENDER_STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    os.replace(tmp, _BLENDER_STATE_PATH)
```

This is the same read-merge-write pattern already used by `_write_nav_event` in `tool_router.py`.

---

## What NOT to touch

- `EloBodyGlow.cs` — Unity side complete
- `EloOSChatTMP.cs` — Unity side complete
- `light_engine.py` — do not change the 20-state table
- `state_writer.py` functions except where noted

---

## Verify

```bash
cd ~/elo-ai
python3 -c "
import json
with open('blender/blender_state.json') as f: s = json.load(f)
pp = s.get('presence_plan', {})
print('hue H :', pp.get('primary_hue_h', 'MISSING'))
print('bloom  :', pp.get('bloom', 'MISSING'))
print('emotion:', s.get('state', {}).get('emotion', 'MISSING'))
"
```

Expected: `hue H : 162.0 | bloom : 0.4 | emotion : confident` (or current state values).

---
Architecture authority: `12_presence_faculty.md`, `10_cognitive_plan.md`
Written: 2026-07-05
