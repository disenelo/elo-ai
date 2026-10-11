# WO-B3-0014 — Spotify Routing Bug Fix
**Seat:** Builder 3  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## Known bugs (from START_HERE)

1. **Pause routing broken** — "pause" / "stop the music" not routing to Spotify pause correctly
2. **Capability denial while playing** — eLo denies capability while Spotify is actively playing
3. **"Got it" with no action** — eLo acknowledges but nothing plays

All three must be fixed. For routing changes in `spine.py` or `backend_router.py` — spec to Builder 1, do not edit those files yourself.

## Done when

Board tests: play request → music plays. Pause request → music stops. No capability denial while playing. File to Board with test log.

---
## Builder 3 (interactive) 2026-10-11: BUILT (same three bugs as 0013)
- Bug 1 pause routing: works ("pause the music"/"stop the music" → control pause), regression-tested.
- Bug 2 capability denial while playing: capability_status live block + spotify awareness; regression-tested.
- Bug 3 "Got it" with no action: 62a577b + f2854a0 (genres); success comes from Spotify's read-back state, never from sending a command.
- Live test log needs David (Board can't run the live server).
