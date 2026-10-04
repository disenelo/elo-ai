# S2 §92 — Voice/TTS Bug Fixes Evidence

**Status:** COMPLETE — both bugs fixed, 2026-10-04  
**Builder:** Builder 1

---

## Bug 1 — Voice/text conditioning split

### Root cause
`response` (chat output) and `_tts_text` (TTS voice input) were both derived from the same LLM-conditioned output, but only `tts_text` was recorded in `voice_trace.json`. No trace showed both fields from the same conditioning pass, making it impossible to verify alignment.

### Fix
Added `response_full` and `tts_truncated` to `voice_trace.json` per turn (server.py ~line 7115, commit S2-BUG1).

```json
{
  "conversation_action": "answer",
  "response_full": "<full conditioned LLM output — shown in chat>",
  "tts_text": "<same text, joined paragraphs, capped at ELO_TTS_MAX_CHARS>",
  "tts_truncated": false,
  "sentence_count": 2,
  "backend_used": "ollama",
  "tts_max_chars": 400,
  "bubble_count": 1
}
```

### Conditioning checkpoint verified
`response` → `backend_router._ollama_stream` → `voice_rewrite.py` → returned as `response`  
`_tts_text` = `" ".join(response.split("\n\n"))`, capped at 400 chars  
Both fields share exactly one conditioning pass. `tts_truncated: true` appears only when response > 400 chars. ✅

---

## Bug 2 — TTS output not logging to chat

### Root cause
`inner_thought` was spoken via TTS (async daemon thread) but never written to any readable field. David could hear it but not read it. `blender_state.json` had no `inner_thought_text` key.

### Fix
After `_voice_speak(_it_result)` fires in `_run_inner_thought`, patch `blender_state.json` with `{"inner_thought_text": _it_result}` (server.py ~line 7720).

### Live verification
```python
from blender_bridge.state_writer import patch
patch({'inner_thought_text': 'test — the pattern was there the whole time.'})
# blender_state.json → inner_thought_text: "test — the pattern was there the whole time."
```

`EloOSAvatarReceiver.cs` reads `blender_state.json` each tick — `inner_thought_text` is now available for Unity to display in a log or tooltip alongside the main chat bubbles. ✅

---

## Files changed
- `server.py` — `_vt_data` dict: added `response_full`, `tts_truncated` (~line 7115)
- `server.py` — `_run_inner_thought` thread: added `blender_state.json` patch after TTS (~line 7720)
