#!/usr/bin/env python3
"""
tools/spotify_auth.py — One-time Spotify OAuth setup for eLo OS.

Run once from the elo-ai directory:
    python tools/spotify_auth.py

Steps:
  1. Opens your browser to Spotify's auth page
  2. You log in and authorise — Spotify redirects to 127.0.0.1:8888/callback
  3. Paste the full redirect URL when prompted
  4. Refresh token is saved to .env automatically

Requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET already in .env.
Get them at: https://developer.spotify.com/dashboard
  → Create app → Set redirect URI to: http://127.0.0.1:8888/callback
"""
import os
import sys
import urllib.parse
import webbrowser
import httpx

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

_SCOPES = [
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-modify-playback-state",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-modify",
    "user-library-read",
]


def _load_env() -> None:
    if not os.path.exists(_ENV_PATH):
        print(f"ERROR: .env not found at {_ENV_PATH}")
        sys.exit(1)
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _save_to_env(key: str, value: str) -> None:
    with open(_ENV_PATH) as f:
        lines = f.readlines()
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"\n{key}={value}\n")
    with open(_ENV_PATH, "w") as f:
        f.writelines(new_lines)


def main() -> None:
    _load_env()

    client_id     = os.environ.get("SPOTIFY_CLIENT_ID",     "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    redirect_uri  = os.environ.get("SPOTIFY_REDIRECT_URI",  "http://127.0.0.1:8888/callback")

    if not client_id or not client_secret:
        print("ERROR: Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to .env first.")
        print("       Get them at https://developer.spotify.com/dashboard")
        sys.exit(1)

    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id":     client_id,
        "response_type": "code",
        "redirect_uri":  redirect_uri,
        "scope":         " ".join(_SCOPES),
    })

    print("\n=== Spotify OAuth Setup ===\n")
    print("Opening browser to authorise eLo OS with Spotify...")
    webbrowser.open(auth_url)
    print(f"\nIf the browser didn't open, visit:\n{auth_url}\n")
    print(f"After authorising, Spotify will redirect to:\n{redirect_uri}?code=...\n")

    callback_url = input("Paste the full redirect URL here:\n> ").strip()

    parsed = urllib.parse.urlparse(callback_url)
    qs     = urllib.parse.parse_qs(parsed.query)
    code   = qs.get("code", [None])[0]

    if not code:
        print("ERROR: No auth code found in that URL. Make sure you pasted the full URL after being redirected.")
        sys.exit(1)

    resp = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type":   "authorization_code",
            "code":         code,
            "redirect_uri": redirect_uri,
            "client_id":    client_id,
            "client_secret": client_secret,
        },
        timeout=10.0,
    )

    if resp.status_code != 200:
        print(f"ERROR: Token exchange failed ({resp.status_code}): {resp.text}")
        sys.exit(1)

    data          = resp.json()
    refresh_token = data.get("refresh_token", "")

    if not refresh_token:
        print("ERROR: No refresh token returned. Make sure offline_access scope is set.")
        sys.exit(1)

    _save_to_env("SPOTIFY_REFRESH_TOKEN", refresh_token)
    print(f"\nDone. Refresh token saved to .env")
    print("eLo OS can now add tracks to playlists, like songs, and search Spotify.\n")


if __name__ == "__main__":
    main()
