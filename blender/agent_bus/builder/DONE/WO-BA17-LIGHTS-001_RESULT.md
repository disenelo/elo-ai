# WO-BA17-LIGHTS-001 · RESULT CARD

**Status**: COMPLETE — SERVING INTENT  
**Filed**: 2026-09-15  
**Builder**: Claude Code (session b15c1e7a)

---

## Deliverables

1. **`capabilities/lights_agent.py`** — Philips Hue local bridge control  
   - `set_scene(scene_name)` → `{success, scene, error}`
   - `set_brightness(level)` → `{success, level, error}`
   - `set_colour(hue, saturation, brightness)` → `{success, error}`
   - `dispatch_lights(action, params)` — primary dispatch for registry
   - `dispatch(query)` — natural-language dispatch (scene-name matching, defaults to "calm")
   - 5 scenes: calm (warm white 40%), focus (cool white 80%), play (colour 60%), dim (warm 20%), off
   - Graceful failure if `HUE_BRIDGE_IP` or `HUE_API_KEY` not set

2. **`runtime/capability_registry.py`** — added `WORLD_LIGHTS_CONTROL` entry + `dispatch_lights()` function  

3. **`.env.example`** — `HUE_BRIDGE_IP` and `HUE_API_KEY` documented

---

## DoD Verification

**DoD-A — set_scene("calm") with no env vars**: PASS  
```python
{'success': False, 'scene': 'calm', 'error': 'HUE_BRIDGE_IP not set'}
```

**DoD-B — WORLD_LIGHTS_CONTROL in registry**: PASS  
- `is_registered("WORLD_LIGHTS_CONTROL")` → True  
- `write_allowed`: True

**DoD-C — dispatch_lights("set_scene", {"scene": "focus"}) returns dict**: PASS  
```python
{'success': False, 'scene': 'focus', 'error': 'HUE_BRIDGE_IP not set'}
```
Graceful failure (env not set in test). Returns dict with `success` key as required.

**Bonus — unknown scene handled**: PASS  
```python
{'success': False, 'scene': 'party', 'error': "Unknown scene 'party'. Known: calm, dim, focus, off, play"}
```

---

## Activation

Set in `.env`:
```
HUE_BRIDGE_IP=192.168.x.x    # your Hue bridge local IP
HUE_API_KEY=<paired-username> # from bridge /debug/clip.html
```

Scene names eLo can use: `calm`, `focus`, `play`, `dim`, `off`

---

## Verdict

SERVING INTENT. Lights capability built, registered, and verified. Fails gracefully when bridge not configured. No cloud dependency.
