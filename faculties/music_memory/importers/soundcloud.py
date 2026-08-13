"""
faculties/music_memory/importers/soundcloud.py — SoundCloud data adapter.

Converts SoundCloud likes/saves export into MusicMemory models.

SoundCloud data export (soundcloud.com/settings → Privacy → Download data)
provides:
    likes.csv     — title, URL, created_at
    reposts.csv   — same format

If a SoundCloud API token is available, richer metadata (artist, genre,
duration) is fetched per track. Without it, artist is parsed from title
(many SoundCloud titles follow "Artist - Title" convention).

Safety: never modifies the source export files. Read-only.
"""
from __future__ import annotations

import csv
import json
import os
import re
from typing import Any

from faculties.music_memory.models import MusicFact, MusicInterpretation, MusicMemory


def _parse_artist_title(raw_title: str) -> tuple[str, str]:
    """
    Attempt to split 'Artist - Title' or 'Artist – Title' into components.
    Falls back to (raw_title, raw_title) if no separator found.
    """
    for sep in (" - ", " – ", " — ", " | "):
        if sep in raw_title:
            parts = raw_title.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    return raw_title.strip(), raw_title.strip()


def from_csv(path: str) -> list[MusicMemory]:
    """
    Import from a SoundCloud likes/reposts CSV export.
    Expected columns: Title, URL, Created At (order may vary; header-matched).
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"SoundCloud export not found: {path}")

    memories: list[MusicMemory] = []

    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_title   = (row.get("Title") or row.get("title") or "").strip()
            created_at  = (row.get("Created At") or row.get("created_at") or "").strip()

            if not raw_title:
                continue

            artist, title = _parse_artist_title(raw_title)

            discovered_date = None
            if created_at:
                try:
                    discovered_date = created_at[:10]
                except Exception:
                    pass

            fact = MusicFact(
                title             = title,
                artist            = artist,
                sources           = ["SoundCloud"],
                play_count        = 1,
                discovered_date   = discovered_date,
                discovered_context= "SoundCloud likes",
            )
            memories.append(MusicMemory(fact=fact))

    return memories


def from_json(path: str) -> list[MusicMemory]:
    """
    Import from a SoundCloud JSON export or API response.
    Expects a list of track objects with 'title', 'user.username',
    'genre', 'duration', 'created_at' fields.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"SoundCloud JSON not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = data.get("tracks", data.get("likes", []))

    memories: list[MusicMemory] = []
    for item in data:
        raw_title = item.get("title", "")
        artist    = (item.get("user") or {}).get("username", "")
        if not artist:
            artist, raw_title = _parse_artist_title(raw_title)

        genre    = item.get("genre", "")
        duration = item.get("duration", 0)
        date_str = (item.get("created_at") or "")[:10] or None

        fact = MusicFact(
            title             = raw_title.strip(),
            artist            = artist.strip(),
            sources           = ["SoundCloud"],
            genres            = [genre] if genre else [],
            duration_ms       = int(duration),
            play_count        = item.get("playback_count", 1),
            discovered_date   = date_str,
            discovered_context= "SoundCloud",
        )
        memories.append(MusicMemory(fact=fact))

    return memories
