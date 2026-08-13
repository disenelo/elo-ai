"""
faculties/music_memory/patterns.py — Cross-library pattern analysis.

Discovers patterns across the music memory library. Never modifies memories.
Pure read + analysis. Returns structured observations for the Executive.

Pattern types:
    creative_period   — tracks linked to a specific project or life period
    mood_landscape    — dominant emotional registers across the library
    discovery_arc     — how music discovery evolved over time
    frequent_revisits — tracks the user keeps returning to
    personal_soundtrack — highest significance tracks = the core map
"""
from __future__ import annotations

from collections import Counter
from faculties.music_memory.models import MusicMemory


def creative_period_tracks(
    project_name: str,
    memories: list[MusicMemory],
) -> list[MusicMemory]:
    """Tracks connected to a specific project or life period."""
    p = project_name.lower()
    return sorted(
        [
            m for m in memories
            if any(p in proj.lower() for proj in m.interpretation.creative_projects)
            or (m.interpretation.life_period and p in m.interpretation.life_period.lower())
        ],
        key=lambda m: m.significance,
        reverse=True,
    )


def mood_distribution(memories: list[MusicMemory]) -> dict[str, int]:
    """Count of tracks per emotional register."""
    moods = [m.interpretation.emotion for m in memories if m.interpretation.emotion]
    return dict(Counter(moods).most_common())


def discovery_timeline(memories: list[MusicMemory]) -> list[dict]:
    """
    Return tracks ordered by discovery date.
    Tracks with no date appear at the end, context="unknown".
    """
    dated   = [m for m in memories if m.fact.discovered_date]
    undated = [m for m in memories if not m.fact.discovered_date]

    dated.sort(key=lambda m: m.fact.discovered_date or "")

    result = []
    for m in dated + undated:
        result.append({
            "artist":  m.fact.artist,
            "title":   m.fact.title,
            "date":    m.fact.discovered_date or "unknown",
            "context": m.fact.discovered_context,
            "sig":     m.significance,
        })
    return result


def frequently_revisited(
    memories: list[MusicMemory],
    min_plays: int = 5,
) -> list[MusicMemory]:
    """Tracks the user keeps returning to — raw frequency signal."""
    return sorted(
        [m for m in memories if m.fact.play_count >= min_plays],
        key=lambda m: m.fact.play_count,
        reverse=True,
    )


def personal_soundtrack(memories: list[MusicMemory], top_n: int = 20) -> list[MusicMemory]:
    """The highest significance tracks — the core map of David's music memory."""
    return sorted(memories, key=lambda m: m.significance, reverse=True)[:top_n]


def grounding_tracks(memories: list[MusicMemory]) -> list[MusicMemory]:
    """Tracks associated with calm, reflection, or grounding emotions."""
    _grounding = {"calm", "reflection", "reflective", "grounding", "peaceful", "meditative"}
    return [
        m for m in memories
        if m.interpretation.emotion in _grounding
        or any(t in _grounding for t in m.interpretation.mood_tags)
    ]


def pattern_summary(memories: list[MusicMemory]) -> str:
    """
    Plain-language summary of patterns found.
    Returned to Executive as an observation — Executive decides action.
    """
    if not memories:
        return "Music memory is empty."

    lines = [f"Library: {len(memories)} tracks."]

    sig = personal_soundtrack(memories, top_n=5)
    if sig:
        lines.append(
            "Highest significance: " +
            ", ".join(f"{m.fact.artist} — {m.fact.title}" for m in sig[:3]) + "."
        )

    moods = mood_distribution(memories)
    if moods:
        top = list(moods.items())[:3]
        lines.append("Emotional landscape: " + ", ".join(f"{k} ({v})" for k, v in top) + ".")

    revisited = frequently_revisited(memories, min_plays=10)
    if revisited:
        lines.append(
            f"Frequently revisited: {revisited[0].fact.artist} — {revisited[0].fact.title} "
            f"({revisited[0].fact.play_count} plays)."
        )

    grounding = grounding_tracks(memories)
    if grounding:
        lines.append(f"{len(grounding)} track(s) used as grounding or reflection.")

    return " ".join(lines)
