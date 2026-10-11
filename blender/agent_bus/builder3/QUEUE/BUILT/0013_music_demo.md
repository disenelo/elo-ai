# WO-B3-0013 — Music: Spotify Demo Ready
**Seat:** Builder 3  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## What

eLo plays music on natural language request. "Play something chill", "put on jazz", "play some reggae" → Spotify plays.

## How

- Verify `tools/spotify_agent.py` is live and responds to natural language music requests
- Fix any routing issues (spec to Builder 1 if routing needs changing)
- Known bugs (from START_HERE): pause routing, capability denial while playing, "Got it" with no action — fix all three
- eLo's acknowledgement: "Sure, putting on some jazz" → [Spotify plays] — not silent

## Acceptance

Board tests: 3 different natural music requests. All must result in music playing. No capability denial. No silent "Got it".

---
## Builder 3 (interactive) 2026-10-11: BUILT
- 62a577b (seat) + **f2854a0 (genres)**: the Board's live test #2 "put on jazz" was NOT recognised after 62a577b; fixed: genre requests (jazz/reggae/chill/lo-fi/house/…) → play(genre).
- Live-turn gate (David): "play me some music", "put on jazz", "pause the music".
