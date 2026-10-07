**WO:** B3-SPOTIFY-PAUSE · **Seat:** builder3 · **Priority:** P1
**Reserved?** no

## Goal
B3-SPOTIFY-001 outbox (2026-10-06) reports pause-while-playing as NOT_DONE — it needs a test window. Commit 65e8d32 built pause/resume/skip/previous. This card closes the gap: confirm pause works while a track is actively playing.

## Scope
1. Start Spotify playing a track
2. Call eLo's pause command
3. Confirm Spotify pauses (not just that the API call was made — confirm state)
4. `tools/spotify_web.py` — read current pause implementation, confirm it uses `PUT /me/player/pause` with a 204 response check
5. Run the Spotify test suite

## Test command
`python3 -m pytest tests/ -k "spotify" -v`

## Done when
Pause confirmed working against live Spotify (not mock) + test green + committed. Close the NOT_DONE in outbox.json.

## Result
- commit:
- test:
- notes:
