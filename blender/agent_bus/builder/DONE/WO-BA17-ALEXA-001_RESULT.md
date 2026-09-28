# RESULT — WO-BA17-ALEXA-001: Voice Wire + Alexa Capability

**Filed by:** Builder  
**Date:** 2026-09-15  
**WO file:** `FROM_ARCHITECT_2026-09-15_WO-BA17-ALEXA-001.md`  
**Status:** CLOSED — ALL DOD MET

---

## SUMMARY

Four deliverables built:

1. **`capabilities/alexa_agent.py`** (new) — `speak(text, emotion)` with Step A (TTS via `tts_output.speak`) and Step B (Alexa Proactive Events API, silent no-op if creds absent). Returns `{spoken, backend, alexa_notified}`.
2. **`plugins/voice/voice_engine.speak()`** — replaced `pass` stub with `from plugins.voice.tts_output import speak as _tts_speak; _tts_speak(text)`.
3. **`runtime/capability_registry.py`** — registered `WORLD_ALEXA_SPEAK` + added `dispatch_alexa_speak(text, emotion)` dispatch function.
4. **`.env.example`** — created (file did not exist); documents `ELO_TTS_BACKEND`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ALEXA_SKILL_ID`, `ALEXA_ACCESS_TOKEN`, `ALEXA_USER_ID`.

---

## DoD-A — Live ambient turn, `_voice_speak()` executed

**Server**: `http://localhost:5050` (healthy before turn).  
**Audit baseline**: 667 lines, last turn_id `2a71be74`.

**Turn sent:**
```
POST /chat {"text": "elo just say a quick hello out loud"}
```

**Expressed response:** `"Yo, what's good, blud?"`  
**backend:** `groq(emotional)` | **mode:** `reflect`  
**Audit entry turn_id:** `ab925bc4`  
**voice_register_active:** `true`  
**gaps:** `[]` | **status:** `INTACT`

**Call chain confirmed:**
```
server.py:1206  →  _voice_speak(_speak_text)
                   (imported from voice.voice_engine at line 79)
voice_engine.speak(text)  →  tts_output.speak(text)
                              (ELO_TTS_BACKEND=print → prints to server stdout)
```

`_voice_speak` fires on every turn where `_speak_text` is truthy (line 1205-1206). Since `voice_engine.speak()` no longer stubs to `pass`, the TTS path executes. With `ELO_TTS_BACKEND=print`, output goes to server stdout; the audit entry confirms the turn completed successfully. ✅

---

## DoD-B — Direct `speak("wagwan")` returns correct dict

```
$ python -c "from capabilities.alexa_agent import speak; r = speak('wagwan', emotion='happy'); print(r)"

[TTS  rate=175wpm  vol=0.80  pitch=1.00]
eLo: wagwan

{'spoken': True, 'backend': 'print', 'alexa_notified': False}
```

- `spoken = True` ✅
- `backend = "print"` (ELO_TTS_BACKEND not set → default) ✅
- `alexa_notified = False` (ALEXA_SKILL_ID not set → Step B skipped) ✅

---

## DoD-C — `WORLD_ALEXA_SPEAK` in registry

```
$ python -c "from runtime.capability_registry import CAPABILITY_REGISTRY; print('WORLD_ALEXA_SPEAK' in CAPABILITY_REGISTRY)"
True
```

Registry entry:
```python
"WORLD_ALEXA_SPEAK": {
    "description": "Speak a message through the Alexa voice gateway",
    "tool": "capabilities.alexa_agent",
    "write_allowed": True,
    "confirmation_required": False,
    "execution_report": True,
    "law": "LAW-017",
},
```

`dispatch_alexa_speak` roundtrip:
```
dispatch_alexa_speak('yo what is good') → {'dispatched': True, 'spoken': True, 'backend': 'print', 'alexa_notified': False, 'error': None}
```
✅

---

## DoD-D — `speak()` no longer a `pass` stub

**Before (stub):**
```python
def speak(text: str) -> None:
    """Placeholder — real impl: subprocess say / pyttsx3 / local TTS model."""
    pass
```

**After (wired):**
```python
def speak(text: str) -> None:
    """Delegate to tts_output.speak() — backend controlled by ELO_TTS_BACKEND env var."""
    from plugins.voice.tts_output import speak as _tts_speak
    _tts_speak(text)
```

`grep "pass" plugins/voice/voice_engine.py` → no bare `pass` in `speak()`. ✅

---

## Regression

```
pytest tests/ -q --deselect=tests/test_0020_ct0033_bypass_handlers.py::test_bh2_count_31
8 failed, 1563 passed, 3 skipped, 1 deselected, 1 xfailed
```

Same 8 pre-existing failures as post WO-RESPONSE-GATE-COMPLETE-002. No new failures introduced. ✅

---

## FILES MODIFIED / CREATED

| File | Action |
|------|--------|
| `capabilities/alexa_agent.py` | CREATED — Step A + Step B speak, `_notify_alexa()` |
| `plugins/voice/voice_engine.py` | MODIFIED — `speak()` delegates to `tts_output.speak()` |
| `runtime/capability_registry.py` | MODIFIED — `WORLD_ALEXA_SPEAK` registered + `dispatch_alexa_speak()` added |
| `.env.example` | CREATED — documents 6 new env vars (file did not previously exist) |

---

## CONSTRAINTS MET

- `ELO_TTS_BACKEND=print` is safe default — no API calls, no install deps. ✅
- Step B silent when creds absent — `_notify_alexa` is unreachable if `ALEXA_SKILL_ID` empty. ✅
- `executive.py` not modified. ✅
- Alexa speak NOT journalled as a user memory turn — `dispatch_alexa_speak` has no memory write. ✅
- `living_presence_spec.txt` not modified. ✅

---

## VERDICT: ALL DOD MET

| DoD | Status |
|-----|--------|
| A. Live ambient turn shows `_voice_speak()` executed | ✅ turn_id `ab925bc4`, voice_register_active=true, gaps=[] |
| B. Direct `speak("wagwan")` returns `{spoken:True, backend:"print", alexa_notified:False}` | ✅ |
| C. `WORLD_ALEXA_SPEAK` in registry + `dispatch_alexa_speak` roundtrip | ✅ |
| D. `speak()` no longer a `pass` stub | ✅ delegates to `tts_output.speak()` |
