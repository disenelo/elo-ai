"""
tools/spotify_agent.py — Spotify status + control via macOS AppleScript.

No OAuth, no API key. Uses the Spotify desktop app directly.
Requires Spotify.app to be installed and running.

Returns a one-line context string for the LLM to respond with.
"""
from __future__ import annotations

import re
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

    B3-SPOTIFY-001 (2026-10-06): acts only on a real request. It used to act on
    substrings — "back" → previous track, "stop" → pause, any "play" → resume —
    so "you are playing something right now" would restart David's music.
    Controls go through spotify_play (Web API, player state read back).
    """
    from tools import spotify_play as _sp

    act = _sp.control_for(query)
    if not act and re.match(
        r"^(?:(?:can|could|will|would)\s+you\s+)?(?:please\s+)?(?:play|put\s+on)\s+"
        r"(?:some\s+)?(?:music|something|anything|spotify)\b", query.strip(), re.I,
    ):
        act = "resume"
    if act:
        try:
            return f"SPOTIFY: {_sp.control(act)}"
        except Exception as e:
            return f"SPOTIFY: {act} failed — {e}"

    # status only — no side effects
    track = get_current_track()
    if track:
        return f"SPOTIFY: {track}"
    return "SPOTIFY: nothing playing (eLo can open Spotify and start anything David names)"


# ── intent gates (WO-020) ─────────────────────────────────────────────────────
# Pure, deterministic classifiers used by tools/tool_router.py to decide whether
# a "play …" request is a playlist request or a search-and-play of a named thing
# (song / artist / podcast / episode / album / title). No network, no side effects.

# A verb that indicates the user wants playback to start of a *named* thing.
_PLAY_VERB = r"(?:play|put\s+on)"

# Generic / control targets that the plain `agent()` play path already handles —
# these are NOT a "search for a specific named thing" request.
_GENERIC_TARGET = re.compile(
    r"^(?:some\s+|a\s+|an\s+|the\s+)?"
    r"(?:music|song|songs|track|tracks|tune|tunes|something|anything|"
    r"it|that|this|again|more|next|previous|nothing)\s*$"
)


def is_playlist_intent(text: str) -> bool:
    """True when the user asks to play/start/shuffle/queue a playlist.

    e.g. "play my workout playlist", "put on the focus playlist",
    "shuffle my liked playlist". Deterministic, no side effects.
    """
    t = (text or "").lower()
    if not re.search(r"\b(?:play|put\s+on|start|shuffle|queue|resume)\b", t):
        return False
    return re.search(r"\bplaylist\b", t) is not None


def is_search_play_intent(text: str) -> bool:
    """True when the user asks to play/put on a *specific named thing*
    (song, artist, podcast, episode, album, title).

    e.g. "play the Joe Budden Podcast", "play Nights by Frank Ocean",
    "put on Fela Kuti".

    Returns False for playlist requests (see is_playlist_intent) and for bare /
    generic playback controls ("play", "play music", "play something",
    "play that", "pause", "skip", "what's playing"). Deterministic, no side
    effects.
    """
    t = (text or "").lower().strip()
    if not t:
        return False
    if is_playlist_intent(t):
        return False
    m = re.search(r"\b" + _PLAY_VERB + r"\b\s+(.+)", t)
    if not m:
        return False
    target = m.group(1).strip(" ?.!,")
    if not target:
        return False
    if _GENERIC_TARGET.match(target):
        return False
    return True
