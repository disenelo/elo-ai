"""
avatar/robot_signal.py — eLo AI OS robot signal protocol.

Converts kernel output into robot control signals.
No decision logic. No AI. Pure deterministic mapping.

Output format:
    {
        motion_state: str    — idle / walking / building / reflecting / playful / resting
        posture:      str    — upright / lean_forward / contracted / open / settled
        direction:    str    — stationary / forward / backward / rotating / scanning
        energy_level: float  — 0.0 (still) to 1.0 (full motion)
        intent:       str    — curious / focused / calm / present / thinking / listening
        safety_flag:  bool   — True = safe to actuate, False = hold all motion
    }

All fields derived from StateBus snapshots or kernel meta dict.
No field requires calling any engine or kernel function.

Entry points:
    to_robot_signal(mode, state_name, emotion, intent, energy, loop_detected)
    robot_signal_from_bus(meta, bus)
    robot_signal_from_event(event)      — from dashboard event dict
"""


# ── mapping tables ─────────────────────────────────────────────────────────────
# Read-only constants. No conditionals beyond dict.get(key, default).

# kernel mode + state → motion_state
_MODE_MOTION: dict = {
    "DIRECT":          "idle",
    "GENTLE_GROUNDED": "resting",
    "CREATIVE":        "walking",
    "STRUCTURED":      "building",
    "SIMPLIFY":        "idle",
    "CONVERSATIONAL":  "idle",
}

_STATE_MOTION: dict = {
    "focused":   "idle",
    "exploring": "walking",
    "building":  "building",
    "reflecting":"reflecting",
    "playful":   "playful",
    "resting":   "resting",
}

# intent/emotion → posture
_INTENT_POSTURE: dict = {
    "show_curiosity":    "lean_forward",
    "show_excitement":   "open",
    "hold_space":        "settled",
    "show_focus":        "upright",
    "show_playfulness":  "open",
    "show_calm":         "settled",
    "show_concern":      "contracted",
    "show_reflection":   "contracted",
    "expand_idea":       "open",
    "name_state":        "settled",
    "advance_project":   "lean_forward",
    "reflect_back":      "contracted",
    "offer_question":    "lean_forward",
    "hold_contradiction":"upright",
    "curious":           "lean_forward",
    "focused":           "upright",
    "calm":              "settled",
    "playful":           "open",
    "distressed":        "contracted",
    "gentle":            "settled",
    "idle":              "upright",
    "neutral":           "upright",
}

# state + emotion → direction of movement
_STATE_DIRECTION: dict = {
    "exploring":  "scanning",
    "building":   "forward",
    "focused":    "stationary",
    "reflecting": "stationary",
    "playful":    "rotating",
    "resting":    "stationary",
}

_EMOTION_DIRECTION: dict = {
    "curious":    "forward",
    "excited":    "forward",
    "calm":       "stationary",
    "focused":    "stationary",
    "playful":    "rotating",
    "distressed": "backward",
    "gentle":     "stationary",
    "neutral":    "stationary",
}

# intent → robot intent string (simpler vocabulary for robot firmware)
_INTENT_MAP: dict = {
    "expand_idea":        "curious",
    "name_state":         "present",
    "hold_space":         "calm",
    "advance_project":    "focused",
    "reflect_back":       "listening",
    "surface_connection": "curious",
    "offer_question":     "curious",
    "hold_contradiction": "thinking",
    "show_curiosity":     "curious",
    "show_excitement":    "excited",
    "show_calm":          "calm",
    "show_focus":         "focused",
    "show_playfulness":   "playful",
    "show_concern":       "listening",
    "show_reflection":    "calm",
    "curious":            "curious",
    "focused":            "focused",
    "calm":               "calm",
    "present":            "present",
    "listening":          "listening",
    "thinking":           "thinking",
}


