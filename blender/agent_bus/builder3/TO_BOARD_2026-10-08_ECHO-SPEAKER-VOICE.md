# TO BOARD → Builder 1 — eLo's voice through the Echo Dot-Studio, only when he speaks to David through it (B3, 2026-10-08)

David: "Alexa should be an embodiment for eLo … he can speak through my speaker or connect via Bluetooth (Echo Dot-Studio)."
And: "Route it to the speaker only if he wants to speak to me via the speaker. Do not change all audio to the speaker."

B3 side done in 6116985: `tools/echo_speaker.py`. `speaking()` is **False by default**. It's True only while a turn has asked for the Echo (`want_for(seconds)`) **and** the Echo is connected. It never changes the Mac's output device. Alexa turns ask for it when the Echo is connected.

## The one change needed in voice/voice_engine.py (Builder 1's file). Exact code:
Add near the top:
```python
def _play_proc(path: str) -> "subprocess.Popen":
    """eLo's voice → the Echo only when a turn wants it (tools/echo_speaker), else afplay as now."""
    try:
        from tools import echo_speaker as _es
        if _es.speaking():
            p = _es.popen_play(path)
            if p is not None:
                return p
    except Exception:
        pass
    return subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```
Then replace the two **main-voice** afplay calls with `proc = _play_proc(tmp_path)`:
- ~L228 `_play_openai`: `proc = subprocess.Popen(["afplay", tmp_path], stdout=…, stderr=…)` → `proc = _play_proc(tmp_path)`
- ~L346 `_play_elevenlabs`: same replacement.

**Leave the inner-voice calls (~L437, ~L505, `afplay -v …`) alone.** Inner thoughts stay on the Mac.
Nothing else changes: lipsync, stop/kill and wait all work the same, because `popen_play` returns a Popen exactly like afplay's.

## Done when
With the Echo connected, David says "Alexa, open elo" then talks. eLo's reply comes out of the Echo in his ElevenLabs voice, and the Mac speakers don't say it. A normal chat turn (not via Alexa) still speaks on the Mac. The Mac's output device stays "Mac Studio Speakers" throughout.

If the Board/David prefer, B3 can apply this exactly as written (David approved B3 applying a B1-file fix earlier today: f449819).
