"""
WO-GAME-006: Game Embodiment Event Bus

Structured event bus connecting the Unity game world to the eLo OS AI pipeline.

Schema (agreed between Builder 1 and Game seat):
{
  "embodiment": "game",
  "event_type": "item_collected | enemy_encountered | life_lost | level_cleared | player_action",
  "detail": {...},
  "timestamp": "ISO8601"
}

Events are written to game_events.json by the game seat / Unity bridge.
The OS AI pipeline reads via poll_events() and processes via ingest_event().
Memory is tagged with embodiment="game", context="simulated".
"""

from __future__ import annotations
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

_BUS_PATH = Path(__file__).parent.parent / "blender" / "game_events.json"
_MAX_EVENTS = 50  # ring buffer — oldest dropped when full

VALID_EVENT_TYPES = frozenset({
    "item_collected",
    "enemy_encountered",
    "life_lost",
    "level_cleared",
    "player_action",
})


# ── I/O helpers ──────────────────────────────────────────────────────────────

def _load() -> list[dict]:
    try:
        with open(_BUS_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(events: list[dict]) -> None:
    _BUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(_BUS_PATH) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(events[-_MAX_EVENTS:], f, indent=2)
    os.replace(tmp, _BUS_PATH)


# ── Public API ────────────────────────────────────────────────────────────────

def emit_event(event_type: str, detail: dict[str, Any] | None = None) -> dict:
    """
    Write a structured game event to the bus.
    Called by Unity bridge or game seat when a game event fires.
    """
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"Unknown event_type: {event_type!r}. Valid: {VALID_EVENT_TYPES}")

    event = {
        "embodiment": "game",
        "event_type": event_type,
        "detail": detail or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "consumed": False,
    }
    events = _load()
    events.append(event)
    _save(events)
    _logger.debug("game_event_bus: emitted %s — %s", event_type, detail)
    return event


def poll_events(mark_consumed: bool = True) -> list[dict]:
    """
    Return unconsumed game events. If mark_consumed=True, marks them consumed.
    Called by the OS AI pipeline on each turn when game_mode is active.
    """
    events = _load()
    pending = [e for e in events if not e.get("consumed")]
    if pending and mark_consumed:
        for e in events:
            if not e.get("consumed"):
                e["consumed"] = True
        _save(events)
    return pending


def clear_bus() -> None:
    """Remove all events from the bus."""
    _save([])


def ingest_event(event: dict) -> str:
    """
    Convert a raw game event into a natural-language context block for injection
    into the OS AI pipeline's system prompt.
    """
    et = event.get("event_type", "player_action")
    detail = event.get("detail", {})
    ts = event.get("timestamp", "")

    TEMPLATES: dict[str, str] = {
        "item_collected":    "David just collected an item in the game: {detail}.",
        "enemy_encountered": "David encountered an enemy: {detail}.",
        "life_lost":         "David lost a life in the game: {detail}.",
        "level_cleared":     "David cleared a level: {detail}.",
        "player_action":     "David performed an action in the game: {detail}.",
    }
    detail_str = json.dumps(detail) if detail else "no additional detail"
    text = TEMPLATES.get(et, "A game event occurred: {detail}.").format(detail=detail_str)
    return f"[GAME EVENT — embodiment:game, context:simulated] {text}"
