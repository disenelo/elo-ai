"""
blender_bridge/animation_driver.py — pure Python clip → NLA logic.

Importable helper used by blender_receiver.py and unit tests.
Does NOT import bpy — safe to test outside Blender.

Produces the NLA commands that blender_receiver applies to the rig.
"""
from __future__ import annotations


# Clips available in the eLo rig — must match NLA action names
KNOWN_CLIPS = {"idle", "walk", "jump", "sit", "float"}


def resolve_clip(animation: str) -> str:
    """Map an animation name to a known clip, falling back to idle."""
    name = animation.lower().strip()
    if name in KNOWN_CLIPS:
        return name
    # aliases
    _ALIASES = {
        "breathe": "idle",
        "settle":  "idle",
        "pace":    "walk",
        "wander":  "walk",
        "hop":     "jump",
    }
    return _ALIASES.get(name, "idle")


def nla_command(animation: str, speed: float, intensity: float) -> dict:
    """
    Produce the NLA playback command dict.

    Returns:
        {
            "clip":     str,    — resolved clip name
            "scale":    float,  — NLA strip scale (inverse of speed)
            "mute_all": bool,   — True = mute all other strips first
        }
    """
    clip  = resolve_clip(animation)
    scale = max(0.1, 1.0 / speed) if speed > 0 else 1.0

    return {
        "clip":     clip,
        "scale":    round(scale, 3),
        "mute_all": True,  # always mute others before playing new clip
    }
