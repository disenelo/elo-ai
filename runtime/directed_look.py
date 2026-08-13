"""
runtime/directed_look.py — WO-108: Directed LOOK produces an observation record.

SEE = passive perception (ambient sweep, always running).
LOOK = deliberate allocation of perception — eLo chooses to inspect,
       and gets an observation record back.

These are not the same capability. A head rotation is not a LOOK.
eLo may claim to have looked at something ONLY if an ObservationRecord exists
for that target. No record → he says he hasn't looked.

Chain (brain half — Unity head rotation is the Design seat's half):
  INTENT → ATTENTION TARGET → PERCEPTION → OBSERVATION → RECORD → STATE UPDATE
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OBS_LOG = os.path.join(_ROOT, "self", "journals", "observation_log.jsonl")
_SPATIAL_PATH = os.path.join(_ROOT, "blender", "elo_spatial.json")
_PERCH_PATH   = os.path.join(_ROOT, "blender", "perch_state.json")

# Perception outcomes
OUTCOME_OBSERVED   = "observed"    # target found in known world state
OUTCOME_OCCLUDED   = "occluded"    # target exists but not directly perceivable
OUTCOME_ABSENT     = "absent"      # target not found in any state source
OUTCOME_PARTIAL    = "partial"     # some attributes retrieved, not all


@dataclass
class ObservationRecord:
    """
    A single directed-look result.

    Fields:
        target       — what eLo looked at (window id, name, or description)
        outcome      — OBSERVED | OCCLUDED | ABSENT | PARTIAL
        observed_at  — what was actually perceived (empty if absent/occluded)
        confidence   — 0.0–1.0 (how reliable this observation is)
        source       — "world_state" | "spatial" | "perch" | "inferred" | "none"
        ts           — Unix timestamp of the look
        kind         — "directed" | "ambient" (directed = deliberate LOOK)
    """
    target:       str
    outcome:      str
    observed_at:  dict          # what was found: {window, position, edge, ...}
    confidence:   float
    source:       str
    ts:           float
    kind:         str = "directed"

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def succeeded(self) -> bool:
        return self.outcome == OUTCOME_OBSERVED

    @property
    def failed(self) -> bool:
        return self.outcome in (OUTCOME_OCCLUDED, OUTCOME_ABSENT)


def _load_spatial() -> dict:
    try:
        with open(_SPATIAL_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_perch() -> dict:
    try:
        with open(_PERCH_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _perceive_target(target: str) -> tuple[str, dict, float, str]:
    """
    Run perception against target using available world state.

    Returns (outcome, observed_at, confidence, source).
    """
    target_lower = target.lower().strip()
    spatial = _load_spatial()
    perch   = _load_perch()

    # Check if target matches current window (highest confidence)
    current_window = (spatial.get("window") or "").lower()
    if current_window and target_lower in current_window:
        return (
            OUTCOME_OBSERVED,
            {
                "window":  spatial.get("window", ""),
                "edge":    spatial.get("edge", ""),
                "x":       spatial.get("x", 0.0),
                "y":       spatial.get("y", 0.0),
                "on_window": spatial.get("on_window", False),
            },
            0.90,
            "spatial",
        )

    # Check perch app name
    perch_app = (perch.get("app") or "").lower()
    if perch_app and target_lower in perch_app:
        return (
            OUTCOME_OBSERVED,
            {
                "window": perch.get("app", ""),
                "edge":   perch.get("edge", ""),
            },
            0.75,
            "perch",
        )

    # Check gaze target from spatial
    gaze = spatial.get("gaze", {})
    gaze_window = (gaze.get("window") or "").lower()
    if gaze_window and target_lower in gaze_window:
        return (
            OUTCOME_OBSERVED,
            {
                "window":    gaze.get("window", ""),
                "on_window": gaze.get("on_window", False),
            },
            0.65,
            "spatial",
        )

    # Target not found in any active state source → absent
    if target_lower:
        return (
            OUTCOME_ABSENT,
            {},
            0.0,
            "none",
        )

    return (OUTCOME_ABSENT, {}, 0.0, "none")


def look(target: str) -> ObservationRecord:
    """
    Execute a directed LOOK at target. Returns an ObservationRecord.

    This is the core of WO-108: a head rotation is not a LOOK.
    LOOK requires a perception attempt and a result record.

    Args:
        target: window name, app title, or spatial description

    Returns ObservationRecord — always (even on failure, outcome=absent).
    """
    if not target:
        return ObservationRecord(
            target="",
            outcome=OUTCOME_ABSENT,
            observed_at={},
            confidence=0.0,
            source="none",
            ts=time.time(),
            kind="directed",
        )

    outcome, observed_at, confidence, source = _perceive_target(target)

    record = ObservationRecord(
        target=target,
        outcome=outcome,
        observed_at=observed_at,
        confidence=confidence,
        source=source,
        ts=time.time(),
        kind="directed",
    )

    _persist(record)
    return record


def _persist(record: ObservationRecord) -> None:
    """Append observation record to the log. Append-only."""
    try:
        os.makedirs(os.path.dirname(_OBS_LOG), exist_ok=True)
        with open(_OBS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
    except Exception:
        pass


def last_observation(n: int = 1) -> list[ObservationRecord]:
    """Return the last n directed observation records, newest last."""
    try:
        with open(_OBS_LOG, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        records = [ObservationRecord(**json.loads(l)) for l in lines]
        return records[-n:]
    except Exception:
        return []


def observation_for(target: str) -> Optional[ObservationRecord]:
    """Return the most recent observation record for a specific target."""
    target_lower = (target or "").lower().strip()
    try:
        with open(_OBS_LOG, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        for line in reversed(lines):
            data = json.loads(line)
            if target_lower in (data.get("target") or "").lower():
                return ObservationRecord(**data)
    except Exception:
        pass
    return None
