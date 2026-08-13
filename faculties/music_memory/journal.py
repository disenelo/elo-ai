"""
faculties/music_memory/journal.py — Music memory journals.

Three append-only journals, each capturing a different layer of music memory:

    listening_journal.json    — what was played, when, how often
    discovery_journal.json    — how music was found (source, context, date)
    inspiration_journal.json  — creative connections (project + notes)

eLo observes patterns across these journals and surfaces them as
MusicObservations for the Executive to act on.

Journal entries are JSON Lines (one JSON object per line, newline-delimited).
Never deleted. Append-only.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from faculties.music_memory.models import MusicFact, MusicMemory

_HERE = os.path.dirname(os.path.abspath(__file__))
_DIR  = os.path.join(_HERE, "journals")

_LISTENING_J    = os.path.join(_DIR, "listening_journal.jsonl")
_DISCOVERY_J    = os.path.join(_DIR, "discovery_journal.jsonl")
_INSPIRATION_J  = os.path.join(_DIR, "inspiration_journal.jsonl")


def _ensure() -> None:
    os.makedirs(_DIR, exist_ok=True)


def _append(path: str, entry: dict) -> None:
    _ensure()
    entry["_ts"] = datetime.now().isoformat(timespec="seconds")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── Listening journal ─────────────────────────────────────────────────────────

def log_listening(fact: MusicFact, play_count_delta: int = 1) -> None:
    """Record a listening event."""
    _append(_LISTENING_J, {
        "artist":      fact.artist,
        "title":       fact.title,
        "source":      fact.sources[0] if fact.sources else "unknown",
        "play_count":  fact.play_count,
        "delta":       play_count_delta,
    })


# ── Discovery journal ─────────────────────────────────────────────────────────

def log_discovery(fact: MusicFact, context: str = "") -> None:
    """Record how a track was found."""
    _append(_DISCOVERY_J, {
        "artist":           fact.artist,
        "title":            fact.title,
        "source":           fact.sources[0] if fact.sources else "unknown",
        "discovered_date":  fact.discovered_date or "unknown",
        "context":          context or fact.discovered_context,
    })


# ── Inspiration journal ───────────────────────────────────────────────────────

def log_inspiration(fact: MusicFact, project: str, notes: str = "") -> None:
    """Record a creative connection between a track and a project."""
    _append(_INSPIRATION_J, {
        "artist":  fact.artist,
        "title":   fact.title,
        "project": project,
        "notes":   notes,
    })


# ── Pattern observations ──────────────────────────────────────────────────────

def recent_listening(n: int = 20) -> list[dict]:
    """Return the last n listening journal entries."""
    return _tail(_LISTENING_J, n)


def recent_discoveries(n: int = 10) -> list[dict]:
    """Return the last n discovery journal entries."""
    return _tail(_DISCOVERY_J, n)


def recent_inspirations(n: int = 10) -> list[dict]:
    """Return the last n inspiration journal entries."""
    return _tail(_INSPIRATION_J, n)


def _tail(path: str, n: int) -> list[dict]:
    if not os.path.exists(path):
        return []
    lines = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return lines[-n:]


def observation_text(memories: list[MusicMemory]) -> str:
    """
    Generate a plain-language observation for the Executive.
    The Executive decides whether this becomes anything. The Faculty only observes.
    """
    if not memories:
        return ""

    artists = list({m.fact.artist for m in memories})
    moods   = [m.interpretation.emotion for m in memories if m.interpretation.emotion != "neutral"]
    projects= list({p for m in memories for p in m.interpretation.creative_projects})

    lines = []
    if artists:
        lines.append(f"Music memory contains {len(memories)} significant track(s) across {len(artists)} artist(s).")
    if moods:
        from collections import Counter
        top_mood = Counter(moods).most_common(1)[0][0]
        lines.append(f"Dominant emotional register: {top_mood}.")
    if projects:
        lines.append(f"Creative connections: {', '.join(projects[:3])}.")

    recent = recent_listening(5)
    if recent:
        recent_artists = list({r["artist"] for r in recent})
        lines.append(f"Recently revisited: {', '.join(recent_artists[:3])}.")

    return " ".join(lines)
