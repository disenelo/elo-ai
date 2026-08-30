# FROM BUILDER — WO-MOBILE-BRAIN phone_capabilities

**WO:** WO-MOBILE-BRAIN — Builder half: `phone_capabilities` field  
**Priority:** P1 · **Authority:** David L3 (D1b ruling, 2026-08-29)  
**Date:** 2026-08-30  
**Commit:** `bc2d99b`

---

## Result

**AT-7: 1/1 PASS**

```
✅ AT-7: phone_capabilities in blender_state.json = [
    'brightness', 'calculator', 'calendar', 'camera', 'draft', 'github',
    'image_gen', 'media_control', 'model_gen', 'news', 'reminders', 'search',
    'spotify', 'time', 'timer', 'translate', 'truth_sync', 'vault_write',
    'weather', 'wikipedia'
]
```

## What shipped

`server.py` startup block: reads `_PHONE_CAPABLE` from `runtime/capabilities/registry.py` and writes it as `phone_capabilities` (sorted array of strings) to `blender_state.json` via `state_writer.patch()`.

Written once at boot. Static field — `_PHONE_CAPABLE` never changes at runtime.

## Constraints met

- No new endpoint — field rides existing state file payload
- Ruling 006 (probe surface) untouched
- `executive.py` not touched (FREEZE_V1_LOCK clean)

*Builder / Board — 2026-08-30*
