"""
avatar/avatar_rules.py — constraints that keep avatar behavior coherent.

Rules are applied to a command dict before it reaches the bridge.
No rules should add data — only clamp, block, or modify.
"""
from __future__ import annotations

# minimum time (seconds) a clip must hold before switching
_MIN_HOLD = 2.0

# modes that should not transition directly to RESTING or IDLE
_NO_IMMEDIATE_REST = {"celebrating", "exploring"}

# low-energy floor — below this, always use idle regardless of mode
_LOW_ENERGY_FLOOR = 0.15


def apply(command: dict, previous_command: dict | None) -> dict:
    """
    Apply avatar rules to a command, returning a (potentially modified) command.

    Args:
        command:          incoming command from avatar_controller.build_command()
        previous_command: last applied command (can be None on first turn)

    Returns:
        filtered/clamped command dict (same shape as input)
    """
    out = dict(command)

    # rule 1: low energy floor — if energy is very low, hold to idle
    if out["energy"] < _LOW_ENERGY_FLOOR:
        out["animation"] = "idle"
        out["speed"]     = 0.3

    # rule 2: celebrating must breathe — don't cut short
    if previous_command and previous_command.get("mode") == "celebrating":
        prev_duration = previous_command.get("duration", 0.0)
        if prev_duration > _MIN_HOLD:
            out["animation"] = previous_command["animation"]
            out["mode"]      = previous_command["mode"]
            out["duration"]  = min(out["duration"], 2.0)

    # rule 3: clip speed always in valid range
    out["speed"] = max(0.1, min(2.0, out["speed"]))

    # rule 4: intensity always in valid range
    out["intensity"] = max(0.0, min(1.0, out["intensity"]))

    return out
