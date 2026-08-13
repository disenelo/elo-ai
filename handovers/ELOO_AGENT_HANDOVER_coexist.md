# eLo OS Agent Handover — TTS Fix + Coexistence

## The two problems

### Problem 1: Voice silenced by module-level credential reads

In `voice/voice_engine.py`, credentials are read at module import time:
```python
_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
_EL_KEY     = os.environ.get("ELEVENLABS_API_KEY", "")
_EL_VOICE   = os.environ.get("ELEVENLABS_VOICE_ID", "")
```

If `server.py` loads `.env` after these lines run, all three are empty strings. The fallback chain then drops straight to macOS `say`, bypassing OpenAI and ElevenLabs entirely.

**Fix: lazy reads.** Replace the module-level reads with a `_creds()` function called at speak time:

```python
# Remove the three module-level lines above. Replace with:

def _creds() -> tuple[str, str, str, str]:
    """Read credentials at call time — .env is already loaded by server.py."""
    return (
        os.environ.get("OPENAI_API_KEY",       "").strip(),
        os.environ.get("ELEVENLABS_API_KEY",    "").strip(),
        os.environ.get("ELEVENLABS_VOICE_ID",   "").strip(),
        os.environ.get("ELEVENLABS_VOICE_ID_2", "").strip(),
    )
```

Update every reference inside the functions:

```python
# In _fetch_openai_audio():
openai_key, _, _, _ = _creds()
if not openai_key: return None
headers = {"Authorization": f"Bearer {openai_key}", ...}

# In _fetch_elevenlabs_audio():
_, el_key, el_voice, _ = _creds()
if not el_key or not el_voice: return None
...

# In _speak_thread():
_, el_key, el_voice, _ = _creds()
if el_key and el_voice:
    success = _play_elevenlabs(sentence, stop)
if not success:
    openai_key, _, _, _ = _creds()
    if openai_key:
        success = _play_openai(sentence, stop)
if not success:
    _play_say(sentence, stop)
```

Also apply the same lazy read to `_TTS_VOICE`, `_TTS_SPEED`, `_EL_MODEL`, `_EL_MIX`:
```python
def _tts_config() -> tuple[str, float, str, float]:
    return (
        os.environ.get("ELO_TTS_VOICE",         "shimmer"),
        float(os.environ.get("ELO_TTS_SPEED",   "1.0")),
        os.environ.get("ELEVENLABS_MODEL",       "eleven_turbo_v2_5"),
        float(os.environ.get("ELEVENLABS_VOICE_MIX", "1.0")),
    )
```

---

### Problem 2: 429 / quota with no retry-after

In `_fetch_openai_audio()`, a 429 response prints an error and returns `None`, falling through to `say`. This is silent and confusing.

**Fix: honour Retry-After on 429:**

```python
def _fetch_openai_audio(text: str) -> bytes | None:
    openai_key, _, _, _ = _creds()
    if not openai_key:
        return None
    voice, speed, _, _ = _tts_config()
    try:
        import httpx
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        body = {"model": "tts-1-hd", "input": text, "voice": voice, "speed": speed, "response_format": "mp3"}
        resp = httpx.post(_TTS_URL, json=body, headers=headers, timeout=6.0)
        if resp.status_code == 200:
            return resp.content
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "3"))
            print(f"[eLo voice] OpenAI TTS quota — waiting {wait}s")
            time.sleep(min(wait, 10))   # cap at 10s to avoid blocking too long
            resp2 = httpx.post(_TTS_URL, json=body, headers=headers, timeout=6.0)
            if resp2.status_code == 200:
                return resp2.content
        print(f"[eLo voice] OpenAI TTS error {resp.status_code}: {resp.text[:120]}")
        return None
    except Exception as e:
        print(f"[eLo voice] OpenAI TTS exception: {e}")
        return None
```

Apply the same 429 retry pattern to `_fetch_elevenlabs_audio()`.

---

## Coexistence — eLo OS + Unity desktop avatar

These systems share `blender_state.json` as the single cross-surface truth. The coexistence rules:

**1. eLo OS is the sole writer of the main state keys:** `motion`, `state`, `presence_plan`, `expression`. Unity never writes these.

**2. Unity is the sole consumer of event keys:** `user_nav_event`, `exit_event`, `greeting_event`. Unity reads + acts; eLo OS writes. Neither party may clear the other's keys.

**3. The `_PRESERVE_KEYS` pattern in `state_writer.py`** (see `ELOO_AGENT_HANDOVER_nav.md`) ensures event keys survive a state write. This is the coexistence contract.

**4. Lipsync coexistence:** `blender_bridge/lipsync_writer.py` writes `lipsync_state.json` (separate file). This does not conflict with `blender_state.json`. Do not merge them.

**5. Spotify widget:** writes `blender_state.json["spotify"]` on its own 4s poll from `server.py`. This is fine — the `_PRESERVE_KEYS` approach will also preserve `spotify` across main state writes if added to the set.

---

## Verify voice fix

```bash
cd ~/elo-ai
python3 -c "
from voice.voice_engine import speak, is_speaking
import time
speak('Yo. Testing.')
time.sleep(0.3)
print('speaking:', is_speaking())
time.sleep(3)
print('done')
"
```

Expected: hears eLo speak "Yo. Testing." via OpenAI TTS (or ElevenLabs if keyed). No `say` fallback unless API fails.

---
Architecture authority: `12_presence_faculty.md`, `08_capability_faculty.md`, `99_future_embodiments.md`
Written: 2026-07-05
