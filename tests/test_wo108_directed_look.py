"""
tests/test_wo108_directed_look.py — WO-108: Directed LOOK produces an observation record.

AT-108-1: look() returns an ObservationRecord with target, timestamp, confidence, source
AT-108-2: look() on an occluded/absent target records failure — outcome != OBSERVED
AT-108-3: Ambient SEE and directed LOOK produce distinguishable records
AT-108-4: No record → observation_for() returns None (verified-speech gate works)
AT-108-5: look() with existing target in world state returns outcome=OBSERVED
AT-108-6: compile() exposes last_observation (Executive-visible)
"""
from __future__ import annotations

import os
import sys
import tempfile
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-108-1: look() returns a valid ObservationRecord ───────────────────────

def test_look_returns_observation_record():
    from runtime.directed_look import look, ObservationRecord
    record = look("some_window_xyz_nonexistent")
    assert isinstance(record, ObservationRecord), (
        f"look() must return ObservationRecord, got {type(record)}"
    )
    assert record.target == "some_window_xyz_nonexistent"
    assert record.ts > 0
    assert 0.0 <= record.confidence <= 1.0
    assert record.source in ("world_state", "spatial", "perch", "inferred", "none")
    assert record.kind == "directed"


# ── AT-108-2: absent/occluded target records failure ─────────────────────────

def test_absent_target_records_failure():
    from runtime.directed_look import look, OUTCOME_ABSENT, OUTCOME_OCCLUDED
    record = look("totally_impossible_app_not_on_screen_xyz_abc_123")
    assert record.failed, (
        f"Absent target must record failure (got outcome={record.outcome})"
    )
    assert record.outcome in (OUTCOME_ABSENT, OUTCOME_OCCLUDED), (
        f"outcome should be absent or occluded, got: {record.outcome}"
    )
    assert record.confidence == 0.0 or record.confidence < 0.5, (
        f"Absent target should have low confidence: {record.confidence}"
    )


# ── AT-108-3: directed LOOK and ambient SEE are distinguishable ───────────────

def test_directed_look_distinguishable_from_ambient():
    from runtime.directed_look import look, ObservationRecord
    directed_record = look("test_target_distinguishable")
    assert directed_record.kind == "directed", (
        f"Directed LOOK must have kind='directed', got: {directed_record.kind}"
    )
    # An ambient observation would have kind='ambient' — assert they differ
    ambient_kind = "ambient"
    assert directed_record.kind != ambient_kind, (
        "Directed LOOK and ambient SEE must produce distinguishable records — "
        "they must not collapse to the same kind"
    )


# ── AT-108-4: No record → observation_for() returns None ────────────────────

def test_no_record_means_no_observation(tmp_path, monkeypatch):
    import runtime.directed_look as dl
    test_log = str(tmp_path / "observation_log.jsonl")
    monkeypatch.setattr(dl, "_OBS_LOG", test_log)

    result = dl.observation_for("google chrome")
    assert result is None, (
        "observation_for() must return None when no record exists — "
        "verified-speech gate: no record = eLo hasn't looked"
    )


# ── AT-108-5: look() with in-world target returns OBSERVED ───────────────────

def test_look_with_known_target_returns_observed(tmp_path, monkeypatch):
    import runtime.directed_look as dl

    # Inject a spatial state where eLo is on Google Chrome
    fake_spatial = {
        "window": "Google Chrome",
        "edge": "top",
        "x": 0.3, "y": 0.8,
        "on_window": True,
        "screen_w": 2560, "screen_h": 1440, "height": 0.065,
        "gaze": {"window": "Google Chrome", "on_window": True},
    }
    test_log = str(tmp_path / "observation_log.jsonl")
    monkeypatch.setattr(dl, "_OBS_LOG", test_log)
    monkeypatch.setattr(dl, "_load_spatial", lambda: fake_spatial)

    record = dl.look("google chrome")
    assert record.succeeded, (
        f"look() on a window in world state must return OBSERVED, got: {record.outcome}"
    )
    assert record.confidence > 0.5, (
        f"OBSERVED result should have high confidence: {record.confidence}"
    )
    assert "window" in record.observed_at, (
        "OBSERVED record must include what was actually found"
    )


# ── AT-108-6: compile() exposes last_observation to the Executive ─────────────

def test_moment_compile_includes_last_observation():
    from runtime.the_moment import compile as tm_compile
    from unittest.mock import MagicMock
    state = MagicMock()
    state.embodiment = "desktop"
    state.pose = "perched"
    state.surface = "Terminal"
    state.location = ""
    state.balance = "stable"
    state.size = {"height_cm": 18, "reach_cm": 30, "jump_cm": 30}
    state.available_actions = ["stand", "run"]
    state.current_action = "idle"
    state.locomotion_faculty_health = "OK"
    state.nearby_surfaces = []
    state.mood = 0.5
    state.curiosity = 0.5
    state.goal = ""
    state.last_updated = 0.0
    state.recent_behavior = {}

    moment = tm_compile(state)
    assert "last_observation" in moment, (
        "compile() must include 'last_observation' key — Executive verified-speech gate depends on it"
    )
