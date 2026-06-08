"""
plugins/voice/tts_output.py — eLo AI voice output layer.

Converts kernel response text to speech.
Optionally varies tone based on the emotion snapshot.

No kernel changes. No decision logic. Read-only consumer of existing outputs.

Three backend stubs:
    "print"      — default, prints to stdout (always available, no deps)
    "pyttsx3"    — local TTS via pyttsx3 (pip install pyttsx3)
    "elevenlabs" — API TTS via ElevenLabs (set ELEVENLABS_API_KEY)

Emotion → voice parameters:
    emotion_snapshot.emotion  → rate, pitch, volume adjustments
    emotion_snapshot.warmth   → volume scale
    emotion_snapshot.pacing   → rate scale

Entry point:
    speak(text, emotion_snapshot=None, backend=None)

Switch backend:
    set_tts_backend("pyttsx3")
    set_tts_backend("elevenlabs")
    set_tts_backend("print")     # default
"""

import os
import logging

logger = logging.getLogger(__name__)

_ACTIVE_TTS = os.environ.get("ELO_TTS_BACKEND", "print")


# ── emotion → voice parameter mapping ─────────────────────────────────────────
# Values are multipliers or offsets applied to TTS engine parameters.
# No decision logic — lookup table only.

_EMOTION_VOICE_PARAMS: dict = {
    #              rate_mult  pitch_mult  volume
    "curious":    (1.05,      1.10,       0.90),
    "excited":    (1.15,      1.15,       0.95),
    "calm":       (0.90,      0.95,       0.85),
    "focused":    (0.95,      0.95,       0.85),
    "playful":    (1.10,      1.15,       0.90),
    "distressed": (0.85,      0.90,       0.80),
    "gentle":     (0.88,      0.92,       0.80),
    "reflective": (0.85,      0.90,       0.80),
    "neutral":    (1.00,      1.00,       0.85),
    "idle":       (1.00,      1.00,       0.85),
}

# pacing string → rate multiplier modifier
_PACING_RATE: dict = {
    "quick":     0.10,
    "measured":  0.00,
    "unhurried":-0.05,
    "slow":     -0.10,
    "very_slow":-0.15,
}

_BASE_RATE   = 175   # words per minute (pyttsx3 default range ~100-250)
_BASE_VOLUME = 1.0   # 0.0 - 1.0
_BASE_PITCH  = 1.0   # multiplier (not all engines support this)


def _resolve_params(emotion_snapshot: dict) -> dict:
    """
    Build voice parameters from an emotion snapshot dict.
    Snapshot keys: emotion, tone, pacing, warmth.

    Returns: {rate, volume, pitch}
    All values are concrete numbers — no logic, only lookup + multiplication.
    """
    emotion = (emotion_snapshot or {}).get("emotion", "neutral")
    pacing  = (emotion_snapshot or {}).get("pacing",  "moderate")
    warmth  = float((emotion_snapshot or {}).get("warmth", 0.7))

    rate_m, pitch_m, vol = _EMOTION_VOICE_PARAMS.get(
        emotion, _EMOTION_VOICE_PARAMS["neutral"]
    )

    # pacing adjusts rate
    rate_m += _PACING_RATE.get(pacing, 0.0)

    # warmth scales volume slightly
    vol_adjusted = round(vol * (0.8 + warmth * 0.2), 2)

    return {
        "rate":   round(_BASE_RATE * rate_m),
        "volume": min(1.0, vol_adjusted),
        "pitch":  round(_BASE_PITCH * pitch_m, 2),
    }


# ── backend implementations ────────────────────────────────────────────────────

def _speak_print(text: str, params: dict):
    """
    Print backend — always available, zero dependencies.
    Shows the text and voice parameters for testing.
    """
    rate   = params["rate"]
    vol    = params["volume"]
    pitch  = params["pitch"]
    print(f"\n[TTS  rate={rate}wpm  vol={vol:.2f}  pitch={pitch:.2f}]")
    print(f"eLo: {text}\n")


def _speak_pyttsx3(text: str, params: dict):
    """
    Local TTS via pyttsx3.

    HARDWARE HOOK — activate with:
        pip install pyttsx3
        set_tts_backend("pyttsx3")

    pyttsx3 supports: rate (wpm), volume (0.0-1.0).
    Pitch is engine-dependent (sapi5 on Windows, nsss on macOS, espeak on Linux).
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate",   params["rate"])
        engine.setProperty("volume", params["volume"])
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except ImportError:
        logger.error("pyttsx3 not installed. Run: pip install pyttsx3")
        _speak_print(text, params)
    except Exception as exc:
        logger.error("pyttsx3 error: %s", exc)
        _speak_print(text, params)


def _speak_elevenlabs(text: str, params: dict, voice_id: str = None):
    """
    ElevenLabs API TTS.

    HARDWARE HOOK — activate with:
        pip install elevenlabs
        export ELEVENLABS_API_KEY=your_key
        export ELO_ELEVENLABS_VOICE_ID=voice_id   (optional)
        set_tts_backend("elevenlabs")

    stability and similarity_boost are fixed — they control voice consistency,
    not emotion. Emotion is carried by the text content itself.
    """
    api_key  = os.environ.get("ELEVENLABS_API_KEY", "")
    voice_id = voice_id or os.environ.get("ELO_ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    if not api_key:
        logger.warning("ELEVENLABS_API_KEY not set. Falling back to print.")
        _speak_print(text, params)
        return

    try:
        from elevenlabs import generate, play, set_api_key
        set_api_key(api_key)
        audio = generate(
            text       = text,
            voice      = voice_id,
            model      = "eleven_monolingual_v1",
        )
        play(audio)
    except ImportError:
        logger.error("elevenlabs not installed. Run: pip install elevenlabs")
        _speak_print(text, params)
    except Exception as exc:
        logger.error("ElevenLabs error: %s", exc)
        _speak_print(text, params)


# ── public API ─────────────────────────────────────────────────────────────────

def set_tts_backend(name: str):
    """
    Switch the active TTS backend.
    Valid: "print" | "pyttsx3" | "elevenlabs"
    """
    global _ACTIVE_TTS
    _ACTIVE_TTS = name.lower()
    logger.info("TTS backend set to: %s", _ACTIVE_TTS)


def active_backend() -> str:
    """Return the name of the currently active TTS backend."""
    return _ACTIVE_TTS


def speak(text: str, emotion_snapshot: dict = None, backend: str = None):
    """
    Convert kernel response text to speech.

    Args:
        text:             The response string from kernel.decide_response().
        emotion_snapshot: The emotion snapshot dict from StateBus or event bus.
                          Keys: emotion, tone, pacing, warmth.
                          Pass None for neutral voice parameters.
        backend:          Override the active backend for this call only.
                          "print" | "pyttsx3" | "elevenlabs"

    No kernel changes. Reads existing outputs only.
    """
    if not text or not text.strip():
        return

    params  = _resolve_params(emotion_snapshot)
    engine  = (backend or _ACTIVE_TTS).lower()

    if engine == "pyttsx3":
        _speak_pyttsx3(text, params)
    elif engine == "elevenlabs":
        _speak_elevenlabs(text, params)
    else:
        _speak_print(text, params)


def voice_params_for(emotion_snapshot: dict) -> dict:
    """
    Return the voice parameter dict for a given emotion snapshot.
    Useful for preview / testing without actually speaking.
    """
    return _resolve_params(emotion_snapshot)
