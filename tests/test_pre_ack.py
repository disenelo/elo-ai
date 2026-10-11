"""tests/test_pre_ack.py — runtime/pre_ack.py AT suite.

WO: B3 pre-acknowledgement for slow tool operations.
Run: python3 -m pytest tests/test_pre_ack.py -v
"""
import sys
import os
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ── Stub voice_engine so tests never fire actual TTS ─────────────────────────
_spoken: list[str] = []

def _fake_speak(text: str) -> None:
    _spoken.append(text)

_ve_stub = types.ModuleType("voice.voice_engine")
_ve_stub.speak = _fake_speak
_ve_stub.speak_inner = _fake_speak
sys.modules["voice"] = types.ModuleType("voice")
sys.modules["voice.voice_engine"] = _ve_stub

# ── Re-import after stub is in place ──────────────────────────────────────────
import importlib
import runtime.pre_ack as _pa
importlib.reload(_pa)


def setup_function():
    _spoken.clear()


# ── AT-1: emit with known capability selects from correct bank ────────────────
def test_at1_document_write_bank():
    _pa.emit("document_write", "write the robot spec")
    assert len(_spoken) == 1
    assert _spoken[0] in _pa._PHRASES["document_write"], \
        f"Unexpected phrase for document_write: {_spoken[0]!r}"


# ── AT-2: device_control uses its bank ───────────────────────────────────────
def test_at2_device_control_bank():
    _pa.emit("device_control")
    assert len(_spoken) == 1
    assert _spoken[0] in _pa._PHRASES["device_control"]


# ── AT-3: spotify_play uses its bank ─────────────────────────────────────────
def test_at3_spotify_bank():
    _pa.emit("spotify_play")
    assert len(_spoken) == 1
    assert _spoken[0] in _pa._PHRASES["spotify_play"]


# ── AT-4: unknown capability falls back to default bank ──────────────────────
def test_at4_unknown_capability_defaults():
    _pa.emit("calendar_write")
    assert len(_spoken) == 1
    assert _spoken[0] in _pa._PHRASES["default"]


# ── AT-5: bare emit() call (no args) works ───────────────────────────────────
def test_at5_bare_emit():
    _pa.emit()
    assert len(_spoken) == 1
    assert _spoken[0] in _pa._PHRASES["default"]


# ── AT-6: emit never raises even when voice fails ─────────────────────────────
def test_at6_emit_never_raises_on_voice_failure(monkeypatch):
    def _bad_speak(text):
        raise RuntimeError("TTS offline")
    monkeypatch.setattr(_pa, "_PHRASES", {"default": ["test phrase"]})
    import voice.voice_engine as _vem
    original = _vem.speak
    _vem.speak = _bad_speak
    try:
        _pa.emit("default")  # must not raise
    finally:
        _vem.speak = original


# ── AT-7: user_text arg accepted but does not change phrase bank ──────────────
def test_at7_user_text_ignored():
    _pa.emit("document_write", user_text="write up the robot shell seam please")
    assert len(_spoken) == 1
    assert _spoken[0] in _pa._PHRASES["document_write"]


# ── AT-8: consecutive emits both fire ────────────────────────────────────────
def test_at8_consecutive_emits():
    _pa.emit("document_write")
    _pa.emit("device_control")
    assert len(_spoken) == 2
