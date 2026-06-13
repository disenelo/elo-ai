"""
avatar/animation_router.py — pure transport layer.

Receives motion intent + avatar state, routes to destination.
No logic. No transforms. Only routing.

Targets:
    unity    → avatar/avatar_signal.json  (Unity reads on poll interval)
    blender  → blender/blender_state.json (Blender driver reads)
    console  → stdout debug line
    all      → all three
"""

import json
import os

_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BLENDER_PATH = os.path.join(_ROOT, "blender", "blender_state.json")
_UNITY_PATH   = os.environ.get(
    "ELO_SIGNAL_PATH",
    os.path.join(_ROOT, "avatar", "avatar_signal.json"),
)

# avatar mode → existing Unity state vocabulary
_MODE_TO_UNITY_STATE = {
    "idle":        "resting",
    "observing":   "reflecting",
    "thinking":    "reflecting",
    "building":    "building",
    "celebrating": "playful",
    "exploring":   "exploring",
    "resting":     "resting",
}


def route(motion: dict, state: dict = None, target: str = "console") -> None:
    """
    Route a motion dict to one or more targets.

    Args:
        motion:  {animation, duration, intensity}
        state:   Optional AvatarState for richer signals.
        target:  "unity" | "blender" | "console" | "all"
    """
    targets = ["unity", "blender", "console"] if target == "all" else [target]
    for t in targets:
        if t == "unity":
            _to_unity(motion, state)
        elif t == "blender":
            _to_blender(motion, state)
        elif t == "console":
            _to_console(motion, state)


def _to_console(motion: dict, state: dict = None) -> None:
    mode = (state or {}).get("mode", "?")
    print(f"  [avatar] {mode} → {motion['animation']} "
          f"({motion['duration']}s  intensity={motion['intensity']})")


def _to_blender(motion: dict, state: dict = None) -> None:
    payload = {"motion": motion}
    if state:
        payload["state"] = state
    os.makedirs(os.path.dirname(_BLENDER_PATH), exist_ok=True)
    with open(_BLENDER_PATH, "w") as f:
        json.dump(payload, f, indent=2)


def _to_unity(motion: dict, state: dict = None) -> None:
    try:
        from avatar.unity_bridge import export_signal
        energy = (state or {}).get("energy", 0.5)
        mode   = (state or {}).get("mode",   "thinking")
        intensity = motion.get("intensity", 0.3)
        export_signal({
            "state":  _MODE_TO_UNITY_STATE.get(mode, "exploring"),
            "energy": energy,
            "mode":   "companion",
            "animation_hints": {
                "bounce_intensity": intensity,
                "movement_speed":   round(intensity * 0.8, 3),
                "scale_pulse":      round(intensity * 0.3, 3),
                "head_tilt_deg":    0.0,
                "lean_amount":      0.0,
                "rotation_speed":   0.0,
            },
        })
    except Exception:
        pass  # Unity bridge unavailable — non-fatal
