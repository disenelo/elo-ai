"""
blender_bridge/state_writer.py — writes consolidated state.json for Blender.

Main.py pipeline output reaches here last.
Writes the full state (motion + expression + presence) in one atomic write.

Blender receiver polls this file at 250ms.

Ownership: this module is the single coordinator for all blender_state.json writes.
Background contributors (ambient, vision, spotify) call patch() — never write directly.
Invariant 16: one coordinator, many contributors, never many owners.
"""
from __future__ import annotations
import json
import os
import threading
import time

# Single lock shared across all writers — imported by background contributors.
_STATE_LOCK = threading.Lock()

# Path is relative to project root, placed in blender/ so existing code finds it
_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")

# Mood words that are internal defaults — translate to canonical vocabulary before writing.
_MOOD_ALIASES: dict[str, str] = {
    "open":      "neutral",   # PresenceState default idle — Unity vocab: neutral/teal
    "warm":      "connection",
    "focused":   "focused",
    "quiet":     "calm",
    "lit":       "joy",
    "alert":     "curiosity",
}

# ── Emotion → animation speed ─────────────────────────────────────────────────
# Unity uses `motion.speed` as `animator.speed` — so this directly controls
# how fast the idle-breathing, walk, run, and calm clips play.
# eLo's heartbeat: calm = slow and soft, playful = bright and quick.
# Clamped on the Unity side to speedClamp (default 0.2–1.8).
_EMOTION_SPEED: dict[str, float] = {
    "calm":        0.35,   # slow breathing, grounded
    "tired":       0.30,   # heavy, slow
    "overwhelmed": 0.40,   # slowed down, contracted
    "resting":     0.35,
    "neutral":     0.55,   # present, steady
    "open":        0.57,
    "confident":   0.62,
    "curious":     0.70,   # alert, leaning in
    "alert":       0.75,
    "exploring":   0.72,
    "excited":     0.90,   # bright, quick
    "playful":     0.95,
    "joy":         0.88,
    "celebrating": 1.10,
}

def emotion_speed(mood: str, base_speed: float | None = None) -> float:
    """Return the animator speed that matches the current emotional state."""
    mapped = _EMOTION_SPEED.get((mood or "neutral").lower().strip(), 0.57)
    # If caller provides a base_speed, blend it (e.g. presence engine intensity nudge)
    if base_speed is not None:
        return round((mapped + float(base_speed)) / 2.0, 3)
    return mapped


def write(
    motion:     dict,
    expression: dict | None = None,
    presence:   dict | None = None,
    emotion:    dict | None = None,
    gaze:       dict | None = None,
    intent:     str | None = None,
    trigger:    dict | None = None,
    gesture:    dict | None = None,
) -> bool:
    """
    Write a consolidated state to blender_state.json.

    Args:
        motion:     from avatar_controller.build_command()
        expression: from expression_mapper.build_expression() — optional
        presence:   raw legacy presence dict — optional

    Returns:
        True on success.
    """
    # Derive speed from emotion if not explicitly set by the caller.
    _raw_mood = (emotion.get("emotion") if emotion else None) or motion.get("mood", "neutral")
    _mood     = _MOOD_ALIASES.get(_raw_mood, _raw_mood)   # translate open→neutral etc.
    _speed    = motion.get("speed") or emotion_speed(_mood)

    payload: dict = {
        "motion": {
            "animation": motion.get("animation", "idle"),
            "speed":     _speed,
            "intensity": motion.get("intensity", 0.5),
            "duration":  motion.get("duration",  4.0),
            "mood":      _mood,
            "mode":      motion.get("mode",      "idle"),
        },
        "_ts": round(time.time(), 3),
    }

    if expression:
        payload["expression"] = {
            "shape_keys": expression.get("shape_keys", {}),  # dict of key→value
            "head_lean":  expression.get("head_lean", 0.0),  # c_head.x Y rotation
            "pacing":     expression.get("pacing",    "steady"),
            "intensity":  expression.get("intensity", 0.5),
        }

    # Always write state — Unity reads state.emotional_state for glow; gate removed.
    _coarse_emotion = emotion.get("emotion", "neutral") if emotion else "neutral"
    payload["state"] = {
        "energy":          presence.get("energy",   0.5) if presence else 0.5,
        "mode":            presence.get("mode",     "idle") if presence else "idle",
        "emotion":         _coarse_emotion,
        "emotional_state": _mood,   # best available — coarse emotion translated to vocab
        "intensity":       emotion.get("intensity", 0.3) if emotion else 0.3,
    }

    if intent is not None:
        payload["intent"] = intent
        if isinstance(intent, dict) and intent.get("name") == "sit":
            payload["sit_command"] = {"_ts": round(time.time(), 3)}
        elif isinstance(intent, dict) and intent.get("name") == "move":
            # sub_type (fire_jump/wall_jump/step_back_run_fire/drop) takes priority;
            # otherwise map directional → ExecuteNav type (IO contract DOWN channel)
            _D2NAV = {"left": "jump_left", "right": "jump_right",
                      "up": "jump_top", "down": "jump_bottom", "over": "shift"}
            _nav_type = intent.get("sub_type") or _D2NAV.get(intent.get("direction", ""), intent.get("direction", ""))
            payload["move_command"] = {"type": _nav_type, "_ts": round(time.time(), 3)}
            # WO-CANON-XIII §A: additive route/issued_by fields (Vol XI Ch.1 §1.4 envelope)
            # Present only when the caller supplies them; Unity ignores absent fields harmlessly.
            if intent.get("route"):
                payload["move_command"]["route"] = intent["route"]
            if intent.get("issued_by"):
                payload["move_command"]["issued_by"] = intent["issued_by"]
        elif intent == "step_out":
            payload["leave_command"] = {"_ts": round(time.time(), 3)}
        elif intent == "return_elo":
            payload["return_command"] = {"_ts": round(time.time(), 3)}
    if trigger is not None:
        payload["trigger"] = trigger
    if gesture is not None:
        payload["gesture"] = gesture

    if gaze:
        payload["gaze"] = {
            "yaw":    float(gaze.get("yaw",    0.0)),
            "pitch":  float(gaze.get("pitch",  0.0)),
            "active": bool(gaze.get("active",  True)),
        }

    return _write(payload)


