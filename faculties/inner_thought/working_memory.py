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

import json
import logging
import os
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


_STORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "self", "state", "working_memory.json",
)


class WorkingMemory:
    """A bounded, ordered record of what has happened. Thread-safe."""

    def __init__(self, max_events: int = MAX_EVENTS, *, path: str | None = None):
        self._events: list[dict] = []
        self._max = max(1, int(max_events))
        self._lock = threading.Lock()
        # Persisted, because an in-memory timeline cannot answer the question
        # it exists for. The ambient tick records focus in the server process;
        # the STATE tier reads it from wherever it is asked. Those are
        # different processes, and the acceptance suite caught it by reporting
        # an empty timeline while focus had been recorded for hours.
        self._path = _STORE_PATH if path is None else path
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, encoding="utf-8") as f:
                rows = json.load(f)
            if isinstance(rows, list):
                self._events = [r for r in rows if isinstance(r, dict)][-self._max:]
        except Exception:
            self._events = []

    def _save(self) -> None:
        """Atomic. A half-written timeline reads as a truncated session."""
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            tmp = f"{self._path}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._events, f, indent=2)
            os.replace(tmp, self._path)
        except Exception as e:
            _log.debug("working memory not persisted (non-fatal): %s", e)

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
            self._save()
        return row

    # ── reading ──────────────────────────────────────────────────────────
    def recent_events(self, n: int = 10) -> list[dict]:
        """Last n events, newest first. Re-reads — see all_events."""
        with self._lock:
            self._load()
            return list(reversed(self._events[-max(0, int(n)):]))

    def all_events(self) -> list[dict]:
        # Re-read before answering. The writer is usually a different process
        # (the ambient tick) from the reader (the STATE tier), so a cached
        # list would answer with whatever this process happened to see.
        with self._lock:
            self._load()
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
            self._save()


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


# ── Feeder: what David is actually in front of ──────────────────────────────
#
# Card 0010 shipped the timeline with nothing writing to it, and said so. The
# card expected app events from "Designer's event bus if wired" — that bus
# does not exist. But Unity already writes the app name every tick:
#
#     blender/perch_state.json   {"app": "Claude", "edge": "bottom"}
#     blender/motion_state.json  {"window": "Claude", "win_id": 473}
#
# So the signal was there, under a different name, the whole time. Reading it
# makes "what was I doing?" answerable from state instead of from a model,
# which is the point of the STATE tier.
#
# Authority is `definitive`: Unity observed the window. It is not eLo's
# inference about what David is doing — it is what the OS reported.

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PERCH_PATH = os.path.join(_ROOT, "blender", "perch_state.json")
_MOTION_PATH = os.path.join(_ROOT, "blender", "motion_state.json")

# Apps worth nothing as a record. eLo perching on his own window says only
# that eLo exists.
_IGNORED_APPS = frozenset({"", "unknown", "none", "presence", "elo", "desktop"})


def _current_app() -> str:
    """Whatever Unity last reported, or "" if it reported nothing usable."""
    for path, key in ((_PERCH_PATH, "app"), (_MOTION_PATH, "window")):
        try:
            with open(path, encoding="utf-8") as f:
                app = str((json.load(f) or {}).get(key, "") or "").strip()
            if app and app.lower() not in _IGNORED_APPS:
                return app
        except Exception:
            continue
    return ""


def observe_focus(app: str | None = None) -> dict | None:
    """
    Record an app change, if there is one. Returns the event, or None.

    Deduped against the last APP_FOCUSED: a timeline that logs the same app
    every half-second is noise, and the ring buffer would hold thirty
    identical rows instead of a session.
    """
    current = _current_app() if app is None else str(app or "").strip()
    if not current or current.lower() in _IGNORED_APPS:
        return None

    for e in _INSTANCE.recent_events(MAX_EVENTS):
        if e.get("type") == "APP_FOCUSED":
            if str(e.get("content", "")) == current:
                return None
            break

    return _INSTANCE.add_event({
        "type": "APP_FOCUSED",
        "content": current,
        "source": "unity",
        "authority": AUTHORITY_DEFINITIVE,
    })
