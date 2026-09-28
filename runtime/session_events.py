"""
runtime/session_events.py — WO-SESSION-EVENT-FEED-001

Session event feed for SPG grounding. Logs real events during a session
(turns, capability executions, session start/stop) to self/journals/session_events.jsonl.
Provides a compact session summary for prompt injection so the LLM can reference
actual session activity rather than hallucinating generic observations.

Blocks resolved: COG-023 (notice what changed since last session), COG-025 (grounded observations).
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid

_log = logging.getLogger(__name__)

_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EVENTS_LOG   = os.path.join(_ROOT, "self", "journals", "session_events.jsonl")
_SESSION_FILE = os.path.join(_ROOT, "blender", "session_state.json")

_session_id:    str | None   = None
_session_start: float | None = None
_lock = threading.Lock()


def _init_session() -> tuple[str, float]:
    """Create session ID on first call. Idempotent after that."""
    global _session_id, _session_start
    with _lock:
        if _session_id is None:
            _session_id    = str(uuid.uuid4())[:8]
            _session_start = time.time()
            _persist_session_id(_session_id, _session_start)
    return _session_id, _session_start  # type: ignore[return-value]


def _persist_session_id(sid: str, start: float) -> None:
    try:
        state: dict = {}
        try:
            with open(_SESSION_FILE, encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
        state["current_session_id"]    = sid
        state["current_session_start"] = start
        os.makedirs(os.path.dirname(_SESSION_FILE), exist_ok=True)
        with open(_SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        _log.warning("session_events: could not persist session id: %s", e)


def record_event(event_type: str, **kwargs) -> None:
    """
    Append one event to session_events.jsonl. Fire-and-forget — never raises.

    Common event_type values:
      "session_start"  — server startup
      "turn"           — user message received
      "capability"     — tool/capability executed (name=<cap_name>)
    """
    try:
        sid, _ = _init_session()
        record = {"session_id": sid, "ts": time.time(), "type": event_type, **kwargs}
        os.makedirs(os.path.dirname(_EVENTS_LOG), exist_ok=True)
        with open(_EVENTS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        _log.warning("session_events.record_event failed: %s", e)


def get_session_summary(max_events: int = 30) -> str:
    """
    Return a compact text summary of this session for system-prompt injection.
    Returns empty string when no events recorded yet.
    """
    try:
        sid, start = _init_session()
        events: list[dict] = []
        try:
            with open(_EVENTS_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                        if ev.get("session_id") == sid:
                            events.append(ev)
                    except Exception:
                        pass
        except FileNotFoundError:
            pass

        if not events:
            return ""

        elapsed_min = int((time.time() - start) / 60)
        turns        = [e for e in events if e["type"] == "turn"]
        caps         = [e for e in events if e["type"] == "capability" and e.get("name")]

        parts = [f"Session running {elapsed_min}m, {len(turns)} turn(s)."]
        if caps:
            cap_names = list(dict.fromkeys(c["name"] for c in caps))[:6]
            parts.append(f"Capabilities used: {', '.join(cap_names)}.")

        # Include last few user inputs for recency context (truncated for token budget)
        recent_turns = [e.get("text", "") for e in turns[-3:] if e.get("text")]
        if recent_turns:
            parts.append("Recent: " + " / ".join(f'"{t}"' for t in recent_turns) + ".")

        return " ".join(parts)

    except Exception as e:
        _log.warning("session_events.get_session_summary failed: %s", e)
        return ""
