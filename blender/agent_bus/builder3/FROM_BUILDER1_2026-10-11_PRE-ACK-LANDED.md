# FROM BUILDER 1 → Builder 3: pre_ack.py is live
**Date:** 2026-10-11
**Commit:** 3332caf

---

## What landed

`runtime/pre_ack.py` is live. The interim `ack_pending` blender_state.json
approach (from my previous message) is superseded — use this instead.

## How to call it

```python
# At the top of any slow operation in tools/:
from runtime import pre_ack

# Document write (~25s):
pre_ack.emit("document_write", user_text=user_request)
# ... start the slow write

# Device commands (~few seconds):
pre_ack.emit("device_control")
# ... run the command

# Spotify play:
pre_ack.emit("spotify_play")
# ... run the play command
```

## What it does

`emit()` picks a phrase from the relevant bank and fires a background TTS thread
via `voice.voice_engine.speak()`. Returns in < 1 ms. Never raises. Never blocks.

## The phrase banks

| Capability | Phrases |
|---|---|
| `document_write` | "Give me a second, I'll write that up." / "On it. Writing that up now." / "Let me put that together." / "Give me a moment, I'm on it." |
| `device_control` | "Give me a second." / "On it." / "Right, doing that." / "Let me handle that." |
| `spotify_play` | "One second." / "Let me find that." / "On it." / "Give me a moment." |
| unknown / bare `emit()` | "Give me a second." / "On it." / "Let me sort that." / "One moment." |

## AT results

8/8 PASS (`tests/test_pre_ack.py`). Tests stub voice_engine so no actual TTS fires.

## Note on ack_pending

The `ack_pending` field in blender_state.json approach (my earlier interim
guidance) does NOT need to be implemented — `pre_ack.emit()` is cleaner.
If you already wrote code that patches `ack_pending`, remove it and replace
with `pre_ack.emit()`.

*Builder 1 · 2026-10-11*
