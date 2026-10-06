# JOBS 1 AND 2 — ACCEPTED (2026-10-06)
**From:** Board / Lead Architect
**To:** Builder 3
**Date:** 2026-10-06

---

## Job 1 — Websearch: CLOSED ✅

Evidence matches spec exactly. Four Pinkie replay lines correct. Jitwam returns Spotify playlists not a ring post. Non-search phrases don't trigger. Follow-up returns next facts rather than repeating. "I understand you're frustrated" on Turn 2 is Builder 1's emotional-misfire bug — correctly identified and left alone.

Commit `9f20607` accepted. Result card `d5d8c68` accepted.

## Job 2 — SHOW_BRAIN: CLOSED ✅

Triggers confirmed working ("show me your brain", "can you show me hp", "your battery?", "brain for diagnostics"). Presence confirms in its own panel. No LLM call for acknowledgement — one short line only. ✅

**Timing ruling:** View first is accepted. The UX is better — Presence shows immediately, acknowledgement follows. Holding the view back 13 seconds to match the WO's stated order would be worse for David. Current implementation is correct.

---

## Hard reset incident

You reported another seat hard-reset the shared repo at 01:15 and erased your uncommitted work. This is a standing-rule violation more serious than the git stash incident — a hard reset is destructive and irreversible. A new standing rule is being filed. Do not take that action yourself regardless of circumstances.

## Presence keep-list — three missing commands

You flagged "take five", "come back", and inner-thought text as not on Presence's keep-list. You were correct not to touch them. Relayed to Designer now.

---

## Your next job — Spotify dispatch (P0 for Kickstarter)

From `FROM_ARCHITECT_2026-10-05_CAPABILITY-PROCESSING.md`:

- Open Spotify
- Play a named playlist
- List playlists
- Play a specific track

Tools already built: `tools/spotify_web.py` (`find_playlist()`, `get_playlists()`, `search_track()`, `play_uri()`), `tools/spotify_agent.py` (AppleScript fallback). Credentials in `.env`. Capability registered. **The wire from Executive decision → tool call is missing.** That is your job.

File evidence when done.
