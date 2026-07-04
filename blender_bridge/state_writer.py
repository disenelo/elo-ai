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

# ── Emotion → animation speed ─────────────────────────────────────────────────
# Unity uses `motion.speed` as `animator.speed` — so this directly controls
# how fast the idle-breathing, walk, run, and calm clips play.
# eLo's heartbeat: calm = slow and soft, playful = bright and quick.
# Clamped on the Unity side to speedClamp (default 0.2–1.8).
_EMOTION_SPEED: dict[str, float] = {
    "calm":        0.35,   # slow breathing, grounded
    "tired":       0.30,   # heavy, slow
    "overwhelmed": 0.40,   # slowed down, contracted
    "resting":     0.35,
    "neutral":     0.55,   # present, steady
    "open":        0.57,
    "confident":   0.62,
    "curious":     0.70,   # alert, leaning in
    "alert":       0.75,
    "exploring":   0.72,
    "excited":     0.90,   # bright, quick
    "playful":     0.95,
    "joy":         0.88,
    "celebrating": 1.10,
}

def emotion_speed(mood: str, base_speed: float | None = None) -> float:
    """Return the animator speed that matches the current emotional state."""
    mapped = _EMOTION_SPEED.get((mood or "neutral").lower().strip(), 0.57)
    # If caller provides a base_speed, blend it (e.g. presence engine intensity nudge)
    if base_speed is not None:
        return round((mapped + float(base_speed)) / 2.0, 3)
    return mapped


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
    # Derive speed from emotion if not explicitly set by the caller.
    _mood  = (emotion.get("emotion") if emotion else None) or motion.get("mood", "neutral")
    _speed = motion.get("speed") or emotion_speed(_mood)

    payload: dict = {
        "motion": {
            "animation": motion.get("animation", "idle"),
            "speed":     _speed,
            "intensity": motion.get("intensity", 0.5),
            "duration":  motion.get("duration",  4.0),
            "mood":      _mood,
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

    return _write(payload)


def write_with_presence(
    motion:       dict,
    expression:   dict | None = None,
    presence:     dict | None = None,
    emotion:      dict | None = None,
    presence_plan: dict | None = None,
) -> bool:
    """
    v1.7 — write blender_state.json with Presence Plan block.

    Calls write() for existing fields then merges presence_plan block.
    Backwards compatible: presence_plan absent → identical to write().
    """
    # Build payload via the existing write path (returns True/False)
    # We need the payload dict, so we replicate the build here.
    _mood  = (emotion.get("emotion") if emotion else None) or motion.get("mood", "neutral")
    _speed = motion.get("speed") or emotion_speed(_mood)

    payload: dict = {
        "motion": {
            "animation": motion.get("animation", "idle"),
            "speed":     _speed,
            "intensity": motion.get("intensity", 0.5),
            "duration":  motion.get("duration",  4.0),
            "mood":      _mood,
            "mode":      motion.get("mode",      "idle"),
        },
        "_ts": round(time.time(), 3),
    }

    if expression:
        payload["expression"] = {
            "shape_keys": expression.get("shape_keys", {}),
            "head_lean":  expression.get("head_lean", 0.0),
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

    # v1.7 — Presence Plan block (Emotional Light Engine output)
    if presence_plan:
        payload["presence_plan"] = presence_plan

    return _write(payload)


def _write(payload: dict) -> bool:
    try:
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, _STATE_PATH)
        return True
    except Exception:
        return False
