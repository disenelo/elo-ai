"""
voice/stt.py — Speech-to-text for eLo OS.

Records from the default microphone until silence, then transcribes via:
    1. OpenAI Whisper API   (OPENAI_API_KEY present — fast, accurate)
    2. Local whisper model  (ELO_STT_ENGINE=whisper_local — needs: pip install openai-whisper)
    3. stdin fallback       (ELO_STT_ENGINE=stdin — useful in headless / test environments)

Config (.env):
    ELO_STT_ENGINE      "whisper_api" | "whisper_local" | "stdin"  (default: whisper_api)
    ELO_WHISPER_MODEL   "tiny" | "base" | "small" | "medium"       (local only, default: base)
    ELO_MIC_MAX_SEC     Max recording seconds                       (default: 15)
    ELO_MIC_SILENCE_SEC Seconds of silence before auto-stop         (default: 1.5)
    ELO_MIC_DEVICE      sounddevice device index or name            (default: system default)

Public API:
    capture() → str    Block until spoken, return transcribed text (empty string on failure)
    is_available() → bool
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import wave
from pathlib import Path
from typing import Optional


# ── Config ────────────────────────────────────────────────────────────────────

def _engine() -> str:
    """Read ELO_STT_ENGINE from env. Defaults to whisper_api when key is set, else stdin."""
    e = os.environ.get("ELO_STT_ENGINE", "").strip().lower()
    if e:
        return e
    return "whisper_api" if os.environ.get("OPENAI_API_KEY", "").strip() else "stdin"


def _max_sec() -> float:
    try:
        return float(os.environ.get("ELO_MIC_MAX_SEC", "15"))
    except ValueError:
        return 15.0


def _silence_sec() -> float:
    try:
        return float(os.environ.get("ELO_MIC_SILENCE_SEC", "1.5"))
    except ValueError:
        return 1.5


def _whisper_model() -> str:
    return os.environ.get("ELO_WHISPER_MODEL", "base").strip()


def _mic_device() -> Optional[int | str]:
    v = os.environ.get("ELO_MIC_DEVICE", "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return v


# ── Mic recording ─────────────────────────────────────────────────────────────

_SAMPLE_RATE   = 16000   # Whisper expects 16kHz
_CHANNELS      = 1
_DTYPE         = "int16"
_SILENCE_RMS   = 300     # RMS threshold below which audio is considered silence
_WARMUP_FRAMES = 5       # ignore first N frames (mic init transient)


def _rms(chunk) -> float:
    import numpy as np
    return float(np.sqrt(np.mean(chunk.astype("float64") ** 2)))


def record_to_wav(max_sec: float | None = None, silence_sec: float | None = None) -> Optional[Path]:
    """
    Record from mic until silence or max_sec. Returns path to a temp WAV file,
    or None on failure (no sounddevice, no mic, etc.).
    Caller is responsible for deleting the temp file.
    """
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print("[stt] sounddevice not installed — pip install sounddevice", file=sys.stderr)
        return None

    max_s = max_sec if max_sec is not None else _max_sec()
    sil_s = silence_sec if silence_sec is not None else _silence_sec()
    device = _mic_device()

    frame_dur = 0.05   # 50ms frames
    frame_samples = int(_SAMPLE_RATE * frame_dur)
    max_frames    = int(max_s / frame_dur)
    sil_frames    = int(sil_s / frame_dur)

    frames_recorded: list = []
    silent_count = 0
    frame_count  = 0

    try:
        with sd.InputStream(
            samplerate=_SAMPLE_RATE,
            channels=_CHANNELS,
            dtype=_DTYPE,
            blocksize=frame_samples,
            device=device,
        ) as stream:
            print("[stt] recording…", end=" ", flush=True)
            while frame_count < max_frames:
                chunk, _ = stream.read(frame_samples)
                frame_count += 1

                if frame_count <= _WARMUP_FRAMES:
                    continue

                frames_recorded.append(chunk.copy())
                rms = _rms(chunk)

                if rms < _SILENCE_RMS:
                    silent_count += 1
                    if silent_count >= sil_frames and frames_recorded:
                        break
                else:
                    silent_count = 0

        print(f"done ({frame_count} frames)", flush=True)

    except Exception as e:
        print(f"\n[stt] mic error: {e}", file=sys.stderr)
        return None

    if not frames_recorded:
        return None

    import numpy as np
    audio = np.concatenate(frames_recorded, axis=0)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    try:
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(_CHANNELS)
            wf.setsampwidth(2)   # int16 = 2 bytes
            wf.setframerate(_SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        return Path(tmp.name)
    except Exception as e:
        print(f"[stt] WAV write error: {e}", file=sys.stderr)
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        return None


# ── Whisper API transcription ─────────────────────────────────────────────────

def _transcribe_whisper_api(wav_path: Path) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        with open(wav_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
                language=os.environ.get("ELO_STT_LANGUAGE", "en").strip() or None,
            )
        text = str(result).strip()
        print(f"[stt] whisper_api → '{text}'")
        return text
    except Exception as e:
        print(f"[stt] whisper_api error: {e}", file=sys.stderr)
        return ""


# ── Local Whisper transcription ───────────────────────────────────────────────

_local_model_cache: dict = {}


def _transcribe_whisper_local(wav_path: Path) -> str:
    model_name = _whisper_model()
    try:
        import whisper
        if model_name not in _local_model_cache:
            print(f"[stt] loading local whisper model '{model_name}'…")
            _local_model_cache[model_name] = whisper.load_model(model_name)
        model = _local_model_cache[model_name]
        result = model.transcribe(str(wav_path))
        text = result.get("text", "").strip()
        print(f"[stt] whisper_local → '{text}'")
        return text
    except ImportError:
        print("[stt] local whisper not installed — pip install openai-whisper", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"[stt] whisper_local error: {e}", file=sys.stderr)
        return ""


# ── stdin fallback ────────────────────────────────────────────────────────────

def _capture_stdin() -> str:
    try:
        text = input("[stt/stdin] speak (type): ").strip()
        return text
    except (EOFError, KeyboardInterrupt):
        return ""


# ── Public API ────────────────────────────────────────────────────────────────

def is_available() -> bool:
    """True if any STT engine can run in this environment."""
    engine = _engine()
    if engine == "stdin":
        return True
    if engine == "whisper_local":
        try:
            import whisper  # noqa: F401
            import sounddevice  # noqa: F401
            return True
        except ImportError:
            return False
    # whisper_api: needs key + sounddevice
    try:
        import sounddevice  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def capture() -> str:
    """
    Block until the user finishes speaking. Returns transcribed text, or "" on failure.
    Engine priority: ELO_STT_ENGINE → auto-detect based on keys present.
    """
    engine = _engine()

    if engine == "stdin":
        return _capture_stdin()

    wav_path = record_to_wav()
    if not wav_path:
        print("[stt] no audio captured", file=sys.stderr)
        return ""

    try:
        if engine == "whisper_local":
            return _transcribe_whisper_local(wav_path)
        # whisper_api (default) — fallback to local if API key missing
        text = _transcribe_whisper_api(wav_path)
        if not text:
            print("[stt] whisper_api empty — trying local fallback")
            text = _transcribe_whisper_local(wav_path)
        return text
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass
