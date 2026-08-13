"""
faculties/music_memory/importers/spotify.py — Spotify data adapter.

Converts Spotify streaming history / library exports into MusicMemory models.

Spotify data export (spotify.com/account/privacy → Request your data):
    StreamingHistory*.json   — listening history (msPlayed, trackName, artistName)
    YourLibrary.json         — saved tracks, albums, artists
    Playlist*.json           — playlist contents

All files are read-only. Source data is never modified.

Play count is approximated from streaming history:
    A track appears N times in StreamingHistory = play_count N.
    Tracks with msPlayed < 30s are counted as skips, not plays.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime
from typing import Any

from faculties.music_memory.models import MusicFact, MusicMemory

_MIN_PLAY_MS = 30_000   # streams shorter than 30s are skips


def from_streaming_history(path: str) -> list[MusicMemory]:
    """
    Import from a Spotify StreamingHistory*.json file.
    Groups streams by artist+track, counts plays, finds first listen date.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Spotify streaming history not found: {path}")

    with open(path, encoding="utf-8") as f:
        streams = json.load(f)

    # Group by (artistName, trackName) — count plays, find earliest date
    plays:    dict[tuple, int]  = Counter()
    dates:    dict[tuple, str]  = {}
    ms_total: dict[tuple, int]  = {}

    for s in streams:
        artist = (s.get("artistName") or s.get("master_metadata_album_artist_name") or "").strip()
        track  = (s.get("trackName")  or s.get("master_metadata_track_name")        or "").strip()
        ms     = int(s.get("msPlayed") or s.get("ms_played") or 0)
        ts     = s.get("endTime") or s.get("ts") or ""

        if not artist or not track:
            continue
        if ms < _MIN_PLAY_MS:
            continue

        key = (artist, track)
        plays[key]    += 1
        ms_total[key]  = ms_total.get(key, 0) + ms

        if ts:
            date_str = ts[:10]
            if key not in dates or date_str < dates[key]:
                dates[key] = date_str

    memories: list[MusicMemory] = []
    for (artist, track), play_count in plays.most_common():
        fact = MusicFact(
            title             = track,
            artist            = artist,
            sources           = ["Spotify"],
            play_count        = play_count,
            duration_ms       = ms_total.get((artist, track), 0) // max(play_count, 1),
            discovered_date   = dates.get((artist, track)),
            discovered_context= "Spotify streaming history",
        )
        memories.append(MusicMemory(fact=fact))

    return memories


def from_library(path: str) -> list[MusicMemory]:
    """
    Import from Spotify YourLibrary.json (saved tracks).
    Saved = minimum 1 play. No streaming history available here.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Spotify library not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    tracks = data.get("tracks", [])
    memories: list[MusicMemory] = []

    for item in tracks:
        artist = item.get("artist", "").strip()
        track  = item.get("track",  "").strip()
        album  = item.get("album",  "").strip() or None

        if not artist or not track:
            continue

        fact = MusicFact(
            title             = track,
            artist            = artist,
            album             = album,
            sources           = ["Spotify"],
            play_count        = 1,
            discovered_context= "Spotify library (saved)",
        )
        memories.append(MusicMemory(fact=fact))

    return memories


def from_playlist(path: str, playlist_name: str = "") -> list[MusicMemory]:
    """
    Import tracks from a Spotify Playlist*.json.
    Playlist name is attached as discovered_context.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Spotify playlist not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    pl_name = playlist_name or data.get("name", "Spotify playlist")
    items   = data.get("items", [])
    memories: list[MusicMemory] = []

    for item in items:
        track_data = item.get("track", item)
        artist = track_data.get("artistName", track_data.get("artist", "")).strip()
        title  = track_data.get("trackName",  track_data.get("track",  "")).strip()
        album  = track_data.get("albumName",  track_data.get("album",  "")).strip() or None

        if not artist or not title:
            continue

        fact = MusicFact(
            title             = title,
            artist            = artist,
            album             = album,
            sources           = ["Spotify"],
            play_count        = 1,
            discovered_context= f"Spotify playlist: {pl_name}",
        )
        memories.append(MusicMemory(fact=fact))

    return memories
