"""
blender_bridge/state_writer.py — writes consolidated state.json for Blender.

Main.py pipeline output reaches here last.
Writes the full state (motion + expression + presence) in one atomic write.

Blender receiver polls this file at 250ms.
"""
from __future__ import annotations
import json
import os
import time

# Path is relative to project root, placed in blender/ so existing code finds it
_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")


def write(
    motion:     dict,
    expression: dict | None = None,
    presence:   dict | None = None,
    emotion:    dict | None = None,
) -> bool:
    """
    Write a consolidated state to blender_state.json.

    Args:
        motion:     from avatar_controller.build_command()
        expression: from expression_mapper.build_expression() — optional
        presence:   raw legacy presence dict — optional

    Returns:
        True on success.
    """
    payload: dict = {
        "motion": {
            "animation": motion.get("animation", "idle"),
            "speed":     motion.get("speed",     0.6),
            "intensity": motion.get("intensity", 0.5),
            "duration":  motion.get("duration",  4.0),
            "mood":      motion.get("mood",      "open"),
            "mode":      motion.get("mode",      "idle"),
        },
        "_ts": round(time.time(), 3),
    }

    if expression:
        payload["expression"] = {
            "shape_keys": expression.get("shape_keys", {}),  # dict of key→value
            "head_lean":  expression.get("head_lean", 0.0),  # c_head.x Y rotation
            "pacing":     expression.get("pacing",    "steady"),
            "intensity":  expression.get("intensity", 0.5),
        }

    if presence:
        payload["state"] = {
            "energy":    presence.get("energy",   0.5),
            "mode":      presence.get("mode",     "idle"),
            "emotion":   emotion.get("emotion",   "neutral") if emotion else "neutral",
            "intensity": emotion.get("intensity", 0.3)       if emotion else 0.3,
        }

    try:
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, _STATE_PATH)
        return True
    except Exception:
        return False
