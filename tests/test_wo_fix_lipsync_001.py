"""
tests/test_wo_fix_lipsync_001.py — WO-FIX-LIPSYNC-001

AT-1: _pulse_lipsync forwards text="Hello world" to write_lipsync
AT-2: _pulse_lipsync forwards text="" (default) to write_lipsync
AT-3: stop event pre-set → write_lipsync NOT called
AT-4: _pulse_lipsync signature accepts text as keyword argument
AT-5: import voice.voice_engine cleanly with no error
"""
import inspect
import os
import sys
import threading
from unittest.mock import patch, call

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import voice.voice_engine as _ve


# ── AT-5: clean import ────────────────────────────────────────────────────────

def test_at5_import_voice_engine_clean():
    """voice.voice_engine must import without error."""
    assert _ve is not None


# ── AT-4: signature ───────────────────────────────────────────────────────────

def test_at4_pulse_lipsync_accepts_text_kwarg():
    """_pulse_lipsync signature must include a 'text' keyword parameter."""
    sig = inspect.signature(_ve._pulse_lipsync)
    assert "text" in sig.parameters, "_pulse_lipsync has no 'text' parameter"
    param = sig.parameters["text"]
    assert param.default == "", f"text default should be '' not {param.default!r}"


# ── AT-1: text forwarded when provided ───────────────────────────────────────

def test_at1_text_forwarded_to_write_lipsync():
    """_pulse_lipsync must call write_lipsync with text='Hello world'."""
    stop = threading.Event()
    phonemes = [("AH", 0.0)]  # zero duration so test doesn't sleep

    with patch("voice.voice_engine.write_lipsync") as mock_wl:
        _ve._pulse_lipsync(phonemes, stop, text="Hello world")

    assert mock_wl.called, "write_lipsync was not called"
    _, kwargs = mock_wl.call_args
    assert kwargs.get("text") == "Hello world", (
        f"write_lipsync was not called with text='Hello world'; kwargs={kwargs}"
    )


# ── AT-2: empty text (default) forwarded ─────────────────────────────────────

def test_at2_empty_text_forwarded_to_write_lipsync():
    """_pulse_lipsync must call write_lipsync with text='' when no text given."""
    stop = threading.Event()
    phonemes = [("AH", 0.0)]

    with patch("voice.voice_engine.write_lipsync") as mock_wl:
        _ve._pulse_lipsync(phonemes, stop)

    assert mock_wl.called, "write_lipsync was not called"
    _, kwargs = mock_wl.call_args
    assert kwargs.get("text") == "", (
        f"write_lipsync text kwarg should be '' not {kwargs.get('text')!r}"
    )


# ── AT-3: stop pre-set → no write_lipsync call ───────────────────────────────

def test_at3_stop_preset_suppresses_write_lipsync():
    """When stop is pre-set, _pulse_lipsync must NOT call write_lipsync."""
    stop = threading.Event()
    stop.set()
    phonemes = [("AH", 0.0)]

    with patch("voice.voice_engine.write_lipsync") as mock_wl:
        _ve._pulse_lipsync(phonemes, stop, text="Should not appear")

    assert not mock_wl.called, "write_lipsync must not be called when stop is pre-set"