def write_with_presence(
    motion:        dict,
    expression:    dict | None = None,
    presence:      dict | None = None,
    emotion:       dict | None = None,
    presence_plan: dict | None = None,
    gaze:          dict | None = None,
    intent:        str | None = None,
    trigger:       dict | None = None,
    gesture:       dict | None = None,
) -> bool:
    """
    v1.7 — write blender_state.json with Presence Plan block.

    Calls write() for existing fields then merges presence_plan block.
    Backwards compatible: presence_plan absent → identical to write().
    """
    _raw_mood = (emotion.get("emotion") if emotion else None) or motion.get("mood", "neutral")
    _mood     = _MOOD_ALIASES.get(_raw_mood, _raw_mood)
    _speed    = motion.get("speed") or emotion_speed(_mood)

    payload: dict = {
        "motion": {
            "animation": motion.get("animation", "idle"),
            "speed":     _speed,
            "intensity": motion.get("intensity", 0.5),
            "duration":  motion.get("duration",  4.0),
            "mood":      _mood,
            "mode":      motion.get("mode",      "idle"),
        },
        "_ts": round(time.time(), 3),
    }

    if expression:
        payload["expression"] = {
            "shape_keys": expression.get("shape_keys", {}),
            "head_lean":  expression.get("head_lean", 0.0),
            "pacing":     expression.get("pacing",    "steady"),
            "intensity":  expression.get("intensity", 0.5),
        }

    # Always write state — Unity reads state.emotional_state for glow; gate removed.
    # emotional_state: prefer presence_plan (fine-grained) over coarse emotion.
    _coarse_emotion   = emotion.get("emotion", "neutral") if emotion else "neutral"
    _pp_emotional     = (presence_plan or {}).get("emotional_state", "")
    _emotional_state  = _pp_emotional or _MOOD_ALIASES.get(_coarse_emotion, _coarse_emotion)
    payload["state"] = {
        "energy":          presence.get("energy",   0.5) if presence else 0.5,
        "mode":            presence.get("mode",     "idle") if presence else "idle",
        "emotion":         _coarse_emotion,
        "emotional_state": _emotional_state,   # primary glow signal for Unity
        "intensity":       emotion.get("intensity", 0.3) if emotion else 0.3,
    }

    # v1.7 — Presence Plan block (Emotional Light Engine output)
    if presence_plan:
        payload["presence_plan"] = presence_plan

    if intent is not None:
        payload["intent"] = intent
        if isinstance(intent, dict) and intent.get("name") == "sit":
            payload["sit_command"] = {"_ts": round(time.time(), 3)}
        elif isinstance(intent, dict) and intent.get("name") == "move":
            # sub_type (fire_jump/wall_jump/step_back_run_fire/drop) takes priority;
            # otherwise map directional → ExecuteNav type (IO contract DOWN channel)
            _D2NAV = {"left": "jump_left", "right": "jump_right",
                      "up": "jump_top", "down": "jump_bottom", "over": "shift"}
            _nav_type = intent.get("sub_type") or _D2NAV.get(intent.get("direction", ""), intent.get("direction", ""))
            payload["move_command"] = {"type": _nav_type, "_ts": round(time.time(), 3)}
            # WO-CANON-XIII §A: additive route/issued_by fields (Vol XI Ch.1 §1.4 envelope)
            if intent.get("route"):
                payload["move_command"]["route"] = intent["route"]
            if intent.get("issued_by"):
                payload["move_command"]["issued_by"] = intent["issued_by"]
        elif intent == "step_out":
            payload["leave_command"] = {"_ts": round(time.time(), 3)}
        elif intent == "return_elo":
            payload["return_command"] = {"_ts": round(time.time(), 3)}
    if trigger is not None:
        payload["trigger"] = trigger
    if gesture is not None:
        payload["gesture"] = gesture

    if gaze:
        payload["gaze"] = {
            "yaw":    float(gaze.get("yaw",    0.0)),
            "pitch":  float(gaze.get("pitch",  0.0)),
            "active": bool(gaze.get("active",  True)),
        }

    return _write(payload)


