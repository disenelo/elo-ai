"""
runtime/wake_thought.py — S2 Phase 3: the first thought after a dream is the dream's.

STACK.md: "Phase 3 — Dream state integration. After S3 Phase 1 live. Dream
inner_thought from `wake_inner_thought` field."

`wake_inner_thought` returned 0 matches repo-wide. The field was never built,
so the phase could not have run.

WHAT IT DOES. wake_from_dream() already folds a dream's insight into mood,
curiosity and satisfaction — proven in test_dream_changes_state. What it does
not do is let the dream be the thing eLo is thinking when he next speaks. The
insight exists, is written to the journal, and never surfaces as a thought.

So on waking, the dream's insight is held as the NEXT turn's inner_thought,
and consumed when used. One turn only: a dream should colour the thought he
wakes with, not every thought after it.

WHY A FILE AND NOT A SELF-MODEL FIELD. EloSelfState has 36 fields and is
loaded, mutated and saved on nearly every turn by several paths. A 37th field
that must be cleared exactly once is a race waiting to happen. This is a
single-slot handoff with its own file, written at wake and emptied on read.

Not authored text: the insight is whatever the dream produced. If a dream
produced nothing, there is no wake thought and the normal generation runs.
"""
from __future__ import annotations

import json
import logging
import os

_log = logging.getLogger("elo.wake_thought")

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "wake_inner_thought.json",
)


def hold(insight: str, *, dream_id: str = "") -> bool:
    """Keep a dream's insight as the next turn's inner thought. "" clears it."""
    text = str(insight or "").strip()
    try:
        os.makedirs(os.path.dirname(_PATH), exist_ok=True)
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump({"wake_inner_thought": text, "dream_id": dream_id}, f)
        if text:
            _log.info("wake thought held from dream %s: %r", dream_id or "?", text[:60])
        return True
    except Exception:
        return False


def take() -> str:
    """
    The held wake thought, cleared as it is read.

    Consumed on read so it colours the turn eLo wakes into and not every turn
    after it. A dream that kept re-surfacing would stop being a dream and
    start being a personality.
    """
    try:
        with open(_PATH, encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return ""
    text = str(data.get("wake_inner_thought", "") or "").strip()
    if text:
        hold("")
    return text


def peek() -> str:
    """Read without consuming — for tests and inspection only."""
    try:
        with open(_PATH, encoding="utf-8") as f:
            return str((json.load(f) or {}).get("wake_inner_thought", "") or "").strip()
    except Exception:
        return ""
