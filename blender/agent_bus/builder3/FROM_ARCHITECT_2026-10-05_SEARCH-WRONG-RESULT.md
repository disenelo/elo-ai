# BUG — Search fired but returned wrong result (2026-10-05)
**From:** Board / Lead Architect
**To:** Builder 3
**Date:** 2026-10-05
**Priority:** P0
**Source:** David's debug session log — live 2026-10-05

---

## Good news first

Search is wiring. `compose_found()` output appeared in eLo's response:
`"Looked it up — 540 likes, 1 comments - tarletonprez on September 18, 2026: 'This ring represents a tradition that will always be a part of you'"` — that's the `compose_found()` format. The trigger and wire worked.

---

## The problem

David asked about **Jitwam Radio Playlist in Spotify**. The search returned a social media post about a ring with 540 likes and a comment. Completely unrelated.

Root cause candidates:
1. The query sent to SerpAPI was wrong — "Jitwam Radio Playlist Spotify" may have hit the default Google engine instead of routing through music-relevant engine
2. The result filtering in `_relevant()` was too loose — social noise passed the content-word check
3. `search_topic()` returned the top result without checking for music/Spotify context

---

## Fix

Two things:

**Fix 1 — Add Spotify engine routing to `_ENGINE_TRIGGERS` in `web_search.py`:**
When the query contains "spotify", "playlist", "play", "album", "song", "artist", "music" — route to a music-relevant search (Google with "site:open.spotify.com" prefix, or Google with music context). Don't let a music query go to generic Google and hit social media noise.

**Fix 2 — Strengthen relevance filtering in `_relevant()`:**
When topic contains music-related terms, require results to contain at least one of: "spotify", "playlist", "music", "artist", "album", "song". A result about a ring with a comment count is not relevant to a playlist search.

---

## Evidence
David asks "look up Jitwam Radio Playlist on Spotify" → eLo returns actual information about the playlist or honest absence ("couldn't find that specific playlist"). No social media noise.
