"""
blender/state_driver.py — writes PresenceState to blender_state.json.

Called from main.py after presence + avatar pipeline runs.
Blender (or any receiver) polls this file at 250ms.

State written is the richer presence format — includes mode, intensity,
mood, speed, duration — not just the older avatar energy dict.
"""
from __future__ import annotations
import json
import os

_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_state.json")


def write(command: dict, presence_dict: dict | None = None) -> bool:
    """
    Write the current animation command + presence state to disk.

    Args:
        command:       dict from avatar_controller.build_command()
        presence_dict: optional legacy avatar state dict (from avatar/presence_engine)

    Returns:
        True on success, False on write failure.
    """
    payload = {
        "motion": {
            "animation": command.get("animation", "idle"),
            "duration":  command.get("duration",  4.0),
            "intensity": command.get("intensity", 0.5),
            "speed":     command.get("speed",     0.6),
            "mood":      command.get("mood",      "open"),
            "mode":      command.get("mode",      "idle"),
        }
    }

    if presence_dict:
        payload["state"] = {
            "energy":     presence_dict.get("energy",    0.5),
            "mode":       presence_dict.get("mode",      "idle"),
        }

    try:
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, _STATE_PATH)  # atomic write
        return True
    except Exception:
        return False


def read() -> dict:
    """Read the current blender_state.json. Returns {} if missing/corrupt."""
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
