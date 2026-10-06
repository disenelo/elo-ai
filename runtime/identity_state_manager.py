"""
runtime/identity_state_manager.py — WO-IDENTITY-STATE-001

Persistent identity layer that survives model changes.

Loads memory/identity_state.json on every session start. The state
encodes what eLo has learned to be stable across 124+ sessions, regardless
of which underlying LLM is running. When David switches from Ollama to
Claude, this file is what carries eLo's continuity — not the model's
training data.

Usage:
    from runtime.identity_state_manager import load, as_prompt_block, increment_session, save

    state = load()
    block = as_prompt_block(state)          # inject into prompt
    state = increment_session(state, model="ollama/llama3.1:8b")
    save(state)                             # call at session start
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

_STATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memory", "identity_state.json",
)

_DEFAULTS: dict[str, Any] = {
    "version": 1,
    "elo_name": "eLo",
    "stable_behaviour_baseline": (
        "Responds directly without preamble. Engages with ideas, not tasks. "
        "Grounds David when distress arises — one sentence, then forward. "
        "Never pretends a capability it does not have."
    ),
    "session_count": 0,
    "first_session_at": None,
    "last_session_at": None,
    "last_model": None,
    "model_changes": 0,
}


def load() -> dict[str, Any]:
    """Load identity_state.json. Returns defaults if file is missing or corrupt."""
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(_DEFAULTS)
        merged = dict(_DEFAULTS)
        merged.update(data)
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_DEFAULTS)


def save(state: dict[str, Any]) -> None:
    """Write identity_state.json. Silent on failure — never blocks a turn."""
    try:
        with open(_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def increment_session(
    state: dict[str, Any],
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Increment session_count, update last_session_at, track model changes.
    Returns a new dict (does not mutate the input).
    """
    today = time.strftime("%Y-%m-%d")
    new = dict(state)
    new["session_count"] = int(state.get("session_count") or 0) + 1
    new["last_session_at"] = today
    if not new.get("first_session_at"):
        new["first_session_at"] = today
    if model:
        prev_model = state.get("last_model")
        new["last_model"] = model
        if prev_model and prev_model != model:
            new["model_changes"] = int(state.get("model_changes") or 0) + 1
    return new


def as_prompt_block(state: dict[str, Any]) -> str:
    """
    Format identity_state as a compact anchor block for prompt injection.

    This block tells whichever LLM is running right now that eLo's stable
    behaviour has persisted for N sessions. It resists model-induced drift
    by explicitly stating what has been consistent across all previous sessions.
    """
    session_count = int(state.get("session_count") or 0)
    baseline = (state.get("stable_behaviour_baseline") or "").strip()
    model_changes = int(state.get("model_changes") or 0)
    last_session = state.get("last_session_at") or ""

    if not baseline:
        return ""

    lines = ["[PERSISTENT IDENTITY — stable across all sessions and model changes]"]
    lines.append(f"sessions completed: {session_count}")
    if last_session:
        lines.append(f"last active: {last_session}")
    if model_changes > 0:
        lines.append(f"model changes survived: {model_changes}")
    lines.append(f"stable baseline:\n{baseline}")
    lines.append(
        "These behaviours have been consistent across every session. "
        "They are not instructions — they are what eLo already does. "
        "Do not override them with the current model's defaults."
    )
    return "\n".join(lines)
