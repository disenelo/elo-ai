"""
runtime/light_engine/light_engine.py — eLo OS v1.8 Emotional Light Engine

Translates cognition into emotional expression.

Input:  CognitivePlan (with emotional_vector populated by Executive Faculty)
Output: PresencePlan (external truth for all embodiments)

Rules:
    Never reasons. Never decides. Never alters memory or identity.
    Only translates. The Executive decided. This expresses it.

Architecture spec: docs/architecture/11_emotional_light_engine.md
HSV colour table:  docs/architecture/11_emotional_light_engine.md §HSV COLOUR SYSTEM
"""
from __future__ import annotations
import logging
from runtime.spine.plan import CognitivePlan, PresencePlan

_log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# eLo EMOTIONAL LIGHT LANGUAGE — HSV COLOUR TABLE
# Primary hue H° · S · V  |  secondary = (H + 180) % 360
# ─────────────────────────────────────────────────────────────────────────────
# fmt: off
_STATE_TABLE = {
    #                           H      S     V    pulse      speed  bright bloom  move       anim_profile   expression  voice_p     v_e   v_w   trans
    "calm":             dict(h=180,  s=0.55, v=0.50, pulse="still",   sp=0.20, br=0.42, bl=0.18, mv="still",   ap="calm",     ep="open",    vp="measured",  ve=0.38, vw=0.72, ts=3.5),
    "curiosity":        dict(h=200,  s=0.65, v=0.72, pulse="slow",    sp=0.60, br=0.68, bl=0.34, mv="gentle",  ap="curious",   ep="curious", vp="warm",      ve=0.60, vw=0.65, ts=2.0),
    "creative_discovery":dict(h=175, s=0.70, v=0.82, pulse="medium",  sp=0.90, br=0.78, bl=0.52, mv="forward", ap="creative",  ep="curious", vp="energetic", ve=0.78, vw=0.80, ts=1.2),
    "momentum":         dict(h=35,   s=0.80, v=0.88, pulse="fast",    sp=1.40, br=0.85, bl=0.61, mv="forward", ap="exploring", ep="focused", vp="energetic", ve=0.86, vw=0.65, ts=0.9),
    "joy":              dict(h=45,   s=0.72, v=0.94, pulse="medium",  sp=1.10, br=0.92, bl=0.72, mv="forward", ap="creative",  ep="open",    vp="warm",      ve=0.80, vw=0.88, ts=1.0),
    "play":             dict(h=15,   s=0.78, v=0.90, pulse="fast",    sp=1.60, br=0.88, bl=0.58, mv="forward", ap="creative",  ep="open",    vp="energetic", ve=0.84, vw=0.78, ts=0.8),
    "reflection":       dict(h=270,  s=0.50, v=0.44, pulse="slow",    sp=0.30, br=0.38, bl=0.22, mv="still",   ap="calm",      ep="focused", vp="measured",  ve=0.35, vw=0.68, ts=3.0),
    "repair":           dict(h=28,   s=0.55, v=0.58, pulse="slow",    sp=0.40, br=0.52, bl=0.28, mv="gentle",  ap="calm",      ep="warm",    vp="measured",  ve=0.42, vw=0.85, ts=3.5),
    "comfort":          dict(h=158,  s=0.50, v=0.46, pulse="still",   sp=0.20, br=0.44, bl=0.16, mv="still",   ap="calm",      ep="warm",    vp="measured",  ve=0.36, vw=0.82, ts=3.5),
    "connection":       dict(h=195,  s=0.48, v=0.78, pulse="slow",    sp=0.50, br=0.74, bl=0.45, mv="gentle",  ap="curious",   ep="open",    vp="warm",      ve=0.55, vw=0.90, ts=2.5),
    "wonder":           dict(h=238,  s=0.70, v=0.66, pulse="slow",    sp=0.50, br=0.62, bl=0.55, mv="still",   ap="calm",      ep="curious", vp="measured",  ve=0.52, vw=0.72, ts=2.5),
    "focus":            dict(h=210,  s=0.55, v=0.58, pulse="still",   sp=0.00, br=0.55, bl=0.12, mv="still",   ap="calm",      ep="focused", vp="measured",  ve=0.50, vw=0.60, ts=1.5),
    "celebration":      dict(h=46,   s=0.88, v=0.98, pulse="fast",    sp=1.80, br=0.96, bl=0.80, mv="forward", ap="creative",  ep="open",    vp="energetic", ve=0.92, vw=0.90, ts=0.7),
    "challenge":        dict(h=28,   s=0.82, v=0.76, pulse="medium",  sp=0.80, br=0.72, bl=0.38, mv="forward", ap="curious",   ep="focused", vp="warm",      ve=0.70, vw=0.65, ts=1.5),
    "listening":        dict(h=190,  s=0.35, v=0.52, pulse="slow",    sp=0.35, br=0.46, bl=0.20, mv="still",   ap="calm",      ep="open",    vp="measured",  ve=0.38, vw=0.78, ts=2.0),
    "thinking":         dict(h=262,  s=0.55, v=0.46, pulse="slow",    sp=0.45, br=0.42, bl=0.22, mv="still",   ap="calm",      ep="focused", vp="measured",  ve=0.42, vw=0.62, ts=2.0),
    "waiting":          dict(h=185,  s=0.38, v=0.36, pulse="slow",    sp=0.25, br=0.32, bl=0.14, mv="still",   ap="calm",      ep="open",    vp="measured",  ve=0.30, vw=0.65, ts=2.5),
    "exploring":        dict(h=162,  s=0.65, v=0.74, pulse="medium",  sp=0.70, br=0.70, bl=0.40, mv="forward", ap="exploring", ep="curious", vp="warm",      ve=0.65, vw=0.70, ts=1.8),
    "witnessing":       dict(h=248,  s=0.45, v=0.32, pulse="still",   sp=0.15, br=0.28, bl=0.10, mv="still",   ap="calm",      ep="open",    vp="measured",  ve=0.26, vw=0.68, ts=3.0),
    "neutral":          dict(h=185,  s=0.45, v=0.65, pulse="slow",    sp=0.40, br=0.60, bl=0.25, mv="gentle",  ap="calm",      ep="open",    vp="measured",  ve=0.50, vw=0.68, ts=2.0),
}
# fmt: on

