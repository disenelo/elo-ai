"""
blender_bridge/brain_state_writer.py — writes brain_state.json for the Quantum One Brain UI.

Outputs per-vortex cognitive system signals for EloBrainCluster.cs in Unity Presence.
Aligned with ONE_BRAIN_QUANTUM_SPEC.md: 9 systems → 9 vortices, each with energy + valence.

Schema: brain_state/v1
Path:   blender/brain_state.json  (same dir as blender_state.json — Unity polls both)

Called once per turn by server.py after the main blender_state write.
Also called by ambient_thought() when eLo enters/exits dream state.
"""
from __future__ import annotations
import json
import os
import time

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "blender", "brain_state.json")

# 9 cognitive systems — maps to 9 vortices in EloBrainCluster.cs
_SYSTEMS = ("intent", "attention", "emotion", "memory", "motion", "body", "vision", "expression", "voice")

# Emotions that carry positive (expansive/high-frequency) valence → circulation sign +1
_POSITIVE_EMOTIONS = {
    "joy", "excited", "playful", "celebrating", "curious", "exploring",
    "connection", "confident", "open", "warm", "focused", "alert", "neutral",
}

# Emotions that carry contracted/low-frequency valence → circulation sign -1
_NEGATIVE_EMOTIONS = {
    "overwhelmed", "tired", "resting", "sad", "frustrated", "anxious",
    "worried", "lost", "heavy",
}


def _valence(emotion: str) -> int:
    """Return ±1 circulation sign from emotional valence. Positive = expansive."""
    e = (emotion or "").lower().strip()
    if e in _POSITIVE_EMOTIONS:
        return 1
    if e in _NEGATIVE_EMOTIONS:
        return -1
    return 1   # unknown → positive default


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def _pacing_to_energy(pacing: str) -> float:
    """Translate expression pacing string to a 0–1 energy value."""
    return {
        "rapid":    0.9,
        "quick":    0.75,
        "warm":     0.6,
        "steady":   0.5,
        "slow":     0.3,
        "quiet":    0.2,
        "silent":   0.0,
    }.get((pacing or "steady").lower(), 0.5)


def _mode_to_energy(mode: str) -> float:
    """Translate eLo OS mode string to a cluster_energy baseline."""
    return {
        "dreaming":   0.15,
        "sleeping":   0.05,
        "idle":       0.35,
        "listening":  0.55,
        "thinking":   0.65,
        "speaking":   0.75,
        "excited":    0.85,
        "calm":       0.25,
    }.get((mode or "idle").lower(), 0.4)


def _detail_intent(intent: str, intensity: float) -> str:
    if not intent:
        return "still" if intensity < 0.3 else "present"
    return intent[:40]


def _detail_attention(vision_active: bool, vision_app: str, curiosity: float, attention: float) -> str:
    if vision_active and vision_app:
        return f"watching {vision_app}"
    if vision_active:
        return f"screen attention {attention:.0%}"
    if curiosity > 0.6:
        return "curious, searching"
    return "listening"


def _detail_emotion(emotion: str, intensity: float, mood: float) -> str:
    base = emotion or "neutral"
    if intensity > 0.7:
        return f"{base} — strongly"
    if intensity > 0.4:
        return f"{base}"
    if mood > 0.6:
        return f"settling toward {base}"
    return f"quietly {base}"


def _detail_memory(energy: float, curiosity: float) -> str:
    if energy > 0.45:
        return "recalling recent threads"
    if curiosity > 0.5:
        return "holding context"
    return "resting"


def _detail_motion(mode: str, speed: float) -> str:
    if speed > 0.8:
        return f"moving quickly — {mode}"
    if speed > 0.4:
        return f"{mode}"
    return "still"


def _detail_body(intensity: float, mood: float) -> str:
    if intensity > 0.6:
        return "fully present"
    if mood > 0.5:
        return "grounded"
    return "settled"


def _detail_vision(active: bool, app: str, attention: float) -> str:
    if active:
        return f"focused on {app or 'screen'} ({attention:.0%})"
    return "not looking"


