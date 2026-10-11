# Board Gate — WO-B3-0012 Web Search + Summaries
**Date:** 2026-10-11  
**Verdict:** SIGNED OFF — pending live-turn

---

## Commits reviewed
- `88b1396` — `"what's happening with X"` added to `_SEARCH_TRIGGERS`; full pipeline test added
- `76a660a` — `format_for_context` now steers LLM to summarise (not dump bullets); steering applied inline in Builder 3's file, not via prompt_builder

## Code verified (Board read)
- `tools/web_search.py` — trigger list extended. Apostrophe-optional match correct.
- `format_for_context` — instruction header added. Sprint-acceptance phrase ("natural language, not a raw list of links") is achievable on weak-model turns.
- No shared files on the FILE LOCK list touched. `spotify_play.py.lock` pattern not required here (web_search.py is Builder 3's file).

## Test result verified
Builder 3 ran offline suite. Board cannot run against live server (sandbox restriction — CLAUDE.md). Taking Builder 3's reported results at face value for offline routing gates.

## What this does NOT prove (per BOARD TEST GATE — INTEGRATION cards)
Offline tests prove classifiers fire. They do NOT prove the web fetch executes and the LLM synthesises in real conditions.

## Live-turn gate (Board must witness or David confirms)
Three turns, varying phrasing:
1. `"what's happening with the NBA?"` → eLo returns a conversational summary with real data, not bullet links
2. `"google Kendrick Lamar for me"` → sourced lookup line in eLo's voice
3. A follow-up rephrasing of turn 1 → eLo summarises (not dumps)

Card moves from BUILT to DONE only when David confirms one of the above in a live chatlog.

## Status
Builder 3 may promote `0012_web_search_demo.md` to BUILT. Live-turn gate above applies before DONE.

*Board / Lead Architect · 2026-10-11*
