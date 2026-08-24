"""
runtime/world_delta.py — SP-27/SP-28 (WO-NAV-006).

World-change detection: save end-of-turn world summary, compute delta at start of next turn.
Pattern: save_world_summary() → load_previous_world() + compute_delta() → world_dict["world_delta"].
"""
from __future__ import annotations

import json
import logging
import os
import time

_log = logging.getLogger(__name__)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SUMMARY_PATH = os.path.join(_ROOT, "self", "state", "previous_world.json")


def save_world_summary(world) -> None:
    """
    SP-27: save a compact summary of the current world state.
    Called at the end of each turn (after world_dict is assembled).
    Silent on failure — never blocks a turn.
    """
    try:
        _gaze = getattr(world, "gaze", None)
        summary = {
            "ts":              time.time(),
            "platform":        getattr(getattr(world, "desktop", None), "platform", "") or "",
            "gaze_win_id":     int(getattr(_gaze, "win_id", 0)) if _gaze else 0,
            "surfaces_count":  len(getattr(world, "surfaces", ()) or ()),
            "jump_px":         int(getattr(world, "jump_px", 0)),
        }
        os.makedirs(os.path.dirname(_SUMMARY_PATH), exist_ok=True)
        _tmp = _SUMMARY_PATH + ".tmp"
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False)
        os.replace(_tmp, _SUMMARY_PATH)
    except Exception as e:
        _log.debug("save_world_summary failed (non-critical): %s", e)


def load_previous_world() -> dict:
    """SP-27: load the summary saved at the end of the previous turn."""
    try:
        with open(_SUMMARY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def compute_delta(previous_world: dict, current_world_dict: dict) -> dict:
    """
    SP-28: compare previous and current world state.

    Returns a WorldDelta dict with fields:
    - position_changed: bool  (platform changed between turns)
    - gaze_changed: bool      (gaze target changed)
    - new_platforms_visible: list  (simplified: non-empty if surface count grew)
    - lost_platforms_visible: list (simplified: non-empty if surface count shrank)
    - elapsed_turns: int      (always 1 for consecutive turns; 0 if no prior state)
    - any_change: bool        (True if any non-trivial change observed)
    """
    if not previous_world:
        return {
            "position_changed":      False,
            "gaze_changed":          False,
            "new_platforms_visible": [],
            "lost_platforms_visible": [],
            "elapsed_turns":         0,
            "any_change":            False,
        }

    prev_platform = previous_world.get("platform", "")
    curr_platform = current_world_dict.get("platform", "")
    position_changed = bool(prev_platform and curr_platform and prev_platform != curr_platform)

    prev_gaze = int(previous_world.get("gaze_win_id", 0))
    curr_gaze = int(current_world_dict.get("gaze_win_id", 0))
    gaze_changed = prev_gaze != curr_gaze

    prev_count = int(previous_world.get("surfaces_count", 0))
    curr_count = int(current_world_dict.get("surfaces_count", 0))
    new_platforms_visible: list = ["+" + str(curr_count - prev_count)] if curr_count > prev_count else []
    lost_platforms_visible: list = ["-" + str(prev_count - curr_count)] if curr_count < prev_count else []

    any_change = position_changed or gaze_changed or bool(new_platforms_visible) or bool(lost_platforms_visible)

    return {
        "position_changed":      position_changed,
        "gaze_changed":          gaze_changed,
        "new_platforms_visible": new_platforms_visible,
        "lost_platforms_visible": lost_platforms_visible,
        "elapsed_turns":         1,
        "any_change":            any_change,
    }