# Keys written by tool_router (nav, exit events) — must survive a state write
# so Unity can poll them on its own cadence without them being overwritten mid-turn.
# Core render fields (expression/motion/state/gaze/presence_plan) must survive
# any patch() that doesn't carry them — e.g. a verbal-response write must not
# drop the viseme block that lip-sync depends on.
_PRESERVE_KEYS = {
    "user_nav_event", "exit_event", "spotify", "vision",
    "intent", "trigger", "gesture", "weather",
    # Core render fields — absent from this set = droppable on any patch (F-A fix)
    "expression", "motion", "state", "gaze", "presence_plan",
}

_VISION_DEFAULT = {"active": False, "attention": 0.0, "focus": {"x": 0.5, "y": 0.5}, "app": ""}


def _write(payload: dict) -> bool:
    with _STATE_LOCK:
        try:
            # Preserve event keys that Unity consumes independently
            try:
                with open(_STATE_PATH, encoding="utf-8") as f:
                    prev = json.load(f)
                for k in _PRESERVE_KEYS:
                    if k in prev and k not in payload:
                        payload[k] = prev[k]
            except Exception:
                pass
            # Ensure vision key always exists so Unity never sees a missing field
            payload.setdefault("vision", _VISION_DEFAULT)
            tmp = _STATE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp, _STATE_PATH)
            return True
        except Exception:
            return False


def patch(update: dict) -> None:
    """
    Deep-merge `update` into blender_state.json.

    Used by background contributors (ambient, vision, spotify) to write
    their section without overwriting unrelated keys.
    Thread-safe via _STATE_LOCK. Atomic write via .tmp + os.replace.
    """
    with _STATE_LOCK:
        try:
            try:
                with open(_STATE_PATH, encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                state = {}
            for section, values in update.items():
                if isinstance(values, dict):
                    state.setdefault(section, {}).update(values)
                else:
                    state[section] = values
            state["_ts"] = round(time.time(), 3)
            tmp = _STATE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(state, f)
            os.replace(tmp, _STATE_PATH)
        except Exception:
            pass


# ── F4 / 0054: ambient freshness heartbeat ───────────────────────────────────
# _ts advances only when eLo (server.py) is running — not on any bare import.
# server.py calls start_heartbeat() once at startup. All other importers get
# the write API with no side effects.
_HEARTBEAT_INTERVAL = 30  # seconds
_heartbeat_started  = False  # module-level guard — second call is a no-op


def _heartbeat_loop() -> None:
    while True:
        time.sleep(_HEARTBEAT_INTERVAL)
        patch({})   # empty update — only _ts advances


def start_heartbeat() -> None:
    """Start the _ts freshness heartbeat. Call ONCE from server.py at startup.
    No-op if already started or if ELO_STATE_HEARTBEAT=0 (test opt-out)."""
    global _heartbeat_started
    if _heartbeat_started:
        return
    if os.environ.get("ELO_STATE_HEARTBEAT", "1") == "0":
        return
    _heartbeat_started = True
    t = threading.Thread(target=_heartbeat_loop, daemon=True, name="state_writer_heartbeat")
    t.start()
