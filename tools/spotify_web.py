"""
tools/spotify_web.py — Spotify Web API layer for eLo OS.

Requires in .env (run tools/spotify_auth.py once to set up):
    SPOTIFY_CLIENT_ID=...
    SPOTIFY_CLIENT_SECRET=...
    SPOTIFY_REFRESH_TOKEN=...
    SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback  (optional)

All calls go through _get_access_token() which caches the token for 58 min —
each user command makes one HTTP round-trip, not two.
"""
from __future__ import annotations

import os
import time
import httpx

_API = "https://api.spotify.com/v1"


# ── credentials (read at call time — .env loaded by server before this runs) ──
def _creds() -> tuple[str, str, str]:
    return (
        os.environ.get("SPOTIFY_CLIENT_ID",     "").strip(),
        os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip(),
        os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip(),
    )


def is_available() -> bool:
    cid, sec, tok = _creds()
    return bool(cid and sec and tok)


# ── token cache (valid for expires_in - 60 s, typically ~58 min) ──────────────
_token_cache: dict = {"token": "", "expires_at": 0.0}


def _get_access_token() -> str:
    if time.time() < _token_cache["expires_at"] and _token_cache["token"]:
        return _token_cache["token"]
    cid, sec, refresh = _creds()
    resp = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type":    "refresh_token",
            "refresh_token": refresh,
            "client_id":     cid,
            "client_secret": sec,
        },
        timeout=8.0,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"]      = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600) - 60
    # Spotify may rotate the refresh token — persist it if a new one arrives
    if data.get("refresh_token"):
        os.environ["SPOTIFY_REFRESH_TOKEN"] = data["refresh_token"]
    return _token_cache["token"]


def _h() -> dict:
    return {"Authorization": f"Bearer {_get_access_token()}"}


# ── rate-limit-aware request helpers (single retry on 429 with Retry-After) ───
def _get(url: str, **kw) -> httpx.Response:
    r = httpx.get(url, **kw)
    if r.status_code == 429:
        time.sleep(int(r.headers.get("Retry-After", "2")))
        r = httpx.get(url, **kw)
    return r


def _post(url: str, **kw) -> httpx.Response:
    r = httpx.post(url, **kw)
    if r.status_code == 429:
        time.sleep(int(r.headers.get("Retry-After", "2")))
        r = httpx.post(url, **kw)
    return r


def _put(url: str, **kw) -> httpx.Response:
    r = httpx.put(url, **kw)
    if r.status_code == 429:
        time.sleep(int(r.headers.get("Retry-After", "2")))
        r = httpx.put(url, **kw)
    return r


# ── track search ───────────────────────────────────────────────────────────────

def search_track(query: str) -> dict:
    """Search for a track. Returns {name, artist, uri}."""
    resp = _get(
        f"{_API}/search",
        headers=_h(),
        params={"q": query, "type": "track", "limit": 1},
        timeout=8.0,
    )
    resp.raise_for_status()
    items = resp.json()["tracks"]["items"]
    if not items:
        raise ValueError(f"No track found for: {query}")
    t = items[0]
    return {"name": t["name"], "artist": t["artists"][0]["name"], "uri": t["uri"]}


# ── playlists ──────────────────────────────────────────────────────────────────

def get_playlists() -> list[dict]:
    """Return user's playlists as [{name, id}]."""
    resp = _get(
        f"{_API}/me/playlists",
        headers=_h(),
        params={"limit": 50},
        timeout=8.0,
    )
    resp.raise_for_status()
    return [{"name": p["name"], "id": p["id"]} for p in resp.json()["items"] if p]


def find_playlist(name: str) -> dict:
    """Find a playlist by name (fuzzy). Returns {name, id}."""
    playlists = get_playlists()
    nl = name.lower().strip()
    for p in playlists:
        if p["name"].lower() == nl:
            return p
    for p in playlists:
        if nl in p["name"].lower() or p["name"].lower() in nl:
            return p
    names = ", ".join(p["name"] for p in playlists[:8])
    raise ValueError(f"No playlist named '{name}'. Your playlists: {names}")


def add_to_playlist(playlist_id: str, track_uri: str) -> None:
    resp = _post(
        f"{_API}/playlists/{playlist_id}/tracks",
        headers=_h(),
        json={"uris": [track_uri]},
        timeout=8.0,
    )
    resp.raise_for_status()


# ── liked songs ────────────────────────────────────────────────────────────────

def like_track(track_uri: str) -> None:
    track_id = track_uri.split(":")[-1]
    resp = _put(
        f"{_API}/me/tracks",
        headers=_h(),
        json={"ids": [track_id]},
        timeout=8.0,
    )
    resp.raise_for_status()


# ── playback ───────────────────────────────────────────────────────────────────

def play_uri(track_uri: str) -> None:
    """Start playback of a specific URI on the active device."""
    resp = _put(
        f"{_API}/me/player/play",
        headers=_h(),
        json={"uris": [track_uri]},
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise ValueError(f"Playback failed ({resp.status_code}): {resp.text[:200]}")


def get_current_track_uri() -> str | None:
    """Get the current track URI via Web API (more reliable than AppleScript for URIs)."""
    resp = _get(
        f"{_API}/me/player/currently-playing",
        headers=_h(),
        timeout=8.0,
    )
    if resp.status_code == 204 or not resp.text:
        return None
    data = resp.json()
    item = data.get("item")
    return item["uri"] if item else None


def now_playing_full() -> dict | None:
    """Rich now-playing data for the Unity widget. Returns None if nothing is playing."""
    resp = _get(
        f"{_API}/me/player/currently-playing",
        headers=_h(),
        timeout=8.0,
    )
    if resp.status_code == 204 or not resp.text:
        return None
    data = resp.json()
    item = data.get("item")
    if not item:
        return None
    images = item.get("album", {}).get("images", [])
    art = images[0]["url"] if images else ""
    return {
        "track":       item["name"],
        "artist":      ", ".join(a["name"] for a in item["artists"]),
        "album":       item["album"]["name"],
        "album_art":   art,
        "duration_ms": item["duration_ms"],
        "progress_ms": data.get("progress_ms", 0),
        "is_playing":  data.get("is_playing", False),
        "uri":         item["uri"],
    }


def skip() -> None:
    """Skip to the next track."""
    _post(f"{_API}/me/player/next", headers=_h(), timeout=8.0).raise_for_status()


def previous() -> None:
    """Go back to the previous track."""
    _post(f"{_API}/me/player/previous", headers=_h(), timeout=8.0).raise_for_status()


def pause() -> None:
    """Pause playback."""
    _put(f"{_API}/me/player/pause", headers=_h(), timeout=8.0).raise_for_status()


def resume() -> None:
    """Resume playback."""
    _put(f"{_API}/me/player/play", headers=_h(), timeout=8.0).raise_for_status()
