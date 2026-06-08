"""
avatar/unity_signal.py — eLo kernel output → Unity animation signal.

Pure translation layer. No AI logic. No behavioural decisions.
Maps existing kernel output fields to Unity-ready animation strings.

Entry point:
    to_unity_signal(mode, state_name, emotion, intent, energy, loop_detected)
    → {"state", "emotion", "intent", "energy", "motion_hint"}

All mapping tables are read-only constants.
No imports from kernel, memory, or engine modules.

Usage:
    from avatar.unity_signal import to_unity_signal

    signal = to_unity_signal(
        mode         = meta["mode"],              # from kernel decide_response()
        state_name   = bus.state.name,            # from StateSnapshot
        emotion      = bus.emotion.emotion,        # from EmotionSnapshot
        intent       = bus.identity.intent,        # from IdentitySnapshot
        energy       = bus.state.style_weight,     # from StateSnapshot
        loop_detected= meta["loop_detected"],      # from kernel meta
    )
    # → {"state": "exploring", "emotion": "curious", "intent": "curious",
    #    "energy": 0.7, "motion_hint": "head_tilt"}
"""


# ── mapping tables ─────────────────────────────────────────────────────────────
# Read-only. No logic. No conditionals beyond lookup fallbacks.

# kernel mode → Unity animation state
_MODE_TO_ANIM_STATE: dict = {
    "DIRECT":          "focused",
    "GENTLE_GROUNDED": "resting",
    "CREATIVE":        "exploring",
    "STRUCTURED":      "building",
    "SIMPLIFY":        "idle",
    "CONVERSATIONAL":  "standing",
}

# state engine name → Unity animation state (fallback when mode not supplied)
_STATE_TO_ANIM_STATE: dict = {
    "focused":   "focused",
    "building":  "building",
    "exploring": "exploring",
    "reflecting":"reflecting",
    "playful":   "playful",
    "resting":   "resting",
}

# emotion engine label → Unity animation emotion layer
_EMOTION_TO_ANIM: dict = {
    "curious":    "curious",
    "excited":    "excited",
    "calm":       "calm",
    "focused":    "focused",
    "reflective": "calm",
    "playful":    "playful",
    "distorted":  "distressed",
    "gentle":     "calm",
    "neutral":    "idle",
}

# identity/emotion intent → Unity intent string
_INTENT_TO_ANIM: dict = {
    # identity_engine intents
    "expand_idea":        "curious",
    "name_state":         "present",
    "hold_space":         "calm",
    "advance_project":    "focused",
    "reflect_back":       "listening",
    "surface_connection": "curious",
    "offer_question":     "curious",
    "hold_contradiction": "thinking",
    # emotion_engine body intents
    "show_curiosity":     "curious",
    "show_excitement":    "excited",
    "show_calm":          "calm",
    "show_focus":         "focused",
    "show_playfulness":   "playful",
    "show_concern":       "listening",
    "show_reflection":    "calm",
}

# (anim_state, anim_emotion) → motion_hint clip name
# motion_hint is a direct Unity Animator trigger or blend tree input.
_MOTION_HINTS: dict = {
    # focused state
    ("focused",    "curious"):    "head_tilt",
    ("focused",    "focused"):    "upright_still",
    ("focused",    "excited"):    "lean_forward",
    ("focused",    "calm"):       "focused_idle",
    ("focused",    "idle"):       "focused_idle",

    # resting state
    ("resting",    "distressed"): "withdraw",
    ("resting",    "calm"):       "settle",
    ("resting",    "idle"):       "settle",

    # exploring state
    ("exploring",  "curious"):    "head_tilt",
    ("exploring",  "excited"):    "bounce",
    ("exploring",  "playful"):    "look_around",
    ("exploring",  "calm"):       "slow_scan",
    ("exploring",  "idle"):       "slow_scan",

    # building state
    ("building",   "focused"):    "lean_forward",
    ("building",   "excited"):    "lean_forward",
    ("building",   "calm"):       "build_pose",
    ("building",   "idle"):       "build_pose",

    # reflecting state
    ("reflecting", "calm"):       "look_upward",
    ("reflecting", "idle"):       "look_upward",
    ("reflecting", "curious"):    "head_tilt",

    # playful state
    ("playful",    "excited"):    "bounce",
    ("playful",    "playful"):    "look_around",
    ("playful",    "curious"):    "head_tilt",
    ("playful",    "idle"):       "light_sway",

    # standing / conversational
    ("standing",   "curious"):    "head_tilt",
    ("standing",   "thinking"):   "slow_scan",
    ("standing",   "calm"):       "standing_idle",
    ("standing",   "idle"):       "standing_idle",
    ("standing",   "distressed"): "withdraw",

    # idle / simplify
    ("idle",       "idle"):       "idle",
    ("idle",       "calm"):       "idle",
}

