"""runtime/pre_ack.py — B3 pre-acknowledgement for slow tool operations.

B3 calls pre_ack.emit(capability, user_text) at the top of any slow operation
(document write, device control, Spotify) so eLo says something while the
work runs in the background.

Design:
    emit() fires a background TTS thread via voice_engine.speak() and returns
    in < 1 ms. No server-side poll needed. No ack_pending in blender_state.json
    (that interim guidance is superseded by this module — B3 should use emit()
    directly once this module lands).

Never raises. A pre-ack that does not form is no pre-ack, never a failed turn.

B3 usage pattern:
    # In tools/document_writer.py, before the slow write:
    from runtime import pre_ack
    pre_ack.emit("document_write", user_request)
    # ... start the slow operation
"""
from __future__ import annotations

import logging
import random

_log = logging.getLogger("elo.pre_ack")

# Capability → candidate ack phrases. Kept short — this fires before a slow op;
# the main response will follow once the op finishes.
_PHRASES: dict[str, list[str]] = {
    "document_write": [
        "Give me a second, I'll write that up.",
        "On it. Writing that up now.",
        "Let me put that together.",
        "Give me a moment, I'm on it.",
    ],
    "device_control": [
        "Give me a second.",
        "On it.",
        "Right, doing that.",
        "Let me handle that.",
    ],
    "spotify_play": [
        "One second.",
        "Let me find that.",
        "On it.",
        "Give me a moment.",
    ],
    "default": [
        "Give me a second.",
        "On it.",
        "Let me sort that.",
        "One moment.",
    ],
}


def emit(capability: str = "default", user_text: str = "") -> None:
    """Speak a brief ack phrase before a slow capability starts.

    Fires a background TTS thread and returns immediately (< 1 ms).
    Never blocks the caller. capability selects the phrase bank.
    user_text is accepted but not used — reserved for future phrase
    personalisation from the turn context.
    """
    try:
        bank = _PHRASES.get(capability) or _PHRASES["default"]
        phrase = random.choice(bank)
        from voice.voice_engine import speak as _speak
        _speak(phrase)
    except Exception as _e:
        _log.debug("pre_ack.emit failed (non-fatal): %s", _e)
