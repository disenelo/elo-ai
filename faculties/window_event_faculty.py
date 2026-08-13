"""
faculties/window_event_faculty.py — WO-094: Window Event Faculty (Builder half)

eLo notices window events and chooses what to do — never as a reflex.
Decision: ignore · glance · observe · relocate to the new surface.

This is the BRAIN side only. The Designer (Unity) emits events to unity_events.json.
The split follows the WO-086 pattern: Designer emits UP, Builder brain decides, sends DOWN.

Guardrails:
  - Never fabricate: only claims to "see" something if the event arrived (ADR-Exec-001)
  - Stays peripheral when David is actively working (user_active=True)
  - Empty state → ignore (no decision from nothing)
  - Decision is advisory: goes through the standard action path, ACK-gated

Decision dict: {action, goal_surface, reason, source: "window_event_faculty", priority: "low"}
"""
from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from self.elo_self_model import EloSelfState

_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EVENTS_PATH = os.path.join(_ROOT, "blender", "unity_events.json")

# Valid window event types we handle
_WINDOW_EVENT_TYPES: frozenset[str] = frozenset({
    "window_closed", "window_opened", "window_moved",
})

# WO-099: gaze event type (discrete noticing — debounced by Unity before emit)
_GAZE_EVENT_TYPE: str = "gaze_target_changed"

# Behaviour weights per event type (0=never, 1=always)
_ACTION_WEIGHTS: dict[str, dict[str, float]] = {
    "window_opened": {"relocate": 0.4, "observe": 0.3, "glance": 0.2, "ignore": 0.1},
    "window_closed": {"ignore": 0.5, "glance": 0.3, "observe": 0.2, "relocate": 0.0},
    "window_moved":  {"glance": 0.4, "observe": 0.3, "ignore": 0.3, "relocate": 0.0},
}


# ── Event consumption ─────────────────────────────────────────────────────────

def consume_window_events(events_path: str | None = None) -> list[dict]:
    """
    Read window events from unity_events.json and return any that are window-type.
    Non-destructive — does not clear the file (ambient_engine owns the file lifecycle).
    Returns [] if file absent, unreadable, or no window events.
    """
    try:
        path = events_path or _EVENTS_PATH
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        ev_type = data.get("type", "")
        if ev_type in _WINDOW_EVENT_TYPES:
            return [data]
        return []
    except Exception:
        return []


def consume_gaze_events(events_path: str | None = None) -> list[dict]:
    """
    WO-099: Read gaze_target_changed events from unity_events.json.
    Unity debounces before emitting — each event is a settled new gaze target.
    Returns [] if no gaze event or file absent.
    """
    try:
        path = events_path or _EVENTS_PATH
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("type") == _GAZE_EVENT_TYPE:
            return [data]
        return []
    except Exception:
        return []


def describe_gaze(event: dict) -> str:
    """
    WO-099: Produce a short verified-speech string from a gaze_target_changed event.
    Only says what the event proves — never fabricates (ADR-Exec-001).
    Returns "" when the event carries no useful info.
    """
    if not event or event.get("type") != _GAZE_EVENT_TYPE:
        return ""
    gaze = event.get("gaze", {})
    on_window = event.get("on_window", False)
    window = event.get("window", "")
    issued_by = event.get("issued_by", "")
    if on_window and window:
        src = f" ({issued_by})" if issued_by and issued_by != "brain" else ""
        return f"eLo noticed '{window}'{src}"
    return ""


# ── Decision engine ───────────────────────────────────────────────────────────

def decide_window_event(
    event: dict,
    state: "EloSelfState | None" = None,
    user_active: bool = False,
) -> dict | None:
    """
    Produce a decision for a window event or return None (legitimately ignore).

    Guardrails:
      - No state → ignore (can't reason about nothing)
      - user_active=True → peripheral (stay out of David's way)
      - eLo's own surface closed → handled by Unity survival recovery; not our decision here
      - ADR-Exec-001: decision cites the event as its source; never claims to "know" without it
    """
    if state is None:
        return None

    # Gate: at least some established self-state required
    has_history = bool(state.focal_thread or state.lifetime_threads or state.inner_events)
    if not has_history:
        return None

    ev_type = event.get("type", "")
    if ev_type not in _WINDOW_EVENT_TYPES:
        return None

    # David is actively working → stay peripheral
    if user_active:
        return {
            "action":       "peripheral",
            "goal_surface": None,
            "reason":       f"{ev_type} noticed; David is active → staying peripheral",
            "source":       "window_event_faculty",
            "priority":     "low",
        }

    # eLo's own surface closing → Unity survival recovery handles it; our choice = nothing
    if event.get("is_elo_surface"):
        return None

    # Determine action based on event type + state
    surface_id = event.get("id", "")
    surface_rect = event.get("rect", {})

    if ev_type == "window_opened":
        # Big new surface → investigate
        action = "observe" if state.curiosity >= 0.65 else "glance"
        reason = f"new window appeared ({surface_id}); curiosity {state.curiosity:.2f}"
    elif ev_type == "window_closed":
        # Something left — glance at the gap, then settle
        action = "glance"
        reason = f"window closed ({surface_id}); noting the gap"
    else:  # window_moved
        action = "glance"
        reason = f"window moved ({surface_id}); noting position change"

    return {
        "action":       action,
        "goal_surface": surface_id,
        "reason":       reason,
        "source":       "window_event_faculty",
        "priority":     "low",
        "event_ts":     float(event.get("_ts", time.time())),
    }