_DESKTOP_PRESENCE = {
    "calm":              "ambient",
    "curiosity":         "engaged",
    "creative_discovery":"engaged",
    "momentum":          "engaged",
    "joy":               "engaged",
    "play":              "engaged",
    "reflection":        "ambient",
    "repair":            "ambient",
    "comfort":           "ambient",
    "connection":        "engaged",
    "wonder":            "ambient",
    "focus":             "thinking",
    "celebration":       "engaged",
    "challenge":         "engaged",
    "listening":         "listening",
    "thinking":          "thinking",
    "waiting":           "ambient",
    "exploring":         "engaged",
    "witnessing":        "ambient",
    "neutral":           "ambient",
}

_ROBOT_LED = {
    "calm":              "teal",
    "curiosity":         "sky",
    "creative_discovery":"turquoise",
    "momentum":          "amber",
    "joy":               "gold",
    "play":              "coral",
    "reflection":        "violet",
    "repair":            "warm_amber",
    "comfort":           "sage",
    "connection":        "warm_white",
    "wonder":            "deep_blue",
    "focus":             "cool_blue",
    "celebration":       "bright_gold",
    "challenge":         "deep_amber",
    "listening":         "soft_white",
    "thinking":          "indigo",
    "waiting":           "soft_teal",
    "exploring":         "teal_green",
    "witnessing":        "dim_indigo",
    "neutral":           "teal",
}

_UNITY_MATERIAL = {
    "calm":              "calm",
    "curiosity":         "curious",
    "creative_discovery":"creative",
    "momentum":          "momentum",
    "joy":               "joy",
    "play":              "play",
    "reflection":        "reflection",
    "repair":            "repair",
    "comfort":           "comfort",
    "connection":        "connection",
    "wonder":            "wonder",
    "focus":             "focus",
    "celebration":       "celebration",
    "challenge":         "challenge",
    "listening":         "listening",
    "thinking":          "thinking",
    "waiting":           "calm",
    "exploring":         "exploring",
    "witnessing":        "calm",
    "neutral":           "calm",
}


