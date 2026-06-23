"""
tools/spotify_agent.py — Spotify status + control via macOS AppleScript.

No OAuth, no API key. Uses the Spotify desktop app directly.
Requires Spotify.app to be installed and running.

Returns a one-line context string for the LLM to respond with.
"""
from __future__ import annotations

import subprocess


def _run_applescript(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5.0,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _spotify_running() -> bool:
    out = _run_applescript('tell application "System Events" to (name of processes) contains "Spotify"')
    return out.lower() == "true"


def get_current_track() -> str | None:
    """Return 'Artist — Track' or None if nothing playing."""
    if not _spotify_running():
        return None
    track  = _run_applescript('tell application "Spotify" to get name of current track')
    artist = _run_applescript('tell application "Spotify" to get artist of current track')
    state  = _run_applescript('tell application "Spotify" to get player state')
    if not track:
        return None
    status = "playing" if state == "playing" else "paused"
    return f"{artist} — {track} ({status})"


def control(action: str) -> str:
    """Execute play/pause/next/previous. Returns confirmation string."""
    if not _spotify_running():
        return "Spotify isn't open."
    cmd_map = {
        "play":     'tell application "Spotify" to play',
        "pause":    'tell application "Spotify" to pause',
        "next":     'tell application "Spotify" to next track',
        "previous": 'tell application "Spotify" to previous track',
    }
    script = cmd_map.get(action)
    if not script:
        return "Unknown action."
    _run_applescript(script)
    return action


def agent(query: str) -> str:
    """
    Main entry point for tool_router.
    Returns a single-line context string.
    """
    q = query.lower()

    # control commands
    if any(w in q for w in ["next", "skip"]):
        control("next")
        track = get_current_track()
        return f"SPOTIFY: skipped — now {track or 'nothing playing'}"
    if "previous" in q or "back" in q:
        control("previous")
        track = get_current_track()
        return f"SPOTIFY: went back — now {track or 'nothing playing'}"
    if "pause" in q or "stop" in q:
        control("pause")
        return "SPOTIFY: paused"
    if "play" in q and "what" not in q:
        control("play")
        track = get_current_track()
        return f"SPOTIFY: playing — {track or 'nothing found'}"

    # status queries
    track = get_current_track()
    if track:
        return f"SPOTIFY: {track}"
    return "SPOTIFY: nothing playing (Spotify may not be open)"
