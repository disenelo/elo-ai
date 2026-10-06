"""
tests/test_wo_perception_001.py — WO-PERCEPTION-001: perception + environment delta

Acceptance criteria:
  PERC-1: perceive() returns snapshot with known keys
  PERC-2: perceive() returns empty delta on first call (no previous snapshot)
  PERC-3: perceive() detects change when blender_state changes
  PERC-4: high_sig_change is True when presence_mode changes
  PERC-5: CognitiveState has environment_delta + perception_changed fields
  PERC-6: format_delta_for_vault produces readable text
"""
import json
import os
import tempfile
import pytest


def _make_bs(mode="idle", emotion="neutral", asleep=False, battery=0.5):
    return {
        "state": {"mode": mode, "emotion": emotion, "energy": 0.5},
        "asleep": asleep,
        "dream_phase": None,
        "elo_battery": battery,
        "activity_recent": None,
        "weather": "cloudy",
    }


# ── PERC-1: snapshot has known keys ───────────────────────────────────────────

def test_perc1_snapshot_keys():
    """PERC-1: perceive() returns snapshot with all expected perception keys"""
    from runtime.perception_faculty import perceive, reset
    reset()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(_make_bs(), f)
        path = f.name
    try:
        result = perceive(path)
        assert "snapshot" in result
        assert "presence_mode" in result["snapshot"]
        assert "emotion" in result["snapshot"]
        assert "asleep" in result["snapshot"]
    finally:
        os.unlink(path)


# ── PERC-2: first call produces empty delta ────────────────────────────────────

def test_perc2_first_call_empty_delta():
    """PERC-2: first call after reset() produces empty delta (no previous to compare)"""
    from runtime.perception_faculty import perceive, reset
    reset()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(_make_bs(), f)
        path = f.name
    try:
        result = perceive(path)
        assert result["delta"] == {}
        assert result["perception_changed"] is False
    finally:
        os.unlink(path)


# ── PERC-3: detects field change between turns ────────────────────────────────

def test_perc3_detects_change():
    """PERC-3: second call detects when environment field changed"""
    from runtime.perception_faculty import perceive, reset
    reset()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(_make_bs(mode="idle"), f)
        path = f.name
    try:
        perceive(path)  # first call — establishes baseline
        # write a changed state
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_make_bs(mode="calm"), f)
        result2 = perceive(path)
        assert result2["perception_changed"] is True
        assert "presence_mode" in result2["delta"]
        assert result2["delta"]["presence_mode"] == ("idle", "calm")
    finally:
        os.unlink(path)


# ── PERC-4: high_sig_change on presence_mode change ──────────────────────────

def test_perc4_high_sig_on_mode_change():
    """PERC-4: high_sig_change is True when presence_mode (high-significance) changes"""
    from runtime.perception_faculty import perceive, reset
    reset()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(_make_bs(mode="idle"), f)
        path = f.name
    try:
        perceive(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_make_bs(mode="speaking"), f)
        result2 = perceive(path)
        assert result2["high_sig_change"] is True
    finally:
        os.unlink(path)


# ── PERC-5: CognitiveState has perception fields ──────────────────────────────

def test_perc5_cognitive_state_fields():
    """PERC-5: CognitiveState has environment_delta and perception_changed"""
    from runtime.contracts import CognitiveState
    cs = CognitiveState()
    assert hasattr(cs, "environment_delta")
    assert cs.environment_delta == {}
    assert hasattr(cs, "perception_changed")
    assert cs.perception_changed is False
    cs2 = CognitiveState(
        environment_delta={"presence_mode": ("idle", "calm")},
        perception_changed=True,
    )
    assert cs2.perception_changed is True
    assert "presence_mode" in cs2.environment_delta


# ── PERC-6: format_delta_for_vault produces readable text ─────────────────────

def test_perc6_format_delta():
    """PERC-6: format_delta_for_vault produces human-readable OBSERVATION text"""
    from runtime.perception_faculty import format_delta_for_vault
    delta = {"presence_mode": ("idle", "calm"), "asleep": (False, True)}
    text = format_delta_for_vault(delta)
    assert "presence_mode" in text
    assert "idle" in text
    assert "calm" in text
    assert "Environment changed" in text
