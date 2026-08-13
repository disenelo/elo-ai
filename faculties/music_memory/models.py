"""
faculties/music_memory/models.py — Core data structures for Music Memory Faculty.

Strict separation of facts and interpretations.

FACT   — verifiable. Play count, source, date discovered. Never guessed.
INTERP — candidate meaning. Emotion, projects, life period. Requires evidence.

A MusicMemory is not a memory until significance > 0. It is a candidate.
eLo learns why something matters through repetition, context, and conversation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MusicFact:
    """
    What we know for certain about a track.
    Sourced from platform exports or user confirmation.
    """
    title:              str
    artist:             str
    sources:            list[str]          = field(default_factory=list)
    play_count:         int                = 0
    duration_ms:        int                = 0
    genres:             list[str]          = field(default_factory=list)
    album:              Optional[str]      = None
    discovered_date:    Optional[str]      = None   # ISO date string
    discovered_context: str                = "unknown"

    def key(self) -> str:
        """Canonical deduplication key."""
        return f"{self.artist.lower().strip()}::{self.title.lower().strip()}"


@dataclass
class MusicInterpretation:
    """
    Candidate meaning — requires evidence to solidify into memory.
    Always separated from facts. Never assumed without signal.
    """
    emotion:           str                = "neutral"
    importance:        float              = 0.0       # 0.0 – 1.0
    notes:             str                = ""
    creative_projects: list[str]          = field(default_factory=list)
    life_period:       Optional[str]      = None
    mood_tags:         list[str]          = field(default_factory=list)
    memories:          list[str]          = field(default_factory=list)


@dataclass
class MusicMemory:
    """
    Complete music memory — fact + candidate interpretation + significance.

    significance = 0.0 → candidate only (not yet meaningful)
    significance > 0.5 → eligible for vault write
    significance > 0.8 → high-weight memory (important to eLo's understanding)
    """
    fact:           MusicFact
    interpretation: MusicInterpretation  = field(default_factory=MusicInterpretation)
    significance:   float                = 0.0
    last_updated:   str                  = ""

    def to_dict(self) -> dict:
        f = self.fact
        i = self.interpretation
        return {
            "title":   f.title,
            "artist":  f.artist,
            "sources": f.sources,
            "album":   f.album,
            "genres":  f.genres,
            "play_count":         f.play_count,
            "duration_ms":        f.duration_ms,
            "discovered": {
                "date":    f.discovered_date,
                "context": f.discovered_context,
            },
            "memory": {
                "emotion":           i.emotion,
                "importance":        i.importance,
                "notes":             i.notes,
                "creative_projects": i.creative_projects,
                "life_period":       i.life_period,
                "mood_tags":         i.mood_tags,
                "memories":          i.memories,
            },
            "significance": self.significance,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MusicMemory":
        disc = data.get("discovered", {})
        mem  = data.get("memory",     {})
        fact = MusicFact(
            title             = data.get("title",       ""),
            artist            = data.get("artist",      ""),
            sources           = data.get("sources",     []),
            album             = data.get("album"),
            genres            = data.get("genres",      []),
            play_count        = data.get("play_count",  0),
            duration_ms       = data.get("duration_ms", 0),
            discovered_date   = disc.get("date"),
            discovered_context= disc.get("context", "unknown"),
        )
        interp = MusicInterpretation(
            emotion           = mem.get("emotion",           "neutral"),
            importance        = mem.get("importance",        0.0),
            notes             = mem.get("notes",             ""),
            creative_projects = mem.get("creative_projects", []),
            life_period       = mem.get("life_period"),
            mood_tags         = mem.get("mood_tags",         []),
            memories          = mem.get("memories",          []),
        )
        return cls(
            fact          = fact,
            interpretation= interp,
            significance  = data.get("significance", 0.0),
            last_updated  = data.get("last_updated",  ""),
        )


@dataclass
class MusicObservation:
    """
    What the Music Memory Faculty reports to the Executive.

    The Executive decides whether this becomes conversation, journal,
    creative suggestion, or nothing. The Faculty never decides.
    """
    trigger:          str           = ""        # what prompted this observation
    patterns:         list[str]     = field(default_factory=list)
    significant_tracks: list[MusicMemory] = field(default_factory=list)
    recent_discoveries: list[MusicMemory] = field(default_factory=list)
    observation_text: str           = ""        # plain-language summary for Executive
    has_signal:       bool          = False     # True if something worth surfacing
