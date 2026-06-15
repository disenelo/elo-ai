"""
plugins/voice/voice_engine.py — TTS output + phoneme → shape key mapping.

NOT ACTIVE YET. Scaffolding for when voice is wired in.

Flow when active:
    1. eLo response text → TTS (system voice or local model)
    2. TTS audio plays
    3. Phoneme sequence extracted from text
    4. Phonemes mapped to viseme shape key values
    5. Shape keys pushed alongside motion to blender_bridge/state_writer

Phoneme → viseme map uses eLo's actual shape keys on 'eLo-BodyxHead w/Mouth':
    Ah, Mbp, Mmmm, Eh, Ai, Oooh, Fv, FvS, S, Ee
"""
from __future__ import annotations

# phoneme → eLo shape key blend
# values kept within safe ranges (most keys run -5 to 5; stay within ±1)
PHONEME_VISEMES: dict[str, dict] = {
    "m":  {"Mbp": 0.8, "MouthOpen.Slightly": -0.1},
    "b":  {"Mbp": 0.7},
    "p":  {"Mbp": 0.9},
    "aa": {"Ah": 0.9, "JawOpening": 0.4, "MouthOpen.Wide": 0.3},
    "ah": {"Ah": 0.7, "JawOpening": 0.3},
    "aw": {"Ah": 0.5, "Oooh": 0.3},
    "ow": {"Oooh": 0.8, "MouthWidth.L": -0.2, "MouthWidth.R": -0.2},
    "oo": {"Oooh": 0.9, "MouthWidth.L": -0.3, "MouthWidth.R": -0.3},
    "ee": {"Ee": 0.9, "Smile.L": 0.3, "Smile.R": 0.3},
    "ih": {"Ee": 0.5},
    "eh": {"Eh": 0.8, "MouthOpen.Slightly": 0.2},
    "ae": {"Eh": 0.6, "Ah": 0.3},
    "ay": {"Ai": 0.8, "MouthOpen.Slightly": 0.2},
    "ai": {"Ai": 0.9},
    "f":  {"Fv": 0.8},
    "v":  {"FvS": 0.7},
    "s":  {"S": 0.8},
    "z":  {"S": 0.6},
    "sh": {"Oooh": 0.3, "S": 0.4},
    "":   {"MouthOpen.Slightly": 0.0},
}

SILENCE_SHAPE: dict = {"MouthOpen.Slightly": 0.0}


def phoneme_to_shape_keys(phoneme: str) -> dict:
    return dict(PHONEME_VISEMES.get(phoneme.lower(), SILENCE_SHAPE))


def text_to_phonemes(text: str) -> list:
    """Placeholder — real impl: phonemizer / espeak / CMU dict."""
    return []


def speak(text: str) -> None:
    """Placeholder — real impl: subprocess say / pyttsx3 / local TTS model."""
    pass
