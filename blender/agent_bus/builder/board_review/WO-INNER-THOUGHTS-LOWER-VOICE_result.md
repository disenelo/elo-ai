# WO-INNER-THOUGHTS-LOWER-VOICE — Result Card

**Builder:** Builder 1
**Date:** 2026-10-05
**Authority:** David L3 — "making inner thoughts read in a lower voice to the main voice" 2026-10-05
**Status:** COMPLETE

---

## What was changed

**`voice/voice_engine.py`** — added inner-thought TTS pipeline:

- `_fetch_openai_audio_inner(text)` — OpenAI TTS at `speed=0.9` (vs normal `_TTS_SPEED`, default 1.0)
- `_play_openai_inner(text, stop)` — plays the lower-speed audio
- `_play_say_inner(text, stop)` — macOS say at rate 130 (vs normal 160)
- `_fetch_elevenlabs_audio_inner(text)` — ElevenLabs with `speed=0.9` (vs 1.09 normal)
- `_speak_thread_inner(text, stop)` — full cascade: EL → OpenAI inner → say inner
- `speak_inner(text)` — public entry point (address rule + audit log, like `speak()`)

Default inner-thought parameters (overridable via env vars):
- `ELO_INNER_TTS_SPEED=0.9` — OpenAI speed
- `ELO_INNER_RATE=130` — macOS say rate
- `ELO_INNER_EL_SPEED=0.9` — ElevenLabs speed

**`server.py`** — updated two inner_thought call sites:
- Line 2384: dream whisper `_voice_speak` → `_voice_speak_inner`
- Line 7797: WO-INNER-THOUGHTS-001 pipeline `_voice_speak` → `_voice_speak_inner`

---

## Evidence

- Import check: `from voice.voice_engine import speak, speak_inner` ✅
- Server compiles clean (AT-6 in WO-041 suite) ✅
- 2873 tests pass, no regressions ✅

---

## Live test required

Play a response that contains both inner_thought and response output. The inner thought should be audibly slower/quieter. Clear difference — not subtle (per David's spec).

Builder 1 · 2026-10-05
