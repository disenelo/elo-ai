"""
runtime/session_id.py — W2 (card 0040): stable, monotonic, persisted session id.

Contract (card 0040 §W2):
    "One session id per process start, stable for its life, monotonic, stored.
     Not os.getpid(). Not str(time.time()) per call."

Design:
    - Allocated once at module import (= process start). Any importer sees the
      same value for the life of the process — no per-call recomputation.
    - Monotonic across processes: reads the previous id from a persistent
      counter file, and picks max(prev + 1, int(time.time())). Two processes
      started in the same second do not collide; a clock rollback does not
      break monotonicity.
    - Persisted: writes back to self/journals/session_counter.json atomically.
    - Numeric string (>= 10 digits from ~2001 onward): keeps compatibility
      with promote_pass()'s distinct_sessions counting and with the existing
      test_w2_session_id.py isdigit() format check.
    - Silent-safe: any I/O failure falls back to int(time.time()) — a still-
      unique-in-practice value that never breaks the record path.

Acceptance test: tests/test_w2_decision_journal_session_id.py
"""
from __future__ import annotations

import json
import os
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COUNTER_PATH = os.path.join(_ROOT, "self", "journals", "session_counter.json")


def _allocate() -> str:
    """Compute this process's session id — called once at import time."""
    now = int(time.time())
    try:
        with open(_COUNTER_PATH, encoding="utf-8") as f:
            prev = int(json.load(f).get("last_id", 0))
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError):
        prev = 0
    new_id = max(prev + 1, now)
    try:
        os.makedirs(os.path.dirname(_COUNTER_PATH), exist_ok=True)
        tmp = _COUNTER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"last_id": new_id, "allocated_at": now}, f)
        os.replace(tmp, _COUNTER_PATH)
    except OSError:
        pass
    return str(new_id)


SESSION_ID: str = _allocate()
