# FROM_BUILDER — WO-VOICE-IO Result Card
**Date:** 2026-09-05  
**WO:** WO-VOICE-IO — Voice Input / Voice Output / Alexa Gateway  
**Priority:** P3 · Gate OPEN (SPEC_voice_io_L3_ratified_2026-09-05.md)  
**Authority:** David L3 2026-09-05  
**Executed by:** Builder seat  

---

## Deliverables

| Item | Status |
|---|---|
| `capabilities/voice_output.py` — `VoiceOutputCapability` class | CHANGED (NEW) |
| `capabilities/__init__.py` — package init | CHANGED (NEW) |
| `runtime/spine/plan.py` — `speech_text: str = ""` added to `CognitivePlan` | CHANGED |
| `WORLD_VOICE_OUTPUT` in `runtime/capability_registry.py` | EXISTING (pre-wired 2026-08-31) |
| `WORLD_VOICE_INPUT` in `runtime/capability_registry.py` | EXISTING (pre-wired 2026-08-31) |
| `voice/voice_engine.py` — canonical TTS engine | EXISTING |
| `voice/stt.py` — canonical STT (`capture()`, `is_available()`) | EXISTING |
| `plugins/voice/tts_output.py` — governed wrapper | EXISTING |
| Alexa gateway | DEFERRED — David L3 2026-09-05: "not in scope" |
| `executive.py` | UNCHANGED |

## Architecture

`VoiceOutputCapability` in `capabilities/voice_output.py` reads `CognitivePlan.speech_text` and delegates to `voice/voice_engine.speak()`. Silence gate: if `speech_text` is empty or None, method returns `False` with no audio output (LAW-017 / Q4 invariant). Backend selected via `ELO_TTS_BACKEND` env var (`openai` / `elevenlabs` / `local`).

## Acceptance tests

| AT | Result |
|---|---|
| AT-1: `from capabilities.voice_output import VoiceOutputCapability` — imports cleanly | PASS |
| AT-2: TTS produces non-empty audio for sample speech_text | DEFERRED — requires live API key + hardware |
| AT-3: STT transcribes audio clip to non-empty string | DEFERRED — requires audio hardware |
| AT-4: Alexa tests | DEFERRED — removed from scope by David L3 |
| AT-5: `WORLD_VOICE_OUTPUT` and `WORLD_VOICE_INPUT` registered | PASS (pre-existing) |
| AT-6: No TTS output when `speech_text` is null/absent | PASS |
| AT-7: Backend switches on `ELO_TTS_BACKEND` env var change | PASS |
| AT-8: Local Whisper without cloud when `ELO_STT_ALLOW_CLOUD=false` | DEFERRED — requires hardware |

**Test run:** 1559 passed. 3 pre-existing failures unchanged.

*Builder seat · 2026-09-05 · WO-VOICE-IO · Alexa DEFERRED per David L3*
