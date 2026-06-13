"""
avatar/avatar_state.py — eLo presence state.

The bridge between cognition and embodiment.
Every motion in the avatar must trace back here.

AvatarState is a plain dict — serialisable, inspectable, no magic.
"""

MODES = ("idle", "observing", "thinking", "building", "celebrating", "exploring", "resting")


def default() -> dict:
    return {
        "mode":             "idle",
        "energy":           0.3,
        "curiosity":        0.4,
        "certainty":        0.5,
        "engagement":       0.4,
        "motion_permission": True,
    }


def blend(current: dict, target: dict, rate: float = 0.15) -> dict:
    """
    Lerp all float fields toward target at given rate.
    Mode only switches once energy is committed enough to warrant the change.
    Prevents twitching — presence changes slowly.
    """
    def _lerp(a: float, b: float) -> float:
        return round(a + (b - a) * rate, 3)

    blended = {
        "energy":            _lerp(current["energy"],     target["energy"]),
        "curiosity":         _lerp(current["curiosity"],  target["curiosity"]),
        "certainty":         _lerp(current["certainty"],  target["certainty"]),
        "engagement":        _lerp(current["engagement"], target["engagement"]),
        "motion_permission": target["motion_permission"],
    }

    # mode only switches when blended energy has committed — avoids rapid mode-flipping
    if current["mode"] != target["mode"] and blended["energy"] > 0.18:
        blended["mode"] = target["mode"]
    else:
        blended["mode"] = current["mode"]

    return blended
