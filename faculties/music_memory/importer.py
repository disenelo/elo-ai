"""
faculties/music_memory/importer.py — Import dispatcher.

Detects source type and routes to the correct adapter.
Merges imported tracks with the existing library (deduplication by fact.key()).
Runs significance scoring on new/updated tracks.
Logs discoveries to the discovery journal.

Usage:
    from faculties.music_memory.importer import ingest
    new_memories = ingest("~/Downloads/spotify_history.json")
    new_memories = ingest("~/Downloads/soundcloud_likes.csv")
    new_memories = ingest({"title": "Kerala", "artist": "Bonobo", ...})  # manual dict
"""
from __future__ import annotations

import os
from faculties.music_memory.models import MusicMemory


def ingest(source: "str | dict | list", context: str = "") -> list[MusicMemory]:
    """
    Import music data from any supported source.

    Args:
        source  — file path (str), manual dict, or list of dicts
        context — optional description of how/when this was discovered

    Returns:
        List of MusicMemory objects that were new or updated.
    """
    if isinstance(source, (dict, list)):
        return _ingest_manual(source, context)

    path = os.path.expanduser(str(source))
    ext  = os.path.splitext(path)[1].lower()
    name = os.path.basename(path).lower()

    if ext == ".csv":
        return _ingest_soundcloud_csv(path, context)
    elif ext == ".json":
        if "streaming" in name or "streaminghistory" in name:
            return _ingest_spotify_history(path, context)
        elif "library" in name or "yourlibrary" in name:
            return _ingest_spotify_library(path, context)
        elif "playlist" in name:
            return _ingest_spotify_playlist(path, context)
        else:
            return _ingest_soundcloud_json(path, context)
    else:
        raise ValueError(f"Unsupported import format: {ext} — expected .csv or .json")


def _merge_and_score(new_memories: list[MusicMemory], context: str = "") -> list[MusicMemory]:
    """
    Merge imported memories with the existing library.
    Deduplicates by fact.key(). Scores significance. Saves updated records.
    Returns only the new or updated memories.
    """
    from faculties.music_memory import storage, analyser, journal

    existing = storage.load_all()
    updated: list[MusicMemory] = []

    for mem in new_memories:
        key = mem.fact.key()

        if key in existing:
            old = existing[key]
            # Merge: accumulate play counts, union sources
            from dataclasses import replace
            merged_fact = replace(
                old.fact,
                play_count = old.fact.play_count + mem.fact.play_count,
                sources    = list(set(old.fact.sources + mem.fact.sources)),
                discovered_date = old.fact.discovered_date or mem.fact.discovered_date,
            )
            mem = replace(old, fact=merged_fact)
        else:
            # New discovery — log it
            journal.log_discovery(mem.fact, context or mem.fact.discovered_context)

        mem = analyser.score_and_update(mem)
        storage.save(mem)

        # Promote to vault if significant enough
        storage.save_to_vault(mem)

        updated.append(mem)

    return updated


def _ingest_soundcloud_csv(path: str, context: str) -> list[MusicMemory]:
    from faculties.music_memory.importers.soundcloud import from_csv
    raw = from_csv(path)
    return _merge_and_score(raw, context or "SoundCloud export")


def _ingest_soundcloud_json(path: str, context: str) -> list[MusicMemory]:
    from faculties.music_memory.importers.soundcloud import from_json
    raw = from_json(path)
    return _merge_and_score(raw, context or "SoundCloud export")


def _ingest_spotify_history(path: str, context: str) -> list[MusicMemory]:
    from faculties.music_memory.importers.spotify import from_streaming_history
    raw = from_streaming_history(path)
    return _merge_and_score(raw, context or "Spotify streaming history")


def _ingest_spotify_library(path: str, context: str) -> list[MusicMemory]:
    from faculties.music_memory.importers.spotify import from_library
    raw = from_library(path)
    return _merge_and_score(raw, context or "Spotify saved library")


def _ingest_spotify_playlist(path: str, context: str) -> list[MusicMemory]:
    from faculties.music_memory.importers.spotify import from_playlist
    raw = from_playlist(path)
    return _merge_and_score(raw, context or "Spotify playlist")


def _ingest_manual(source: "dict | list", context: str) -> list[MusicMemory]:
    from faculties.music_memory.importers.manual import add_track
    if isinstance(source, dict):
        source = [source]
    raw = [
        add_track(
            title  = item.get("title",  ""),
            artist = item.get("artist", ""),
            source = "manual",
            notes  = item.get("notes",  ""),
            emotion= item.get("emotion","neutral"),
            creative_projects = item.get("creative_projects", []),
        )
        for item in source
        if item.get("title") and item.get("artist")
    ]
    return _merge_and_score(raw, context or "manual entry")
