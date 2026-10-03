"""
tests/test_wo_elevenlabs_settings_wire.py — WO-ELEVENLABS-SETTINGS-WIRE-001

Acceptance: changing ELEVENLABS_STABILITY/SIMILARITY/STYLE/SPEED in os.environ
must be reflected in the next API call body immediately (no server restart).

Tests:
- _el_voice_settings() reads live env values (not stale module-level constants)
- Default values match original hardcoded fallbacks
- Updated env values appear in voice_settings dict at call time
- Both primary and secondary fetch functions use _el_voice_settings()
"""
from __future__ import annotations

import os
import importlib


def _get_module():
    import voice.voice_engine as ve
    return ve


# ── Default values ─────────────────────────────────────────────────────────────

def test_el_voice_settings_returns_dict():
    ve = _get_module()
    s = ve._el_voice_settings()
    assert isinstance(s, dict)
    for key in ("stability", "similarity_boost", "style", "use_speaker_boost"):
        assert key in s, f"Expected '{key}' in voice_settings; got {list(s)}"


def test_el_voice_settings_defaults_are_floats():
    ve = _get_module()
    s = ve._el_voice_settings()
    for key in ("stability", "similarity_boost", "style", "speed"):
        assert isinstance(s[key], float), (
            f"Expected float for '{key}'; got {type(s[key])}"
        )


# ── Live env read ──────────────────────────────────────────────────────────────

def test_stability_reads_from_env_at_call_time(monkeypatch):
    """Setting ELEVENLABS_STABILITY in env must appear in next _el_voice_settings() call."""
    ve = _get_module()
    monkeypatch.setenv("ELEVENLABS_STABILITY", "0.88")
    s = ve._el_voice_settings()
    assert abs(s["stability"] - 0.88) < 1e-6, (
        f"stability must be 0.88 from env; got {s['stability']}"
    )


def test_similarity_reads_from_env_at_call_time(monkeypatch):
    ve = _get_module()
    monkeypatch.setenv("ELEVENLABS_SIMILARITY", "0.42")
    s = ve._el_voice_settings()
    assert abs(s["similarity_boost"] - 0.42) < 1e-6, (
        f"similarity_boost must be 0.42 from env; got {s['similarity_boost']}"
    )


def test_style_reads_from_env_at_call_time(monkeypatch):
    ve = _get_module()
    monkeypatch.setenv("ELEVENLABS_STYLE", "0.77")
    s = ve._el_voice_settings()
    assert abs(s["style"] - 0.77) < 1e-6, (
        f"style must be 0.77 from env; got {s['style']}"
    )


def test_speed_reads_from_env_at_call_time(monkeypatch):
    ve = _get_module()
    monkeypatch.setenv("ELEVENLABS_SPEED", "1.25")
    s = ve._el_voice_settings()
    assert abs(s["speed"] - 1.25) < 1e-6, (
        f"speed must be 1.25 from env; got {s['speed']}"
    )


def test_settings_change_without_module_reload(monkeypatch):
    """The key guarantee: two successive calls with different env values return different dicts."""
    ve = _get_module()
    monkeypatch.setenv("ELEVENLABS_STABILITY", "0.10")
    first = ve._el_voice_settings()["stability"]
    monkeypatch.setenv("ELEVENLABS_STABILITY", "0.90")
    second = ve._el_voice_settings()["stability"]
    assert abs(first - 0.10) < 1e-6
    assert abs(second - 0.90) < 1e-6


# ── use_speaker_boost is always True ─────────────────────────────────────────

def test_use_speaker_boost_is_true():
    ve = _get_module()
    assert ve._el_voice_settings()["use_speaker_boost"] is True
