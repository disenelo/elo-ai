"""
avatar/motion_mapper.py — presence state → animation intent.

Pure function. No state held here.
"""

# mode → (animation_name, base_duration_seconds, base_intensity)
_MODE_MOTION: dict[str, tuple] = {
    "idle":        ("breathe",  8,  0.15),
    "observing":   ("look",     8,  0.30),
    "thinking":    ("sit",      10, 0.20),
    "building":    ("pace",     6,  0.55),
    "celebrating": ("hop",      2,  0.85),
    "exploring":   ("wander",   12, 0.45),
    "resting":     ("settle",   14, 0.10),
}


def map(state: dict) -> dict:
    """
    Map an AvatarState to a concrete motion intent.

    Returns:
        {animation, duration, intensity}
    """
    mode      = state.get("mode",             "idle")
    energy    = state.get("energy",           0.3)
    engaged   = state.get("engagement",       0.4)
    permitted = state.get("motion_permission", True)

    if not permitted:
        return {"animation": "settle", "duration": 14, "intensity": 0.05}

    animation, base_dur, base_intensity = _MODE_MOTION.get(mode, _MODE_MOTION["idle"])

    # scale intensity by energy and engagement
    intensity = base_intensity * (0.6 + energy * 0.4) * (0.7 + engaged * 0.3)
    intensity = round(max(0.05, min(1.0, intensity)), 2)

    # higher energy = shorter hold time (more restless)
    duration  = round(base_dur * (1.0 + (0.5 - energy) * 0.4))
    duration  = max(4, duration)

    return {
        "animation": animation,
        "duration":  duration,
        "intensity": intensity,
    }
