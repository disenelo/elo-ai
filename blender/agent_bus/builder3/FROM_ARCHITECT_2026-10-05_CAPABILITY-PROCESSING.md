# Builder 3 — Capability Processing: Wire world capabilities end-to-end (2026-10-05)
**From:** Board / Lead Architect
**To:** Builder 3
**Date:** 2026-10-05
**Priority:** P0 — Kickstarter critical
**Authority:** David L3 — "capabilities to be processed maybe Builder 3 can sort that"
**Source:** Live session 2026-10-05 — David tried multiple world capabilities, none fired correctly

---

## The pattern — same problem across all capabilities

The tools are built. The credentials are in `.env`. The capability registry has the entries. The intent engine detects the right intents. The capability faculty scores the candidates. The Executive is supposed to decide.

The gap: **execution dispatch from Executive decision → actual tool call is broken or missing** for every world capability David tried.

---

## Capability 1 — Websearch (already in B3-SEARCH-001 brief)

Already dispatched separately. See `FROM_ARCHITECT_2026-10-05_WEBSEARCH-WIRE.md`.

Short version: `tools/web_search.py` exists, `SERPAPI_KEY` in `.env`, `dispatch_web_research()` in `capability_registry.py`. Not called from `spine.py`. Add the wire.

---

## Capability 2 — Spotify

### What David asked for (verbatim from session):
- "Can you open spotify for me?"
- "Can you start Jitwam Radio Playlist in spotify?"
- "List me a few [playlists] and choose one"
- "Can you play Four Brothers Soundtrack in Spotify"

### What exists:

| Component | Status |
|---|---|
| `SPOTIFY_CLIENT_ID` in `.env` | EXISTS |
| `SPOTIFY_CLIENT_SECRET` in `.env` | EXISTS |
| `SPOTIFY_REFRESH_TOKEN` in `.env` | EXISTS — already authorised |
| `tools/spotify_web.py` — `find_playlist(name)`, `get_playlists()`, `play_uri()`, `search_track()` | EXISTS |
| `tools/spotify_agent.py` — AppleScript control (play/pause/next/skip) | EXISTS |
| `capabilities/media_agent.py` — Now Playing via osascript | EXISTS |
| `intent_engine.py` — `utility_spotify` intent | EXISTS |
| `runtime/capabilities/registry.py` — Spotify capability registered | EXISTS |

### What's missing:

The execution dispatch. When `utility_spotify` is detected and Executive selects the Spotify capability, nothing calls `spotify_web.py` or `spotify_agent.py`. The turn falls through to the LLM.

### Wire to add:

```
When intent = utility_spotify OR capability_hint = utility_spotify:

1. "open spotify" → osascript open Spotify.app → eLo: "Opening Spotify"
   (spotify_agent already has this — check if it's being called)

2. "start [playlist name]" / "play [playlist name]" → 
   from tools.spotify_web import find_playlist, play_uri
   playlist = find_playlist(playlist_name_from_query)
   play_uri(playlist['id'])
   eLo: "Playing [playlist name]"

3. "list my playlists" / "what playlists do I have" →
   from tools.spotify_web import get_playlists
   playlists = get_playlists()
   eLo: names the top 5, offers to play one

4. "play [track] by [artist]" / "play [soundtrack]" →
   from tools.spotify_web import search_track, play_uri
   track = search_track(query)
   play_uri(track['uri'])
   eLo: "Playing [track] by [artist]"
```

### Playlist name extraction:
Query "start Jitwam Radio Playlist in spotify" → extract "Jitwam Radio". Use fuzzy match — `find_playlist()` already does this. Pass the extracted name.

---

## Capability 3 — General capability execution path

The broader problem: `_capability_faculty()` returns scored candidates. The Executive is supposed to pick one and dispatch it. Find where in `spine.py` or `backend_router.py` the Executive's capability decision is supposed to trigger an actual tool call. Trace:

```
Executive decides → capability selected → ??? → tool call → result → eLo response
```

The `???` is what's missing. Once you find where this dispatch should happen, add the handlers for each world capability David uses.

---

## Evidence required

Three separate turns:
1. "Open Spotify" → Spotify opens, eLo confirms
2. "Play Jitwam Radio Playlist" → playlist starts, eLo confirms with track name
3. "List my playlists" → eLo names 3-5 actual playlists from David's account

All using real Spotify API via `spotify_web.py` with the `.env` credentials.
