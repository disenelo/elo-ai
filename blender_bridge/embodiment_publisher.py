"""
blender_bridge/embodiment_publisher.py — EmbodimentState Publisher

Single authoritative publisher from CognitivePlan → blender_state.json.

Replaces the scattered _state_write() / _state_write_presence() calls in
server.py with ONE call per turn. The plan carries all the data; this module
assembles it into the EmbodimentState shape and publishes via state_writer.

Architecture rule: nothing else writes blender_state.json per-turn.
Background contributors (ambient, vision, spotify) still use patch().
"""
from __future__ import annotations


def publish(plan: "CognitivePlan", gaze: "dict | None" = None) -> bool:
    """
    Publish CognitivePlan as blender_state.json.

    Args:
        plan — fully populated CognitivePlan from spine.run()
        gaze — optional {yaw, pitch, active} from gaze system

    Returns:
        True on successful write.
    """
    from blender_bridge.state_writer import write_with_presence as _write

    # ── Motion command from emotional vector ──────────────────────────────────
    ev = plan.emotional_vector or {}
    pp = plan.presence_plan    or {}

    # Presence plan carries the canonical motion fields from the Light Engine
    animation = pp.get("animation", "idle")
    speed     = pp.get("speed",     0.55)
    intensity = pp.get("intensity", 0.5)
    duration  = pp.get("duration",  4.0)
    mood      = pp.get("emotional_state", "neutral")
    mode      = pp.get("mode",      "idle")

    # Translate 20-state light engine vocabulary → Unity MoodPalette vocabulary.
    # Source of truth: blender_bridge/shared_tables.py (WO-010).
    from blender_bridge.shared_tables import resolve_mood
    mood = resolve_mood(mood)

    motion = {
        "animation": animation,
        "speed":     speed,
        "intensity": intensity,
        "duration":  duration,
        "mood":      mood,
        "mode":      mode,
    }

    # ── Expression from presence plan ─────────────────────────────────────────
    expression = None
    if pp.get("shape_keys") or pp.get("head_lean") is not None:
        expression = {
            "shape_keys": pp.get("shape_keys", {}),
            "head_lean":  pp.get("head_lean",  0.0),
            "pacing":     pp.get("pacing",     "steady"),
            "intensity":  pp.get("intensity",  0.5),
        }

    # ── Presence (legacy top-level presence dict) ─────────────────────────────
    presence = {
        "energy": ev.get("energy", 0.5),
        "mode":   mode,
    }

    # ── Emotion ───────────────────────────────────────────────────────────────
    emotion = {
        "emotion":   mood,
        "intensity": pp.get("intensity", 0.3),
    }

    # ── Intent, trigger, gesture from Presence Faculty ────────────────────────
    intent  = plan.movement_intent  if plan.movement_intent  else None
    trigger = plan.movement_trigger if plan.movement_trigger else None
    gesture = plan.movement_gesture if plan.movement_gesture else None

    # ── Publish ───────────────────────────────────────────────────────────────
    return _write(
        motion        = motion,
        expression    = expression,
        presence      = presence,
        emotion       = emotion,
        presence_plan = pp if pp else None,
        gaze          = gaze,
        intent        = intent,
        trigger       = trigger,
        gesture       = gesture,
    )