# ── safety flag rules ─────────────────────────────────────────────────────────
# safety_flag = True  → robot may actuate (normal operation)
# safety_flag = False → robot must hold all motion (protective stop)
#
# False conditions:
#   - loop_detected AND mode is GENTLE_GROUNDED (user in distress — do not approach)
#   - energy_level < 0.05 (near-zero energy — avoid spurious movement)
#
# No other conditions. This is a hardcoded safety contract, not a routing decision.

def _compute_safety_flag(
    mode:          str,
    loop_detected: bool,
    energy_level:  float,
) -> bool:
    if loop_detected and mode == "GENTLE_GROUNDED":
        return False   # user in distress loop — hold position
    if energy_level < 0.05:
        return False   # near-zero energy — prevent spurious actuations
    return True


# ── main mapping function ──────────────────────────────────────────────────────

def to_robot_signal(
    mode:          str,
    state_name:    str   = "exploring",
    emotion:       str   = "neutral",
    intent:        str   = "offer_question",
    energy:        float = 0.5,
    loop_detected: bool  = False,
) -> dict:
    """
    Convert kernel output fields into a robot control signal.

    No decision logic. All fields come from lookup tables.
    Same inputs always produce the same output (deterministic).

    Args:
        mode:          Kernel mode — DIRECT, GENTLE_GROUNDED, CREATIVE, etc.
        state_name:    State engine name — exploring, building, focused, etc.
        emotion:       Emotion engine label — curious, calm, distorted, etc.
        intent:        Identity or emotion body intent string.
        energy:        Style weight or warmth (0.0–1.0).
        loop_detected: True if loop detection fired this turn.

    Returns:
        {
            motion_state: str,
            posture:      str,
            direction:    str,
            energy_level: float,
            intent:       str,
            safety_flag:  bool,
        }
    """
    energy_f = round(max(0.0, min(1.0, float(energy))), 2)

    # motion_state: mode takes priority, state_name as fallback
    motion_state = _MODE_MOTION.get(mode,
                   _STATE_MOTION.get(state_name, "idle"))

    # posture: intent first, emotion as fallback
    posture = _INTENT_POSTURE.get(intent,
              _INTENT_POSTURE.get(emotion, "upright"))

    # direction: state first, emotion as modifier
    direction = _STATE_DIRECTION.get(state_name,
                _EMOTION_DIRECTION.get(emotion, "stationary"))

    # intent: simplified vocabulary for firmware
    robot_intent = _INTENT_MAP.get(intent,
                   _INTENT_MAP.get(emotion, "calm"))

    # safety flag: hardcoded rules, no routing
    safety = _compute_safety_flag(mode, loop_detected, energy_f)

    return {
        "motion_state": motion_state,
        "posture":      posture,
        "direction":    direction,
        "energy_level": energy_f,
        "intent":       robot_intent,
        "safety_flag":  safety,
    }


# ── convenience wrappers ──────────────────────────────────────────────────────

def robot_signal_from_bus(meta: dict, bus) -> dict:
    """
    Build a robot signal from kernel meta + StateBus.

    Args:
        meta: The meta dict from kernel.decide_response().
        bus:  The StateBus from core_engine.prepare_context().
    """
    return to_robot_signal(
        mode          = meta.get("mode", "CONVERSATIONAL"),
        state_name    = bus.state.name,
        emotion       = bus.emotion.emotion,
        intent        = bus.identity.intent,
        energy        = bus.state.style_weight,
        loop_detected = meta.get("loop_detected", False),
    )


def robot_signal_from_event(event: dict) -> dict:
    """
    Build a robot signal from a dashboard event dict.

    Args:
        event: An event dict from dashboard/event_bus.py.
    """
    st = event.get("state_snapshot",  {})
    em = event.get("emotion_snapshot",{})
    id_ = event.get("identity_snapshot",{})

    return to_robot_signal(
        mode          = event.get("mode", "CONVERSATIONAL"),
        state_name    = st.get("name",    "exploring"),
        emotion       = em.get("emotion", "neutral"),
        intent        = id_.get("intent", "offer_question"),
        energy        = float(st.get("weight", 0.5)),
        loop_detected = event.get("loop",  False),
    )
