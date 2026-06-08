"""
core/avatar_bridge.py — eLo AI avatar signal bridge.

Single function: get_avatar_signal()

Packages all core signals into a clean dict that any embodiment layer can consume.
The bridge is the contract between eLo Core and every body eLo can run in.

Consumers:
    desktop avatar  → canvas_2d.py reads this dict
    game engine     → Unity bridge reads this dict via JSON
    physical robot  → hardware plugin reads this dict
    terminal debug  → printed directly

The bridge never contains rendering logic.
It contains signals. The body decides what to do with them.
"""

from core.emotion_engine import from_state, orb_intensity


def get_avatar_signal(
    state: str,
    input_emotion: str = "neutral",
    mode: str = "companion",
    memory: dict = None,
    response_text: str = "",
) -> dict:
    """
    Package all core signals into an avatar-ready dict.

    Args:
        state:          From state_engine.state
        input_emotion:  Detected emotion from behavior_engine phase 1
        mode:           Active mode
        memory:         From build_memory_influence() — used for energy modifiers
        response_text:  The generated response — length influences energy signal

    Returns:
        {
            # identity signals (what the AI is doing)
            state:    str
            emotion:  str
            intent:   str
            mode:     str
            energy:   float 0.0–1.0

            # expression hints (how to move the body)
            posture:  str
            pace:     str
            orb:      float 0.0–1.0   # glow intensity

            # context
            response_length: "short" | "medium" | "long"
            project:  str             # active project namespace
        }
    """
    emotion_signal = from_state(state, input_emotion, mode)

    # memory can modulate energy slightly
    memory_tone = (memory or {}).get("tone_signal", "neutral")
    energy      = emotion_signal["energy"]
    if memory_tone == "distorted":
        energy = max(0.1, energy - 0.2)
    elif memory_tone == "curious":
        energy = min(1.0, energy + 0.1)

    # response length from text
    words = len(response_text.split()) if response_text else 0
    if words == 0:
        response_length = "short"
    elif words <= 30:
        response_length = "short"
    elif words <= 80:
        response_length = "medium"
    else:
        response_length = "long"

    return {
        # identity signals
        "state":   state,
        "emotion": emotion_signal["emotion"],
        "intent":  emotion_signal["intent"],
        "mode":    mode,
        "energy":  round(energy, 2),

        # expression hints
        "posture": emotion_signal["posture"],
        "pace":    emotion_signal["pace"],
        "orb":     orb_intensity(energy, emotion_signal["emotion"]),

        # context
        "response_length": response_length,
        "project": (memory or {}).get("project_momentum", "elo_core"),
    }


def signal_to_animation_hints(signal: dict) -> dict:
    """
    Convert an avatar signal into concrete animation parameter hints.

    This is the layer between "what eLo feels" and "how the body moves."
    Each body (desktop avatar, Unity, robot) still interprets these — but this
    provides a shared starting point.

    Returns values that an animator can directly apply:
        head_tilt_deg    float   degrees of head tilt
        lean_amount      float   0.0 (upright) → 1.0 (fully forward)
        bounce_intensity float   0.0 (still) → 1.0 (full bounce)
        rotation_speed   float   0.0 (still) → 1.0 (fast rotation)
        scale_pulse      float   0.0 (no pulse) → 1.0 (full size pulse)
        movement_speed   float   0.0 (still) → 1.0 (fast movement)
    """
    intent  = signal.get("intent",  "hold_space")
    energy  = signal.get("energy",  0.5)
    posture = signal.get("posture", "settle")

    _INTENT_ANIMATION = {
        "show_curiosity":   {"head_tilt_deg": 12, "lean_amount": 0.4, "bounce_intensity": 0.2,
                             "rotation_speed": 0.1, "scale_pulse": 0.1},
        "show_excitement":  {"head_tilt_deg": 5,  "lean_amount": 0.3, "bounce_intensity": 0.8,
                             "rotation_speed": 0.3, "scale_pulse": 0.5},
        "hold_space":       {"head_tilt_deg": 0,  "lean_amount": 0.0, "bounce_intensity": 0.0,
                             "rotation_speed": 0.0, "scale_pulse": 0.0},
        "show_focus":       {"head_tilt_deg": 0,  "lean_amount": 0.1, "bounce_intensity": 0.0,
                             "rotation_speed": 0.0, "scale_pulse": 0.0},
        "show_playfulness": {"head_tilt_deg": 18, "lean_amount": 0.2, "bounce_intensity": 0.6,
                             "rotation_speed": 0.2, "scale_pulse": 0.3},
        "show_calm":        {"head_tilt_deg": 5,  "lean_amount": 0.0, "bounce_intensity": 0.0,
                             "rotation_speed": 0.0, "scale_pulse": 0.05},
        "show_concern":     {"head_tilt_deg": -5, "lean_amount": -0.1, "bounce_intensity": 0.0,
                             "rotation_speed": 0.0, "scale_pulse": 0.0},
        "show_reflection":  {"head_tilt_deg": -8, "lean_amount": 0.0, "bounce_intensity": 0.0,
                             "rotation_speed": 0.05, "scale_pulse": 0.0},
    }

    base = _INTENT_ANIMATION.get(intent, _INTENT_ANIMATION["hold_space"])

    # scale everything by energy
    return {
        "head_tilt_deg":    round(base["head_tilt_deg"] * energy, 1),
        "lean_amount":      round(base["lean_amount"]   * energy, 2),
        "bounce_intensity": round(base["bounce_intensity"] * energy, 2),
        "rotation_speed":   round(base["rotation_speed"] * energy, 2),
        "scale_pulse":      round(base["scale_pulse"]   * energy, 2),
        "movement_speed":   round(energy, 2),
    }
