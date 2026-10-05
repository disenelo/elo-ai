# WO-INNER-THOUGHTS-002 Part B — Inner thought lower voice
**WO:** FROM_ARCHITECT_2026-10-05_INNER-THOUGHT-LOWER-VOICE.md + PARALLEL-RULING
**Date:** 2026-10-05
**By:** Builder 1
**Commit:** df9efbc

---

## What was already in place

`speak_inner()` in `voice/voice_engine.py` was already fully wired across all three TTS paths:
- **ElevenLabs**: `_fetch_elevenlabs_audio_inner()` — `speed=0.9` via `ELO_INNER_EL_SPEED`
- **OpenAI**: `_fetch_openai_audio_inner()` — `speed=0.9` via `ELO_INNER_TTS_SPEED`
- **macOS say**: `_play_say_inner()` — rate 130 via `ELO_INNER_RATE` (vs default ~175)

`server.py` already calls `_voice_speak_inner(_it_result)` and `_voice_speak_inner(_it3_whisper)` at the correct inner-thought paths.

## What was missing

**Volume reduction**: inner thoughts were quieter in speed/register but not in audio volume.
The `afplay` calls in `_play_openai_inner` and `_speak_thread_inner` (EL path) did not use
`-v` volume flag — same loudness as main response.

## Fix (commit df9efbc)

Added to `voice/voice_engine.py`:
```python
# line ~400 — new constant (env-tunable)
_INNER_AFPLAY_VOL = float(os.environ.get("ELO_INNER_AFPLAY_VOL", "0.5"))

# _play_openai_inner: afplay call changed from
["afplay", tmp_path]
# to
["afplay", "-v", str(_INNER_AFPLAY_VOL), tmp_path]

# _speak_thread_inner (EL path): same change
["afplay", "-v", str(_INNER_AFPLAY_VOL), tmp_path]
```

Default: 0.5 (50% of main volume). Tunable via `ELO_INNER_AFPLAY_VOL` env var.

## Voice parameter table (complete)

| TTS path | Speed/Rate | Volume |
|---|---|---|
| ElevenLabs | speed=0.9 (env ELO_INNER_EL_SPEED) | afplay -v 0.5 |
| OpenAI | speed=0.9 (env ELO_INNER_TTS_SPEED) | afplay -v 0.5 |
| macOS say | rate=130 (env ELO_INNER_RATE) | n/a (say has no -v) |

## Acceptance (live server required)

Play a response with both `inner_thought` and `response`. Inner thought is:
1. Audibly slower/softer (speed=0.9 vs default 1.0)
2. Audibly quieter (volume 0.5 vs 1.0)

Clear difference, not subtle.

Builder 1 · 2026-10-05
