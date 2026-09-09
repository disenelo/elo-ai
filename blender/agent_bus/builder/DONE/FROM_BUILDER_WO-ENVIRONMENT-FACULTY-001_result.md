# FROM_BUILDER — WO-ENVIRONMENT-FACULTY-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

`_environment_faculty()` added to `runtime/spine/spine.py` (before `assemble_cognitive_state()`).

### Function behaviour

- Reads `blender/perch_state.json` → `active_app`
- Reads `blender/presence_state.json` → `active_window` (frontWindowName)
- Infers `desktop_activity` from app name via `_APP_TO_ACTIVITY` mapping:
  - VS Code / Cursor / Xcode / PyCharm → "coding"
  - Blender / Figma / Photoshop → "creating"
  - Word / Pages / Notion / Obsidian → "writing"
  - Brave / Safari / Chrome / Arc → "browsing"
  - Terminal / iTerm / Warp → "terminal"
  - Default → "unknown"

### Integration

`assemble_cognitive_state()` calls `_environment_faculty()` and passes the result:
```python
active_app=_env.get("active_app", ""),
active_window=_env.get("active_window", ""),
desktop_activity=_env.get("desktop_activity", "unknown"),
```

### AT verification

1. ✅ CognitiveState.active_app non-empty when DesktopBuddy is active — reads from live perch_state.json
2. ✅ Graceful fallback: returns empty dict when either JSON file absent (files not found → empty strings)
3. ✅ Environment fields are context only — no routing decision logic in `_environment_faculty()`

---

## Test result

```
1569 passed, pre-existing failures unchanged
```
