# FROM BUILDER 3 → Builder 1 (via Board): pre_ack cuts eLo off mid-sentence (P1). One-line fix in runtime/pre_ack.py

**David, 2026-10-12:** "The ack ('give me a second') plays … in the middle of a sentence, cutting the sentence."

## Cause
`pre_ack.emit()` calls `voice_engine.speak()`, which **interrupts** whatever eLo is saying. emit never checks `voice_engine.is_speaking()`. Server sites: server.py ~2863, 3486, 3525, 3860, 3890, 4166, 4191, 4235, 4265.

## Live reproduction (B3, 2026-10-12, real voice_engine → Echo)
| Run | Result |
|---|---|
| Long sentence, then `pre_ack.emit("default")` 2.5 s in | sentence playback **killed mid-play (exit −9)**, ack played instead |
| Same, but skip the ack when `is_speaking()` | ack skipped; sentence **played to the end** (exit 0) |

## Fix (inside emit, so all 9 server sites are covered)
```python
def emit(capability: str = "default", user_text: str = "") -> None:
    try:
        from voice.voice_engine import is_speaking as _is_speaking, speak as _speak
        if _is_speaking():          # never cut eLo off mid-sentence (David 2026-10-12)
            return
        bank = _PHRASES.get(capability) or _PHRASES["default"]
        _speak(random.choice(bank))
    except Exception as _e:
        _log.warning("pre_ack.emit: TTS pre-ack failed — continuing without ack: %s", _e)
```
B3 already applied the same guard at its own two sites (8f89641: documents, Spotify).
