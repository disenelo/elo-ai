"""
core/session_persistence.py — eLo AI session persistence layer.

Saves and restores in-memory engine state between runs.

What is persisted:
    StateEngine state  — current state, history, turn count, pending
    Active mode        — studio / companion / adventure

What is NOT persisted (already handled elsewhere):
    Memory interactions — memory/interactions.json  (memory_engine)
    Session metadata    — memory/session.json       (memory_engine)
    Export snapshot     — memory/export_memory.md   (memory_engine)

What is intentionally NOT persisted:
    Kernel loop detector — resets cleanly each session (correct behaviour)
    Identity/emotion     — derived fresh each turn from input (stateless)

Save file: memory/session_state.json

No routing logic. No behavioural changes. Pure read/write.
"""

import json
import os
from datetime import datetime


_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memory", "session_state.json"
)


# ── save ──────────────────────────────────────────────────────────────────────

def save_session(engine, path: str = None) -> str:
    """
    Save the current session state to disk.

    Args:
        engine: A CoreEngine instance.
        path:   Override save path. Default: memory/session_state.json.

    Returns:
        Path written to.
    """
    out = path or _DEFAULT_PATH

    se = engine.state_engine
    state = {
        "saved_at":    datetime.utcnow().isoformat() + "Z",
        "active_mode": engine._active_mode,
        "state_engine": {
            "state":         se.state,
            "turn_count":    se.turn_count,
            "history":       list(se._history),
            "pending_state": se._pending_state,
            "pending_count": se._pending_count,
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as f:
        json.dump(state, f, indent=2)

    return out


# ── restore ───────────────────────────────────────────────────────────────────

def restore_session(engine, path: str = None) -> bool:
    """
    Restore session state from disk into a CoreEngine instance.

    Args:
        engine: A CoreEngine instance (state will be applied in-place).
        path:   Override load path. Default: memory/session_state.json.

    Returns:
        True if restored, False if no save file found.
    """
    src = path or _DEFAULT_PATH
    if not os.path.exists(src):
        return False

    try:
        with open(src) as f:
            saved = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    # restore active mode
    mode = saved.get("active_mode", "companion")
    if mode in ("studio", "companion", "adventure"):
        engine._active_mode = mode

    # restore state engine
    se_data = saved.get("state_engine", {})
    se = engine.state_engine

    saved_state = se_data.get("state", "exploring")
    if saved_state in se._NATURAL_TRANSITIONS if hasattr(se, "_NATURAL_TRANSITIONS") else True:
        se._state         = saved_state
    se.turn_count         = int(se_data.get("turn_count", 0))
    se._history           = list(se_data.get("history", []))
    se._pending_state     = se_data.get("pending_state")
    se._pending_count     = int(se_data.get("pending_count", 0))

    return True


# ── clear ─────────────────────────────────────────────────────────────────────

def clear_session(path: str = None):
    """Remove the saved session file (start fresh next run)."""
    src = path or _DEFAULT_PATH
    if os.path.exists(src):
        os.remove(src)


# ── metadata ──────────────────────────────────────────────────────────────────

def session_info(path: str = None) -> dict:
    """
    Return metadata about the saved session without loading it into an engine.
    Returns empty dict if no save file exists.
    """
    src = path or _DEFAULT_PATH
    if not os.path.exists(src):
        return {}
    try:
        with open(src) as f:
            saved = json.load(f)
        se = saved.get("state_engine", {})
        return {
            "saved_at":    saved.get("saved_at", ""),
            "active_mode": saved.get("active_mode", ""),
            "state":       se.get("state", ""),
            "turn_count":  se.get("turn_count", 0),
        }
    except Exception:
        return {}