_DEFAULT_MOTION_HINT = "standing_idle"   # safe fallback for any unmapped combo


# ── translation function ───────────────────────────────────────────────────────

def to_unity_signal(
    mode:          str,
    state_name:    str   = "exploring",
    emotion:       str   = "neutral",
    intent:        str   = "offer_question",
    energy:        float = 0.5,
    loop_detected: bool  = False,
) -> dict:
    """
    Translate kernel output into a Unity-ready animation signal.

    Args:
        mode:          Kernel response mode — one of DIRECT, GENTLE_GROUNDED,
                       CREATIVE, STRUCTURED, SIMPLIFY, CONVERSATIONAL.
        state_name:    Current state engine name — exploring, building, etc.
        emotion:       Emotion engine label — curious, calm, distorted, etc.
        intent:        Identity or emotion engine intent string.
        energy:        Style weight or warmth float (0.0–1.0).
        loop_detected: True if the kernel's loop detector fired this turn.

    Returns:
        {
            state:       str    — Unity Animator state name
            emotion:     str    — animation emotion layer
            intent:      str    — what eLo communicates through motion
            energy:      float  — animation intensity (0.0–1.0)
            motion_hint: str    — direct clip/trigger name for the Animator
        }
    """
    # 1 — translate each field through its lookup table
    anim_state  = _MODE_TO_ANIM_STATE.get(mode,
                  _STATE_TO_ANIM_STATE.get(state_name, "standing"))

    anim_emotion = _EMOTION_TO_ANIM.get(emotion, "idle")
    anim_intent  = _INTENT_TO_ANIM.get(intent,   "calm")
    anim_energy  = round(max(0.0, min(1.0, float(energy))), 2)

    # 2 — motion_hint: combine state + emotion for the specific clip
    motion_hint = _MOTION_HINTS.get(
        (anim_state, anim_emotion),
        _MOTION_HINTS.get((anim_state, "idle"), _DEFAULT_MOTION_HINT)
    )

    # 3 — loop break override: reset pose when loop detection fires
    if loop_detected:
        motion_hint  = "reset_pose"
        anim_state   = "focused"     # snap to focused to break repetition visually
        anim_emotion = "idle"

    return {
        "state":       anim_state,
        "emotion":     anim_emotion,
        "intent":      anim_intent,
        "energy":      anim_energy,
        "motion_hint": motion_hint,
    }


# ── convenience: build from kernel meta + StateBus ────────────────────────────

def signal_from_bus(meta: dict, bus) -> dict:
    """
    Convenience wrapper — build a Unity signal directly from a kernel meta dict
    and a StateBus object.

    Args:
        meta: The (response, meta) tuple's meta component from decide_response().
        bus:  The StateBus produced by core_engine.prepare_context().

    Returns:
        Unity animation signal dict (same structure as to_unity_signal()).
    """
    return to_unity_signal(
        mode          = meta.get("mode", "CONVERSATIONAL"),
        state_name    = bus.state.name,
        emotion       = bus.emotion.emotion,
        intent        = bus.identity.intent,
        energy        = bus.state.style_weight,
        loop_detected = meta.get("loop_detected", False),
    )
