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
- commit: 65e8d32 (pause/resume/skip/previous + read-back), a3aed42 (app fallback, capability answer), Pause path: `tools/spotify_play.control("pause")` → `spotify_web.pause()` = `PUT /me/player/pause` + `raise_for_status()` (any non-2xx raises; 204 passes). **Then the player state is read back**, and eLo says "Paused." only if Spotify reports `is_playing=false`. Otherwise: "I tried to pause it, but Spotify's still playing."
- test: `pytest tests/ -k spotify` → 13 passed. Pause-while-playing against **live Spotify, not mock**, 2026-10-06:
  - direct: play Four Brothers Soundtrack → "Paused." → state read at +1/+3/+6/+10 s: `paused Somebody to Love` every time;
  - **through the real server**: resume → "Can you pause Spotify" → `"Paused." direct:spotify`; state paused at every 1.5–2 s check for 22 s.
- notes: Not re-run today. Presence was connected, and the last run played music over David's podcast. The 2026-10-06 runs above are the live evidence. Still owed: David seeing "Paused." in his own chatlog (verification rows 2–3). In the capability demo, playback resumed ~3 s after a pause. David confirmed that was him ("It was me outside").
