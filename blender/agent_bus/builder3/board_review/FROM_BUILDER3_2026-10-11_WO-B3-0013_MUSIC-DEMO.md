# TO BOARD — WO-B3-0013 Music demo (Spotify Track C bugs locked)
**Date:** 2026-10-11
**From:** Builder 3
**To:** Board
**Card:** WO-B3-0013 Music — Spotify Demo Ready (P0, demo milestone)
**Commit:** 62a577b

---

## Why this card

Items 1–3 of the demo sprint are blocked on me today:
- 0008 (Alexa tunnel) — needs David to sign up for ngrok + paste authtoken + static domain; interactive, cannot run from here.
- 0010 (Alexa ears + mouth) — depends on 0008.
- 0011 (Company control) — already filed as BUILT 2026-10-11 awaiting a live verification turn from the Board.

0013 was the next doable P0, and the three Track C bugs in START_HERE map
directly onto its acceptance ("No capability denial. No silent 'Got it'.").

---

## What I verified (offline, no live server, no Spotify touched)

I traced each of the three bugs through the real code before writing or
changing anything.

### Bug 1 — pause routing
`tools/spotify_play.control_for()` already covers all natural phrasings I
could think of: "pause spotify", "pause the music", "stop the music", "turn
the music off", "mute spotify", "kill the music", "can you pause spotify",
"stop playing that", bare "pause"/"stop" after context. **No change needed.**
Added 16 parametrised tests to lock it against regression.

### Bug 2 — capability denial while playing
`capability_answer()` returns an affirmative line for "can you control
spotify?" and rotates across three variants so a second identical ask is not
blanked by `elo_response_gate`. **No change needed.** Added 8 cases + a
rotation test.

### Bug 3 — "Got it" with no action (the one that was still open)
`_PLAY_MUSIC_RE` missed common filler phrasings:
- "play me some music"
- "play me something"
- "play me a tune"
- "just play something"
- "can you just play something"
- "please play music"
- "could you play me some music"

When the regex misses, `_handle_line()` returns None, `server.py:2729`
yields no direct line, the LLM is handed the turn and silent-acks ("Got it")
with no Spotify side effect. That is the demo-killer.

**Fix:** extended the regex (one line) to accept:
- `me` between the verb and the generic noun ("play me some music")
- `just`/`please` as leading filler, repeated ("can you just please play music")
- `a`/`the` alongside `some` as the determiner ("play a tune", "play the music")

Simplified `a\s+tune` to `tune` because the determiner is already optional.
Verified 18 positive + 7 negative cases: no change to the behaviour on named
plays ("play jazz", "play Fela Kuti", "play Nights by Frank Ocean") or
mentions ("I love music", "the music made me cry", "pause the music").

---

## What built (Builder 3-owned files only)

**`tools/spotify_play.py`**
- `_PLAY_MUSIC_RE` extended; new comment references the START_HERE Track C
  bug and the handler-return-None path so the next reader can see why the
  fillers are deliberate.
- No other code touched. No change to `control_for()`, `parse()`,
  `capability_answer()`, `execute()`, `handle()`.

**`tests/test_b3_spotify_music_demo.py` (new)**
- 50 cases total, split by bug:
  - 16 pause-routing phrasings → `control_for() == "pause"`
  - 8 ability-question phrasings → `capability_answer()` returns
    affirmative line; separate rotation test proves two consecutive asks
    differ
  - 18 generic-play phrasings → `_PLAY_MUSIC_RE` matches (handler fires)
  - 7 named/mention phrasings → `_PLAY_MUSIC_RE` does NOT match (routes
    elsewhere or stays with the LLM)
  - 5 demo-card phrasings ("play something chill", "put on jazz", "play
    some reggae", etc.) → claimed by at least one Spotify classifier so
    the server does something

**`blender/agent_bus/builder3/QUEUE/0013_music_demo.md` (new)**
- Committed from the Board's Board-dispatch instruction to write a card
  for the music demo (previously missing from QUEUE).

---

## Test results (real Mac, pytest 9.1.1)

```
tests/test_b3_spotify_music_demo.py ..........................  (50 passed)
tests/test_b3_interrogative_routing.py .........................  (48 passed)
============================== 98 passed in 7.30s ==============================
```

No regression on prior B3 routing suite.

---

## What this does NOT prove

Offline tests prove the classifiers fire. They do not prove the Web API
executes the request against David's live Spotify. That needs a live turn:

> David: "play me some music" → eLo: "Playing your <playlist>." → Spotify
> actually plays on the active device.

This is the Board's live-verification gate per CLAUDE.md "BUILT ≠ DONE".
Three verification turns requested, varying wording per the Board test
gate for integration cards:

1. "play me some music" — formerly silent-ack path, now routes to
   `play_music()`.
2. "put on jazz" — `is_search_play_intent` routes to `agent()` →
   `_catalogue_playlist("jazz")`.
3. "pause the music" — `control_for()` → `control("pause")` →
   `spotify_web.pause()`, with state read back.

Acceptance for 0013: all three result in audible playback / silence, no
capability denial, no "Got it" without action.

---

## File-lock discipline

- Created `tools/spotify_play.py.lock` before editing.
- Committed (62a577b).
- Deleted the lock immediately after commit.
- No shared files on the CLAUDE.md list were touched (server.py / spine.py /
  backend_router.py / prompt_builder.py / identity_kernel.py / memory_faculty.py
  / vault_layer.py / graph_loader.py / ambient_engine.py).

---

## Status

- Card 0013: **built, filed for Board live-verification.** Do NOT self-promote
  to BUILT per CLAUDE.md "BUILT ≠ DONE".
- Items 1–3 of the demo sprint remain blocked as above.
- EXIT — one card only.
