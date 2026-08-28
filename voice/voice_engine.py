"""
voice/voice_engine.py — TTS + lipsync for eLo OS.

Primary:  OpenAI TTS (tts-1-hd, voice=shimmer) — natural, childlike quality.
Fallback: macOS `say` — used when OPENAI_API_KEY is absent or API fails.

Architecture:
  speak(text) spawns a background thread that:
    1. Fetches audio from OpenAI TTS API (or falls back to `say`).
    2. Plays audio via afplay (OpenAI) or say subprocess.
    3. Simultaneously pulses lipsync shapes into blender_state.json at ~50ms.
    4. Clears mouth shapes when speech ends.

Config (.env):
    OPENAI_API_KEY=sk-...       required for OpenAI TTS
    ELO_TTS_VOICE=shimmer       OpenAI voice (shimmer/nova/alloy/echo/fable/onyx)
    ELO_TTS_SPEED=1.0           OpenAI speech speed (0.25–4.0)
    ELO_VOICE=Junior            fallback macOS voice
    ELO_RATE=160                fallback macOS wpm
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import threading
import time
from typing import Optional

from blender_bridge.lipsync_writer import write_lipsync, clear_lipsync

# ── Config ────────────────────────────────────────────────────────────────────

_OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
_TTS_VOICE    = os.environ.get("ELO_TTS_VOICE",  "shimmer")   # childlike, light
_TTS_SPEED    = float(os.environ.get("ELO_TTS_SPEED", "1.0"))
_TTS_URL      = "https://api.openai.com/v1/audio/speech"

_EL_KEY    = os.environ.get("ELEVENLABS_API_KEY", "")
_EL_VOICE  = os.environ.get("ELEVENLABS_VOICE_ID", "")
_EL_VOICE2 = os.environ.get("ELEVENLABS_VOICE_ID_2", "")
_EL_MIX    = float(os.environ.get("ELEVENLABS_VOICE_MIX", "1.0"))  # weight of primary (0–1)
_EL_MODEL  = os.environ.get("ELEVENLABS_MODEL", "eleven_turbo_v2_5")

_SAY_VOICE    = os.environ.get("ELO_VOICE", "").strip()  # empty = use macOS system voice

# ── TTS text cleaner ──────────────────────────────────────────────────────────
# Strips emoji and variation selectors so TTS never reads "smiley face".
# Chat panel can still render the original emoji glyphs — this only cleans
# the string going to the audio API.
_EMOJI_RE = re.compile(
    "["
    "\U0001F100-\U0001FAFF"   # all emoji blocks (enclosed alphanumeric → pictographic)
    "\U00002600-\U000027BF"   # misc symbols + dingbats (✅ ⚠️ etc.)
    "\U0000FE00-\U0000FE0F"   # variation selectors (️)
    "]+",
    flags=re.UNICODE,
)

def _clean_for_tts(text: str) -> str:
    """Remove emoji and tidy whitespace — voice only, never modifies the chat string."""
    cleaned = _EMOJI_RE.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned
_SAY_RATE     = int(os.environ.get("ELO_RATE", "160"))

# ── Phoneme → blendshape mapping ─────────────────────────────────────────────

_PHONEME_SHAPES: dict[str, tuple[str, float]] = {
    "AA":   ("Ah",         0.82),
    "AH":   ("Ah",         0.65),
    "EH":   ("Eh",         0.72),
    "EE":   ("Ee",         0.80),
    "IY":   ("Ee",         0.75),
    "AY":   ("Ai",         0.72),
    "OO":   ("Oooh",       0.80),
    "UW":   ("Oooh",       0.68),
    "MM":   ("Mmmm",       0.65),
    "M":    ("Mbp",        0.92),
    "B":    ("Mbp",        0.85),
    "P":    ("Mbp",        0.90),
    "F":    ("Fv",         0.80),
    "V":    ("Fv",         0.70),
    "FV2":  ("FvS",        0.65),
    "S":    ("S",          0.75),
    "Z":    ("S",          0.58),
    "HH":   ("Huh",        0.42),
    "REST": ("Mbp",        0.0),
}

# ── Text → phoneme timing ─────────────────────────────────────────────────────

_DIGRAPHS: dict[str, tuple[str, float]] = {
    "ai": ("AY",  0.14), "ay": ("AY",  0.14),
    "ei": ("EH",  0.13), "ey": ("AY",  0.14),
    "oo": ("OO",  0.14), "ou": ("OO",  0.13), "ow": ("OO",  0.13),
    "ee": ("EE",  0.13), "ea": ("EE",  0.13),
    "mb": ("M",   0.07), "mp": ("M",   0.07), "mm": ("MM",  0.10),
    "fv": ("F",   0.07), "ph": ("F",   0.07),
    "th": ("HH",  0.06), "sh": ("S",   0.07), "ch": ("S",   0.07),
    "wh": ("HH",  0.06), "ng": ("MM",  0.07), "nk": ("MM",  0.07),
}
_VOWEL: dict[str, tuple[str, float]] = {
    "a": ("AA", 0.13), "e": ("EE", 0.11), "i": ("IY", 0.11),
    "o": ("OO", 0.12), "u": ("UW", 0.11),
}
_CONSONANT: dict[str, tuple[str, float]] = {
    "m": ("M",  0.06), "b": ("B",  0.06), "p": ("P",  0.06),
    "f": ("F",  0.06), "v": ("V",  0.06),
    "s": ("S",  0.06), "z": ("Z",  0.06),
    "h": ("HH", 0.05),
}


def _text_to_phoneme_sequence(text: str) -> list[tuple[str, float]]:
    clean = re.sub(r"[^a-z\s]", "", text.lower())
    seq: list[tuple[str, float]] = []
    i = 0
    while i < len(clean):
        ch = clean[i]
        if ch == " ":
            seq.append(("REST", 0.07))
            i += 1
            continue
        pair = clean[i:i+2]
        if pair in _DIGRAPHS:
            seq.append(_DIGRAPHS[pair])
            i += 2
            continue
        if ch in _VOWEL:
            seq.append(_VOWEL[ch])
        elif ch in _CONSONANT:
            seq.append(_CONSONANT[ch])
        else:
            seq.append(("HH", 0.05))
        i += 1
    return seq


def _build_frame(phoneme: str) -> dict[str, float]:
    frame = {
        "Ah": 0.0, "Eh": 0.0, "Ee": 0.0, "Ai": 0.0,
        "Oooh": 0.0, "Shock-Oooo": 0.0,
        "Mbp": 0.0, "Mmmm": 0.0, "Fv": 0.0, "FvS": 0.0,
        "S": 0.0, "Huh": 0.0,
    }
    if phoneme == "REST":
        return frame
    shape_name, peak = _PHONEME_SHAPES.get(phoneme, ("Huh", 0.3))
    frame[shape_name] = round(peak, 3)
    return frame


def _pulse_lipsync(phonemes: list[tuple[str, float]], stop: threading.Event, text: str = "") -> None:
    """Drive mouth shapes for the duration of the phoneme sequence."""
    for phoneme, duration in phonemes:
        if stop.is_set():
            break
        write_lipsync(_build_frame(phoneme), active=True, text=text)
        time.sleep(duration)


# ── OpenAI TTS ────────────────────────────────────────────────────────────────

def _fetch_openai_audio(text: str) -> bytes | None:
    """Call OpenAI TTS API and return raw mp3 bytes, or None on failure."""
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {_OPENAI_KEY}",
            "Content-Type":  "application/json",
        }
        body = {
            "model": "tts-1-hd",
            "input": text,
            "voice": _TTS_VOICE,
            "speed": _TTS_SPEED,
            "response_format": "mp3",
        }
        resp = httpx.post(_TTS_URL, json=body, headers=headers, timeout=15.0)
        if resp.status_code == 200:
            return resp.content
        print(f"[eLo voice] OpenAI TTS error {resp.status_code}: {resp.text[:120]}")
        return None
    except Exception as e:
        print(f"[eLo voice] OpenAI TTS exception: {e}")
        return None


def _play_openai(text: str, stop: threading.Event) -> bool:
    """Fetch from OpenAI, write to tmp file, play with afplay + lipsync. Returns True on success."""
    if stop.is_set():
        return False
    audio = _fetch_openai_audio(text)
    if not audio or stop.is_set():   # WO-019: check stop after API fetch (may have been cancelled)
        return False

    phonemes = _text_to_phoneme_sequence(text)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio)
        tmp_path = f.name

    try:
        # Start playback and lipsync simultaneously
        proc = subprocess.Popen(
            ["afplay", tmp_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _pulse_lipsync(phonemes, stop, text=text)

        if stop.is_set():
            proc.kill()              # WO-019: immediately cancel afplay when interrupted
        else:
            try:
                proc.wait(timeout=60.0)
            except subprocess.TimeoutExpired:
                proc.kill()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return True


# ── ElevenLabs TTS ───────────────────────────────────────────────────────────

def _fetch_elevenlabs_audio(text: str) -> bytes | None:
    """Call ElevenLabs TTS API and return raw mp3 bytes, or None on failure."""
    if not _EL_KEY or not _EL_VOICE:
        return None
    try:
        import httpx
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{_EL_VOICE}",
            headers={"xi-api-key": _EL_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": _EL_MODEL,
                "voice_settings": {
                    "stability": 0.35,
                    "similarity_boost": 0.70,
                    "style": 0.35,
                    "use_speaker_boost": True,
                },
            },
            timeout=15.0,
        )
        if resp.status_code == 200:
            return resp.content
        print(f"[eLo voice] ElevenLabs TTS error {resp.status_code}: {resp.text[:120]}")
        return None
    except Exception as e:
        print(f"[eLo voice] ElevenLabs TTS exception: {e}")
        return None


def _fetch_elevenlabs_audio_2(text: str) -> bytes | None:
    """Fetch from the secondary EL voice (for blending). Same settings as primary."""
    if not _EL_KEY or not _EL_VOICE2:
        return None
    try:
        import httpx
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{_EL_VOICE2}",
            headers={"xi-api-key": _EL_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": _EL_MODEL,
                "voice_settings": {
                    "stability": 0.55,
                    "similarity_boost": 0.75,
                    "style": 0.15,
                    "use_speaker_boost": True,
                },
            },
            timeout=15.0,
        )
        return resp.content if resp.status_code == 200 else None
    except Exception:
        return None


def _mix_audio(primary: bytes, secondary: bytes, primary_weight: float) -> bytes | None:
    """Blend two MP3 streams using ffmpeg amix. Returns mixed MP3 bytes or None."""
    try:
        import subprocess as _sp, tempfile as _tf
        w2 = round(1.0 - primary_weight, 3)
        with (_tf.NamedTemporaryFile(suffix=".mp3", delete=False) as f1,
              _tf.NamedTemporaryFile(suffix=".mp3", delete=False) as f2,
              _tf.NamedTemporaryFile(suffix=".mp3", delete=False) as fout):
            f1.write(primary);   p1 = f1.name
            f2.write(secondary); p2 = f2.name
            pout = fout.name
        cmd = [
            "ffmpeg", "-y",
            "-i", p1, "-i", p2,
            "-filter_complex",
            f"[0:a]volume={primary_weight}[a1];[1:a]volume={w2}[a2];[a1][a2]amix=inputs=2:duration=longest[aout]",
            "-map", "[aout]", "-codec:a", "libmp3lame", "-q:a", "4", pout,
        ]
        result = _sp.run(cmd, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        if result.returncode != 0:
            return None
        with open(pout, "rb") as f:
            mixed = f.read()
        for p in (p1, p2, pout):
            try: os.unlink(p)
            except OSError: pass
        return mixed
    except Exception as e:
        print(f"[eLo voice] ffmpeg mix error: {e}")
        return None


def _play_elevenlabs(text: str, stop: threading.Event) -> bool:
    """Fetch from ElevenLabs voice 1, play with afplay + lipsync. Returns True on success."""
    if stop.is_set():
        return False
    audio = _fetch_elevenlabs_audio(text)
    if not audio or stop.is_set():
        return False

    phonemes = _text_to_phoneme_sequence(text)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio)
        tmp_path = f.name

    try:
        proc = subprocess.Popen(
            ["afplay", tmp_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _pulse_lipsync(phonemes, stop, text=text)

        if stop.is_set():
            proc.kill()
        else:
            try:
                proc.wait(timeout=60.0)
            except subprocess.TimeoutExpired:
                proc.kill()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return True


# ── macOS say fallback ────────────────────────────────────────────────────────

def _play_say(text: str, stop: threading.Event) -> None:
    phonemes = _text_to_phoneme_sequence(text)
    try:
        cmd = ["say", "-r", str(_SAY_RATE)]
        if _SAY_VOICE:
            cmd += ["-v", _SAY_VOICE]  # empty = use macOS system default voice
        cmd.append(text)
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return

    _pulse_lipsync(phonemes, stop, text=text)

    try:
        proc.wait(timeout=30.0)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── Public API ────────────────────────────────────────────────────────────────

_active_thread: Optional[threading.Thread] = None
_stop_flag = threading.Event()


def is_speaking() -> bool:
    """Return True if a speak() thread is currently active."""
    return _active_thread is not None and _active_thread.is_alive()


def speak(text: str) -> None:
    """
    Speak eLo's response. Non-blocking — cancels any in-progress speech.
    Uses OpenAI TTS (tts-1-hd / shimmer) if OPENAI_API_KEY is set, else macOS say.
    Emoji are stripped before reaching the audio API so the voice never reads
    "smiley face" — the original string with emoji is for the chat panel only.
    """
    global _active_thread, _stop_flag

    _stop_flag.set()
    if _active_thread and _active_thread.is_alive():
        _active_thread.join(timeout=0.5)

    _stop_flag = threading.Event()
    _active_thread = threading.Thread(
        target=_speak_thread,
        args=(_clean_for_tts(text), _stop_flag),
        daemon=True,
    )
    _active_thread.start()


def _split_sentences(text: str) -> list:
    """Split response into sentences for sequential playback."""
    parts = re.split(r'(?<=[.!?…])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


# OpenAI TTS supports up to 4096 chars per call; longer text falls back sentence-by-sentence.
_OPENAI_TTS_MAX_CHARS = 4096


def _speak_thread(text: str, stop: threading.Event) -> None:
    """
    WO-019 fix: send the FULL reply as ONE TTS call to avoid per-sentence
    API round-trips. Per-sentence splits meant any slow fetch or interruption
    between sentences dropped the tail. OpenAI/EL handle multi-sentence text
    natively; only the say fallback uses sentence-by-sentence.
    """
    success = False
    # Try the full text as one call — no mid-reply truncation risk.
    if _EL_KEY and _EL_VOICE and not stop.is_set():
        success = _play_elevenlabs(text, stop)
    if not success and _OPENAI_KEY and len(text) <= _OPENAI_TTS_MAX_CHARS and not stop.is_set():
        success = _play_openai(text, stop)
    if not success:
        # macOS say fallback: sentence-by-sentence (say has no long-text API limit)
        sentences = _split_sentences(text)
        for sentence in sentences:
            if stop.is_set():
                break
            _play_say(sentence, stop)
    clear_lipsync()
