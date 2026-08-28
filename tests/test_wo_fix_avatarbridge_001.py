"""
tests/test_wo_fix_avatarbridge_001.py — WO-FIX-AVATARBRIDGE-001

AT-1: from_state + orb_intensity importable from core.emotion_engine
AT-2: core.avatar_bridge importable (the defect import chain resolved)
AT-3: from_state("idle") returns all five required keys with correct types
AT-4: from_state("conversing", ...) returns energy in [0.0, 1.0]
AT-5: from_state("unknown_state_xyz") returns all five keys, no error
AT-6: orb_intensity(0.7, "curious") returns float in [0.0, 1.0]
AT-7: orb_intensity(0.0, "idle") returns value near zero
AT-8: get_avatar_signal(state="idle", response_text="Hello") has "orb" as float
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── AT-1: import ──────────────────────────────────────────────────────────────

def test_at1_from_state_orb_intensity_importable():
    from core.emotion_engine import from_state, orb_intensity
    assert callable(from_state)
    assert callable(orb_intensity)


# ── AT-2: avatar_bridge importable ───────────────────────────────────────────

def test_at2_avatar_bridge_importable():
    from core.avatar_bridge import get_avatar_signal
    assert callable(get_avatar_signal)


# ── AT-3: from_state("idle") keys and types ──────────────────────────────────

def test_at3_from_state_idle_has_all_keys():
    from core.emotion_engine import from_state
    result = from_state("idle")
    assert isinstance(result, dict), "from_state must return a dict"
    assert isinstance(result["emotion"], str),  "emotion must be str"
    assert isinstance(result["intent"],  str),  "intent must be str"
    assert isinstance(result["posture"], str),  "posture must be str"
    assert isinstance(result["pace"],    str),  "pace must be str"
    assert isinstance(result["energy"],  float),"energy must be float"


# ── AT-4: energy in [0.0, 1.0] ───────────────────────────────────────────────

def test_at4_from_state_conversing_energy_in_range():
    from core.emotion_engine import from_state
    result = from_state("conversing", input_emotion="happy", mode="companion")
    assert 0.0 <= result["energy"] <= 1.0, (
        f"energy out of range: {result['energy']}"
    )


# ── AT-5: unknown state → no error ───────────────────────────────────────────

def test_at5_from_state_unknown_state_no_error():
    from core.emotion_engine import from_state
    result = from_state("unknown_state_xyz")
    assert isinstance(result, dict)
    for key in ("emotion", "intent", "posture", "pace", "energy"):
        assert key in result, f"missing key: {key}"


# ── AT-6: orb_intensity range ────────────────────────────────────────────────

def test_at6_orb_intensity_curious_in_range():
    from core.emotion_engine import orb_intensity
    result = orb_intensity(0.7, "curious")
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0, f"orb_intensity out of range: {result}"


# ── AT-7: orb_intensity near zero when energy=0 ─────────────────────────────

def test_at7_orb_intensity_zero_energy():
    from core.emotion_engine import orb_intensity
    result = orb_intensity(0.0, "idle")
    assert isinstance(result, float)
    assert result <= 0.1, f"expected near-zero orb_intensity, got {result}"


# ── AT-8: end-to-end get_avatar_signal has orb as float ──────────────────────

def test_at8_get_avatar_signal_has_orb_float():
    from core.avatar_bridge import get_avatar_signal
    result = get_avatar_signal(state="idle", response_text="Hello")
    assert isinstance(result, dict), "get_avatar_signal must return a dict"
    assert "orb" in result, "'orb' key missing from avatar signal"
    assert isinstance(result["orb"], float), f"orb must be float, got {type(result['orb'])}"
    assert 0.0 <= result["orb"] <= 1.0, f"orb out of range: {result['orb']}"