def _detail_expression(pacing: str, intensity: float) -> str:
    if intensity > 0.6:
        return f"expressive — {pacing}"
    if pacing == "silent":
        return "quiet"
    return pacing


def _detail_voice(active: bool, pacing: str) -> str:
    if active:
        return f"speaking — {pacing}"
    return "listening"


def publish(
    emotion:        str         = "neutral",
    intensity:      float       = 0.3,
    energy:         float       = 0.5,
    mode:           str         = "idle",
    motion_speed:   float       = 0.55,
    motion_intensity: float     = 0.5,
    vision_active:  bool        = False,
    vision_attention: float     = 0.0,
    vision_app:     str         = "",
    expression_intensity: float = 0.5,
    expression_pacing:    str   = "steady",
    intent:         str         = "",
    memory_energy:  float       = -1.0,    # -1 = derive from state
    voice_active:   bool        = False,
    self_mood:      float       = 0.5,     # from EloSelfState.mood
    self_curiosity: float       = 0.5,     # from EloSelfState.curiosity
    show_one_brain: bool        = True,
) -> bool:
    """
    Write brain_state.json with per-vortex signals for all 9 cognitive systems.

    Derives energy values from the same signals that drive blender_state.json so
    both files stay consistent without separate bookkeeping.
    """
    val = _valence(emotion)

    # ── Per-system energy ────────────────────────────────────────────────────
    # intent: rises with intensity and when a meaningful intent string is present
    _intent_energy = _clamp(intensity * 0.8 + (0.2 if intent else 0.0))

    # attention: vision attention if screen-vision is active, else curiosity-linked
    _attention_energy = _clamp(
        vision_attention if vision_active else self_curiosity * 0.6 + intensity * 0.2
    )

    # emotion: primary driver — intensity + energy blend
    _emotion_energy = _clamp((intensity + energy) / 2.0)

    # memory: explicit if passed, else moderate background hum
    if memory_energy >= 0.0:
        _memory_energy = _clamp(memory_energy)
    else:
        # Derive: memory is quietly active when eLo is curious or in conversation
        _memory_energy = _clamp(self_curiosity * 0.4 + intensity * 0.2)

    # motion: normalized from animator speed (0.2–1.2 → 0.0–1.0)
    _motion_energy = _clamp((motion_speed - 0.2) / 1.0)

    # body: physical presence intensity — close to motion but weighted toward intensity
    _body_energy = _clamp((motion_intensity + intensity) / 2.0)

    # vision: active when screen-vision running
    _vision_energy = _clamp(vision_attention) if vision_active else 0.0

    # expression: mouth/face activity
    _expression_energy = _clamp(expression_intensity)

    # voice: TTS active or pacing implies speaking energy
    _voice_energy = _clamp(expression_intensity * 0.8) if voice_active else 0.0

    # ── INT7-HEAT: rate (0–1 processing urgency → pulse speed) ──────────────
    _intent_rate     = _clamp(intensity * 0.7 + (0.3 if intent else 0.0))
    _attention_rate  = _clamp(vision_attention if vision_active else self_curiosity * 0.5 + intensity * 0.3)
    _emotion_rate    = _clamp(intensity)
    _memory_rate     = _clamp(max(self_curiosity, _memory_energy) * 0.8)
    _motion_rate     = _clamp((motion_speed - 0.2) / 1.0)
    _body_rate       = _clamp(intensity * 0.8)
    _vision_rate     = _clamp(vision_attention) if vision_active else 0.05
    _expr_rate       = _pacing_to_energy(expression_pacing)
    _voice_rate      = _clamp(expression_intensity) if voice_active else 0.05

    # ── INT7-HEAT: confidence (0–1 certainty → opacity/saturation) ──────────
    _intent_conf     = _clamp(0.8 if intent else 0.35 + intensity * 0.2)
    _attention_conf  = _clamp(vision_attention if vision_active else 0.4 + self_curiosity * 0.4)
    _emotion_conf    = _clamp(0.5 + intensity * 0.5)
    _memory_conf     = _clamp(0.3 + min(_memory_energy, 1.0) * 0.7)
    _motion_conf     = _clamp(0.6 if motion_speed > 0.3 else 0.3)
    _body_conf       = _clamp(0.5 + intensity * 0.4 + self_mood * 0.1)
    _vision_conf     = _clamp(vision_attention + 0.1) if vision_active else 0.2
    _expr_conf       = _clamp(0.4 + expression_intensity * 0.6)
    _voice_conf      = _clamp(0.7 + expression_intensity * 0.3) if voice_active else 0.25

    systems: dict[str, dict] = {
        "intent":     {
            "energy":     round(_intent_energy,     3), "valence": val,  "active": bool(intent),
            "rate":       round(_intent_rate,        3), "confidence": round(_intent_conf,    3),
            "label":      intent[:20] if intent else "still",
            "detail":     _detail_intent(intent, intensity),
        },
        "attention":  {
            "energy":     round(_attention_energy,  3), "valence": val,  "active": True,
            "rate":       round(_attention_rate,     3), "confidence": round(_attention_conf, 3),
            "label":      vision_app or "present",
            "detail":     _detail_attention(vision_active, vision_app, self_curiosity, vision_attention),
        },
        "emotion":    {
            "energy":     round(_emotion_energy,    3), "valence": val,  "active": True,
            "rate":       round(_emotion_rate,       3), "confidence": round(_emotion_conf,   3),
            "label":      emotion,
            "detail":     _detail_emotion(emotion, intensity, self_mood),
        },
        "memory":     {
            "energy":     round(_memory_energy,     3), "valence": 1,    "active": _memory_energy > 0.1,
            "rate":       round(_memory_rate,        3), "confidence": round(_memory_conf,    3),
            "label":      "recalling" if _memory_energy > 0.3 else "idle",
            "detail":     _detail_memory(_memory_energy, self_curiosity),
        },
        "motion":     {
            "energy":     round(_motion_energy,     3), "valence": val,  "active": motion_speed > 0.25,
            "rate":       round(_motion_rate,        3), "confidence": round(_motion_conf,    3),
            "label":      mode,
            "detail":     _detail_motion(mode, motion_speed),
        },
        "body":       {
            "energy":     round(_body_energy,       3), "valence": val,  "active": True,
            "rate":       round(_body_rate,          3), "confidence": round(_body_conf,      3),
            "label":      "present",
            "detail":     _detail_body(intensity, self_mood),
        },
        "vision":     {
            "energy":     round(_vision_energy,     3), "valence": 1,    "active": vision_active,
            "rate":       round(_vision_rate,        3), "confidence": round(_vision_conf,    3),
            "label":      vision_app if vision_active else "idle",
            "detail":     _detail_vision(vision_active, vision_app, vision_attention),
        },
        "expression": {
            "energy":     round(_expression_energy, 3), "valence": val,  "active": expression_intensity > 0.1,
            "rate":       round(_expr_rate,          3), "confidence": round(_expr_conf,      3),
            "label":      expression_pacing,
            "detail":     _detail_expression(expression_pacing, expression_intensity),
        },
        "voice":      {
            "energy":     round(_voice_energy,      3), "valence": val,  "active": voice_active,
            "rate":       round(_voice_rate,         3), "confidence": round(_voice_conf,     3),
            "label":      "speaking" if voice_active else "silent",
            "detail":     _detail_voice(voice_active, expression_pacing),
        },
    }

    # cluster_energy = mean of active system energies (drives overall vortex clustering)
    active_energies = [s["energy"] for s in systems.values() if s["active"]]
    cluster_energy  = round(sum(active_energies) / len(active_energies), 3) if active_energies else 0.0

    payload = {
        "schema":         "brain_state/v1",
        "_ts":            round(time.time(), 3),
        "cluster_energy": cluster_energy,
        "show_one_brain": show_one_brain,
        "systems":        systems,
    }

    try:
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, _STATE_PATH)
        return True
    except Exception:
        return False
