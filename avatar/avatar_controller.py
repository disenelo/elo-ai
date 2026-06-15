"""
avatar/avatar_controller.py — PresenceState → body command.

Maps the rich PresenceState from presence/ into a concrete animation command
that downstream targets (Blender, Unity, desktop avatar) can consume.

Output format matches blender_bridge/state_writer expected schema.
"""
from __future__ import annotations

from presence.presence_state import PresenceMode, PresenceState


# ── mode → animation clip name ────────────────────────────────────────────────
# These must match clips available in the eLo rig.

_MODE_CLIP: dict[PresenceMode, str] = {
    PresenceMode.IDLE:        "idle",
    PresenceMode.THINKING:    "idle",        # subtle breathe — same clip, lower speed
    PresenceMode.OBSERVING:   "idle",        # lean + slow look, same idle base
    PresenceMode.BUILDING:    "walk",        # forward energy maps to walk cycle
    PresenceMode.CELEBRATING: "jump",        # arrival moment
    PresenceMode.RESTING:     "idle",        # settled idle
    PresenceMode.EXPLORING:   "walk",        # scanning = moving
}

# ── mode → animation speed multiplier ─────────────────────────────────────────

_MODE_SPEED: dict[PresenceMode, float] = {
    PresenceMode.IDLE:        0.6,
    PresenceMode.THINKING:    0.4,
    PresenceMode.OBSERVING:   0.55,
    PresenceMode.BUILDING:    1.0,
    PresenceMode.CELEBRATING: 1.2,
    PresenceMode.RESTING:     0.3,
    PresenceMode.EXPLORING:   0.85,
}


def build_command(state: PresenceState) -> dict:
    """
    Convert a PresenceState to an animation command dict.

    Returns:
        {
            "animation":  str,    — clip name (matches rig library)
            "speed":      float,  — playback speed (0–2)
            "intensity":  float,  — 0–1
            "energy":     float,  — 0–1
            "duration":   float,  — seconds to hold
            "mood":       str,    — descriptive label
            "mode":       str,    — presence mode name
        }
    """
    clip  = _MODE_CLIP.get(state.mode, "idle")
    speed = _MODE_SPEED.get(state.mode, 0.6)

    # energy modulates speed — low energy slows everything
    speed = round(speed * (0.5 + state.energy * 0.5), 3)

    return {
        "animation": clip,
        "speed":     speed,
        "intensity": state.intensity,
        "energy":    state.energy,
        "duration":  state.duration,
        "mood":      state.mood,
        "mode":      state.mode.value,
    }
