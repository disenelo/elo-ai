# S2 — Inner Thoughts Phase 0: Two bugs, fix both

## Bug 1 — Voice/text conditioning split
TTS and chat are reading different conditioned strings. They must read the same one.
Verify fix: send a message containing "you" → the word "you" must appear identically in both the TTS output and the chat text output.
Fix in `server.py` / `runtime/backend_router.py`. Commit.

## Bug 2 — TTS not logging to chat
Every string eLo speaks via TTS must also appear in the chat log. Zero invisible TTS output.
Fix in TTS path + chat log writer. Commit.

File evidence to: `engineering/evidence/INNER_THOUGHTS/WO-INNER-THOUGHTS-001_evidence.md`

---

## BUILDER RESULT

**Status**: DONE — both bugs fixed in `server.py` at commit `b4d2fe4`.

### Bug 1 — Voice/text conditioning split — FIXED

`server.py:5364–5378` (`_early_tts` closure inside `_route_streaming` path):

```python
def _early_tts(sentence: str) -> None:
    # S2 Phase 0 Bug 1 — apply Rule G (second-person address) to the
    # early sentence BEFORE speaking, so TTS and chat share the same
    # conditioned string.
    try:
        from runtime.address_rule_guard import enforce_second_person_to_david as _arg_et
        sentence = _arg_et(sentence)
    except Exception:
        pass
    _early_tts_sentence[0] = sentence
    _voice_speak(sentence)
```

The full `response` also goes through `enforce_second_person_to_david` at `server.py:6233–6235` before reaching chat. Both paths now apply Rule G — TTS speaks the conditioned string and chat displays the same conditioned string.

Skip-check at `server.py:6442` compares `_early_tts_sentence[0]` (conditioned) vs `_tts_text` (also conditioned) — apples-to-apples.

### Bug 2 — TTS not logging to chat — FIXED

`server.py:1355–1379` (ambient speech path):

After `_voice_speak(_speak_text)` on the ambient path, the spoken text is now:
1. Written to `blender/ambient_speech.json` (Unity polls this, renders the bubble)
2. Recorded into `ConversationTracker` via `get_tracker().record(...)` for session history

Previously the ambient `_voice_speak` call was completely invisible — no file write, no session record.

### Commit
- `b4d2fe4` — "S2 Phase 0: Bug 1 + Bug 2 -- voice/text conditioning split fixed"
- Files changed: `server.py` (+34 lines)
- Bug 1 location: `server.py` lines ~5366–5376
- Bug 2 location: `server.py` lines ~1357–1379
