"""
blender/avatar_driver.py — motion intent → movement sequence.

Translates a single motion dict into a timed sequence of steps.
Each step has a description, duration, and eased intensity.

Rules (from spec):
    - No idle loops under 4 seconds
    - No instant transitions — all movement uses easing
    - Max speed: slow (intensity cap at 0.65)
    - No cartoon hyperactivity
"""

import math
import time


# animation → step sequence (description, fraction_of_total_duration)
_SEQUENCES: dict[str, list] = {
    "breathe": [
        ("inhale slowly",       0.5),
        ("exhale slowly",       0.5),
    ],
    "sit": [
        ("lower gently",        0.30),
        ("settle",              0.40),
        ("look down",           0.30),
    ],
    "pace": [
        ("step forward",        0.35),
        ("pause",               0.15),
        ("step forward",        0.35),
        ("turn slowly",         0.15),
    ],
    "hop": [
        ("small lift",          0.40),
        ("land softly",         0.35),
        ("settle",              0.25),
    ],
    "wander": [
        ("walk slowly",         0.30),
        ("pause",               0.15),
        ("look sideways",       0.20),
        ("continue walking",    0.25),
        ("slow to stop",        0.10),
    ],
    "look": [
        ("turn head",           0.35),
        ("hold gaze",           0.40),
        ("return",              0.25),
    ],
    "settle": [
        ("lower to rest",       0.40),
        ("adjust",              0.20),
        ("still",               0.40),
    ],
}


def _ease(t: float) -> float:
    """Cubic ease in-out. t in [0, 1]."""
    if t < 0.5:
        return 4 * t * t * t
    p = 2 * t - 2
    return 1 + p * p * p / 2


def drive(motion: dict, realtime: bool = False) -> list:
    """
    Expand a motion intent into a movement sequence.

    Args:
        motion:   {animation, duration, intensity}
        realtime: If True, sleep between steps. Default False.

    Returns:
        List of {step, duration_s, intensity, eased}
    """
    animation = motion.get("animation", "breathe")
    duration  = float(motion.get("duration",  8))
    intensity = float(motion.get("intensity", 0.3))

    # max speed: slow
    intensity = min(intensity, 0.65)

    sequence = _SEQUENCES.get(animation, _SEQUENCES["breathe"])
    steps    = []

    print(f"\n[eLo]")
    print(f"  animation = {animation}")
    print(f"  duration  = {duration:.0f}s")
    print(f"  intensity = {intensity:.2f}")
    print()

    for i, (desc, fraction) in enumerate(sequence):
        step_dur = max(1.0, duration * fraction)
        t        = i / max(1, len(sequence) - 1)
        eased_i  = round(_ease(t) * intensity, 3)

        step = {
            "step":       desc,
            "duration_s": round(step_dur, 1),
            "intensity":  eased_i,
        }
        steps.append(step)

        print(f"  → {desc:26s}  {step_dur:4.1f}s  i={eased_i:.3f}")

        if realtime:
            time.sleep(step_dur)

    return steps
