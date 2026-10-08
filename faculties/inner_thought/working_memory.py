"""
faculties/inner_thought/working_memory.py — card 0010A: what eLo has been
doing, answered by lookup rather than by asking a model.

    "What am I working on?" is currently answered by LLM generation. It
    should be answered by state lookup. The kernel doesn't need to ask a
    model to reinterpret something eLo already knows.
    [SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08 §Tier 1]

NOT THE SAME THING as runtime/working_memory.py, and the name collision is
worth stating plainly because the two will otherwise be merged by someone in
good faith:

    runtime/working_memory.py    cognitive FRAMES, goals, attention
                                 competition, rolling summary. What eLo is
                                 holding in mind during a turn. Wired into
                                 server.py and grounding.
    this module                  an EVENT LOG. What happened, in order, with
                                 a source and an authority. "09:31 opened
                                 Blender. 09:34 imported eLo model."

One is a mind's contents; the other is a timeline. Merging them would lose
the authority field, which is the part that makes this answerable without a
model.

AUTHORITY IS THE POINT. Every event records where it came from and how much
weight it carries — `definitive` (the OS says the app opened), `recorded`
(eLo logged it happening), `inference` (something concluded it). A timeline
that cannot say which is which is no better than generation, because the
reader has to guess anyway.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Iterable, Mapping

_log = logging.getLogger("elo.working_memory")

# Spec says 10-30. 30 is the upper bound it allows: a timeline short enough to
# read in a prompt and long enough to cover a working session.
MAX_EVENTS: int = 30

AUTHORITY_DEFINITIVE = "definitive"
AUTHORITY_RECORDED = "recorded"
AUTHORITY_INFERENCE = "inference"

_AUTHORITIES = (AUTHORITY_DEFINITIVE, AUTHORITY_RECORDED, AUTHORITY_INFERENCE)

# The event types the spec names, plus the ones already flowing in this
# system. An unknown type is kept rather than dropped — a timeline that
# silently discards what it does not recognise is worse than one carrying an
# odd row.
PROJECT_TYPES = ("TASK_CHANGED", "PROJECT_SET")


class WorkingMemory:
    """A bounded, ordered record of what has happened. Thread-safe."""

    def __init__(self, max_events: int = MAX_EVENTS):
        self._events: list[dict] = []
        self._max = max(1, int(max_events))
        self._lock = threading.Lock()

    # ── writing ──────────────────────────────────────────────────────────
    def add_event(self, event: Mapping[str, Any]) -> dict | None:
        """
        Record one event. Returns the stored row, or None if unusable.

        Never raises: losing an event must not cost the thing that produced
        it.
        """
        if not isinstance(event, Mapping):
            return None
        etype = str(event.get("type", "") or "").strip()
        if not etype:
            return None

        row = {
            "timestamp": float(event.get("timestamp") or time.time()),
            "type": etype,
            "content": event.get("content", ""),
            "source": str(event.get("source", "") or "elo"),
            # Defaults to `recorded`, never to `definitive`. Claiming more
            # authority than the writer stated is the failure this field
            # exists to prevent.
            "authority": (str(event.get("authority", "") or AUTHORITY_RECORDED)
                          if str(event.get("authority", "")) in _AUTHORITIES
                          else AUTHORITY_RECORDED),
        }
        with self._lock:
            self._events.append(row)
            if len(self._events) > self._max:
                self._events = self._events[-self._max:]
        return row

    # ── reading ──────────────────────────────────────────────────────────
    def recent_events(self, n: int = 10) -> list[dict]:
        """Last n events, newest first."""
        with self._lock:
            return list(reversed(self._events[-max(0, int(n)):]))

    def all_events(self) -> list[dict]:
        with self._lock:
            return list(self._events)

    def query(self, query: str) -> list[dict]:
        """
        Keyword or type filter, newest first.

        Deliberately not fuzzy. This tier exists so an answer can be given
        WITHOUT a model; a clever matcher here would reintroduce the guessing
        it replaces.
        """
        q = str(query or "").strip().lower()
        if not q:
            return []
        out = []
        for e in reversed(self.all_events()):
            if (q in str(e.get("type", "")).lower()
                    or q in str(e.get("content", "")).lower()
                    or q in str(e.get("source", "")).lower()):
                out.append(e)
        return out

    def current_project(self) -> dict | None:
        """The most recent TASK_CHANGED or PROJECT_SET, or None."""
        for e in reversed(self.all_events()):
            if str(e.get("type", "")) in PROJECT_TYPES:
                return e
        return None

    def freshness_s(self, event: Mapping[str, Any]) -> float:
        """Seconds since it happened. The spec's freshness measure."""
        try:
            return max(0.0, time.time() - float(event.get("timestamp", 0.0)))
        except (TypeError, ValueError):
            return 0.0

    def as_context(self, n: int = 10) -> str:
        """
        The STATE-tier string. Empty when nothing has happened — which is an
        honest answer, and better than a line saying so.
        """
        rows = self.recent_events(n)
        if not rows:
            return ""
        lines = ["[WORKING MEMORY — what has just happened, recorded not inferred]"]
        for e in reversed(rows):            # oldest first reads as a timeline
            when = time.strftime("%H:%M", time.localtime(e["timestamp"]))
            content = str(e.get("content", "") or e.get("type", ""))
            mark = "" if e["authority"] == AUTHORITY_DEFINITIVE else f" ({e['authority']})"
            lines.append(f"{when} {content}{mark}")
        proj = self.current_project()
        if proj:
            lines.append(f"Current: {proj.get('content', '') or proj.get('type')}")
        return "\n".join(lines)

    def clear(self) -> None:
        with self._lock:
            self._events = []


# ── Process-wide instance ────────────────────────────────────────────────────
# One timeline per eLo, like the stores it sits beside. Accessed through a
# function so a test can swap it without reaching into module state.

_INSTANCE = WorkingMemory()


def get_working_memory() -> WorkingMemory:
    return _INSTANCE


def add_event(event: Mapping[str, Any]) -> dict | None:
    return _INSTANCE.add_event(event)


def as_context(n: int = 10) -> str:
    return _INSTANCE.as_context(n)


def current_project() -> dict | None:
    return _INSTANCE.current_project()


def recent_events(n: int = 10) -> list[dict]:
    return _INSTANCE.recent_events(n)


def query(q: str) -> list[dict]:
    return _INSTANCE.query(q)
