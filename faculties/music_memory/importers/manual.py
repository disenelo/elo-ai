"""
faculties/music_memory/importers/manual.py — Manual music memory entry.

Used when David tells eLo directly about a track:
    "Bonobo - Kerala is connected to the Disenelo clothing project"
    "Add Massive Attack - Teardrop — it's important to me, calm energy"
    "I discovered Jon Hopkins through a late night SoundCloud session in 2019"

Returns a MusicMemory ready for analyser.score_and_update() and storage.save().
"""
from __future__ import annotations

from faculties.music_memory.models import MusicFact, MusicInterpretation, MusicMemory


def add_track(
    title:            str,
    artist:           str,
    *,
    source:           str                = "manual",
    emotion:          str                = "neutral",
    notes:            str                = "",
    creative_projects: list[str]         = None,
    life_period:      str | None         = None,
    mood_tags:        list[str]          = None,
    memories:         list[str]          = None,
    play_count:       int                = 1,
    discovered_date:  str | None         = None,
    discovered_context: str              = "",
    album:            str | None         = None,
    genres:           list[str]          = None,
) -> MusicMemory:
    """
    Create a MusicMemory from a manual entry.
    Significance is set to 0.0 — call analyser.score_and_update() after adding notes.
    """
    fact = MusicFact(
        title             = title.strip(),
        artist            = artist.strip(),
        sources           = [source],
        play_count        = play_count,
        album             = album,
        genres            = genres or [],
        discovered_date   = discovered_date,
        discovered_context= discovered_context or source,
    )
    interp = MusicInterpretation(
        emotion           = emotion,
        notes             = notes,
        creative_projects = creative_projects or [],
        life_period       = life_period,
        mood_tags         = mood_tags or [],
        memories          = memories or [],
    )
    return MusicMemory(fact=fact, interpretation=interp)


def from_conversation(text: str) -> MusicMemory | None:
    """
    Attempt to parse a music mention from a natural language message.
    Looks for 'Artist - Title' or 'Artist — Title' patterns.
    Returns None if no pattern is found (caller should handle gracefully).

    Used by the Music Memory Faculty when eLo detects a music reference in
    conversation — creates a candidate memory for the user to annotate.
    """
    import re
    # Patterns: "Bonobo - Kerala", "Massive Attack — Teardrop", "Bicep – Glue"
    m = re.search(
        r'([A-Z][^\-–—]+?)\s*[-–—]\s*([A-Z][^\.,\n]+)',
        text,
        re.UNICODE,
    )
    if not m:
        return None

    artist = m.group(1).strip()
    title  = m.group(2).strip().rstrip(".,;!?")

    return add_track(
        title  = title,
        artist = artist,
        source = "conversation",
        discovered_context = "mentioned in conversation",
    )