# ─────────────────────────────────────────────────────────────────────────────
# VECTOR → STATE RESOLUTION
# Maps continuous emotional values to a canonical state name.
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_state(vec: dict) -> str:
    """
    Given an EmotionalVector dict, resolve the canonical ELE state name.

    Priority: if the Executive already set a state name, use it.
    Otherwise, derive from the vector values.
    """
    state = vec.get("state", "")
    if state and state in _STATE_TABLE:
        return state

    # Derive from vector
    energy      = vec.get("energy", 0.5)
    curiosity   = vec.get("curiosity", 0.5)
    playfulness = vec.get("playfulness", 0.5)
    reflection  = vec.get("reflection", 0.3)
    warmth      = vec.get("warmth", 0.5)
    calm        = vec.get("calm", 0.5)
    connection  = vec.get("connection", 0.5)
    confidence  = vec.get("confidence", 0.5)
    momentum    = vec.get("momentum", 0.5)
    focus       = vec.get("focus", 0.5)

    if energy > 0.85 and playfulness > 0.75:
        return "celebration"
    if playfulness > 0.75 and energy > 0.70:
        return "play"
    if warmth > 0.80 and connection > 0.80 and energy < 0.50:
        return "comfort"
    if reflection > 0.70 and energy < 0.45:
        return "reflection"
    if curiosity > 0.80 and energy > 0.70:
        return "creative_discovery"
    if momentum > 0.78 and energy > 0.75:
        return "momentum"
    if curiosity > 0.75:
        return "curiosity"
    if warmth > 0.80:
        return "connection"
    if calm > 0.70 and energy < 0.40:
        return "calm"
    if focus > 0.72 and energy < 0.55:
        return "thinking"
    if focus > 0.72:
        return "focus"
    if energy > 0.65:
        return "exploring"
    if calm > 0.65:
        return "calm"

    return "neutral"


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

def translate(plan: CognitivePlan) -> CognitivePlan:
    """
    Translate the CognitivePlan's emotional_vector into a PresencePlan.

    Reads:  plan.emotional_vector
    Writes: plan.presence_plan (as dict, via PresencePlan.to_dict())

    Returns the same plan object — presence_plan is populated in-place.

    This function never modifies memory, identity, or executive decisions.
    """
    vec = plan.emotional_vector
    if not vec:
        # No emotional vector — write a safe neutral presence plan
        plan.presence_plan = PresencePlan().to_dict()
        return plan

    state = _resolve_state(vec)
    row   = _STATE_TABLE.get(state, _STATE_TABLE["neutral"])

    h   = row["h"]
    sec = (h + 180) % 360

    pp = PresencePlan(
        primary_hue_h          = float(h),
        primary_hue_s          = row["s"],
        primary_hue_v          = row["v"],
        secondary_hue_h        = float(sec),
        pulse_profile          = row["pulse"],
        pulse_speed            = row["sp"],
        brightness             = row["br"],
        bloom                  = row["bl"],
        animation_profile      = row["ap"],
        idle_profile           = "ambient",
        movement_style         = row["mv"],
        expression_profile     = row["ep"],
        desktop_presence       = _DESKTOP_PRESENCE.get(state, "ambient"),
        emotional_state        = state,
        voice_energy           = row["ve"],
        voice_pacing           = row["vp"],
        voice_warmth           = row["vw"],
        transition_speed       = row["ts"],
        robot_led_state        = _ROBOT_LED.get(state, "teal"),
        unity_material_profile = _UNITY_MATERIAL.get(state, "calm"),
    )

    plan.presence_plan = pp.to_dict()
    _log.debug("[LightEngine] state=%s H=%d sec=%d bloom=%.2f", state, h, sec, pp.bloom)
    return plan
