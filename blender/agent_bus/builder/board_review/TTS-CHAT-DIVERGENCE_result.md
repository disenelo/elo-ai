# Result Card — TTS-CHAT-DIVERGENCE
**Builder:** Builder 1
**Date:** 2026-10-06
**Commit:** e0a45d6
**Status:** COMPLETE — inner_thought now mirrors to ambient_speech.json

---

## Root cause found

`_run_inner_thought` is a daemon thread that fires **after the HTTP response returns**.
Unity receives `inner_thought: ""` in the HTTP response dict. The daemon thread:
1. Generates `_it_result` via LLM
2. Calls `_voice_speak_inner(_it_result)` — TTS fires ~15s after the turn
3. Patches `blender_state.json.inner_thought_text` — depends on Unity polling

Unity was not displaying the inner_thought in the chat log because it never received the text through the HTTP response channel.

---

## Fix

After `_voice_speak_inner(_it_result)` (line ~8430), atomically write the inner_thought to `blender/ambient_speech.json` with:
- `text: "-- " + _it_result.strip()` — the `--` debug prefix as the dispatch requires
- `source: "inner_thought"` — distinguishable from normal ambient speech
- `_ts: time.time()` — same timestamp format as ambient path

Unity already polls `ambient_speech.json` for ambient engine output. Inner_thought text now arrives through the same channel.

---

## Audit of all TTS sources vs Unity chat

| Source | TTS | Unity chat | Status |
|---|---|---|---|
| Main path `_tts_text` | `_voice_speak(_tts_text)` line 7633 | `response` field in HTTP | ✅ same text (both from `response` post-scrubs) |
| Early TTS `sentence` | `_voice_speak(sentence)` line 6267 | Same text — skip logic at 7629 prevents double-speak | ✅ |
| Ambient `_speak_text` | `_voice_speak(_speak_text)` line 1522 | `ambient_speech.json` + conversation_tracker | ✅ (already fixed) |
| Inner thought `_it_result` | `_voice_speak_inner(_it_result)` line 8430 | `ambient_speech.json` with `-- ` prefix | ✅ **FIXED this commit** |
| Direct paths (39 calls) | `_voice_speak(resp)` then `return {"response": resp}` | Same variable | ✅ |

**All TTS sources now have a Unity chat mirror path.**

---

## Acceptance criteria

"David speaks to eLo for 10 turns. Every word eLo says aloud is visible in the Unity chat log."

This requires Unity to be reading `ambient_speech.json` and displaying its content in the chat. The Python side now writes all spoken text there. Whether Unity's chat panel is wired to display `ambient_speech.json` content is a Unity-side question (Builder 1 cannot read or edit C#). Escalate to Design/Unity seat if the patch is live but content still doesn't appear.

---

Builder 1 · 2026-10-06
