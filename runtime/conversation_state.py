"""
runtime/conversation_state.py — WO-CONVERSATION-001

Lightweight module-level conversation session state.
Holds the cross-turn conversation context that spine.py needs at CognitiveState
assembly time but that only server.py can write (because the response is generated
by the LLM after the spine returns).

Writers: server.py — calls update_after_response() once per successful response.
Readers: spine.py — reads at CognitiveState construction.
         server.py — reads active_topic + referents when building MemoryCandidate.

Thread safety: single-threaded server; no locking needed.
"""

from __future__ import annotations

import time as _time

# ── Session state ─────────────────────────────────────────────────────────────

_last_elo_response: str   = ""      # last thing eLo said (up to 500 chars)
_active_topic:      str   = ""      # current conversation topic
_prev_topic:        str   = ""      # topic from the turn before, for TOPIC_CHANGE detection
_referents:         dict  = {}      # {pronoun/ref_word: entity_name} from recent turns
_thread_history:    list  = []      # [{topic, turns}] ring buffer, max 5 entries
_last_response_at:  float = 0.0    # WO-B1-0140: epoch seconds of last successful response


# ── API ───────────────────────────────────────────────────────────────────────

def get_last_elo_response() -> str:
    return _last_elo_response


def get_last_response_time() -> float:
    """WO-B1-0140: epoch seconds when the last eLo response was recorded (0.0 = never)."""
    return _last_response_at


def get_active_topic() -> str:
    return _active_topic


def get_prev_topic() -> str:
    return _prev_topic


def get_referents() -> dict:
    return dict(_referents)


def get_thread_history() -> list:
    return list(_thread_history)


def topic_changed() -> bool:
    """True when active_topic differs from prev_topic (non-empty)."""
    return bool(_prev_topic and _active_topic and _active_topic != _prev_topic)


def update_after_response(
    *,
    elo_response:  str,
    active_topic:  str = "",
    referents:     dict | None = None,
) -> None:
    """
    Called by server.py after each successful LLM response.
    Updates all session state for the next turn.
    """
    global _last_elo_response, _active_topic, _prev_topic, _referents, _thread_history, _last_response_at

    _last_elo_response = (elo_response or "")[:500]
    _last_response_at  = _time.time()  # WO-B1-0140: record when eLo last spoke

    new_topic = (active_topic or "").strip()
    if new_topic and new_topic != _active_topic:
        _prev_topic = _active_topic
        # Add old topic to thread_history (ring buffer, max 5)
        if _active_topic:
            _thread_history = (
                _thread_history + [{"topic": _active_topic, "turns": 1}]
            )[-5:]
        _active_topic = new_topic
    elif not new_topic:
        _prev_topic = _active_topic

    if referents is not None:
        _referents = dict(referents)


def reset() -> None:
    """Called at session start to clear cross-session bleed."""
    global _last_elo_response, _active_topic, _prev_topic, _referents, _thread_history, _last_response_at
    _last_elo_response = ""
    _active_topic      = ""
    _prev_topic        = ""
    _referents         = {}
    _thread_history    = []
    _last_response_at  = 0.0
