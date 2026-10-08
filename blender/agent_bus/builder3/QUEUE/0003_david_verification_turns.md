**WO:** DAVID-VERIFICATION · **Seat:** builder3 · **Priority:** P0
**Reserved?** no

## Goal
David must see eLo's capabilities working in his own chatlog — not just in test results. B3 result cards and commits exist but David hasn't done the live verification turns.

## The 12 verification turns (run with David live, no test server)
Say each of the following to eLo and record what eLo says back:

1. "What's the weather like?" → eLo gives Hackney Wick weather (not a generic answer)
2. "Play some music" → Spotify opens / plays
3. "Pause the music" → Spotify pauses
4. "What's on my reminders?" → eLo lists reminders from Apple
5. "Make a note: eLo capability demo complete 2026-10-06" → eLo confirms note made in Apple Notes
6. "What did I just ask you to note?" → eLo retrieves it
7. "Open Spotify" → Spotify opens
8. "Show me your brain" → Presence/brain view opens
9. "What's my battery?" → eLo reads Mac battery %
10. "Search for the latest AI news" → eLo returns current results
11. "Remember this: my studio is in Hackney Wick" → eLo says "Saved." or "Got it"
12. "Where is my studio?" → eLo says "Hackney Wick" without being re-told

## Seat action
File `FROM_BUILDER3_DAVID-VERIFICATION-RESULTS_<date>.md` with each turn result — what David said, what eLo said, pass/fail.

## Done when
All 12 turns recorded (pass or fail noted). David has seen it in his chatlog.

## Result
- commit:
- test:
- notes:

## Seat pre-check (Builder 3, 2026-10-07, before David's session; no live-server turns)
Each turn traced through the language faculty → Executive candidates → B3 tool layer, with real side effects stubbed. Predicted reply and owner if it fails:

| # | Turn | Predicted eLo reply | Path / owner |
|---|---|---|---|
| 1 | What's the weather like? | "<conditions> in Hackney Wick — <t>°C…" | weather (Executive top candidate) · B3 |
| 2 | Play some music | "Back on — <track>." or "Playing your <first playlist> playlist." | spotify_play.play_music (`268b4c6`) · B3 |
| 3 | Pause the music | "Paused." | spotify_play.control · B3 |
| 4 | What's on my reminders? | "You've got 14 open reminders: …" (Reminders' own store; the AppleScript read timed out) | `268b4c6` · B3 |
| 5 | Make a note: eLo capability demo complete 2026-10-06 | "Made a note: “…”." + the note in Notes | `f1bb47a` · B3 |
| 6 | What did I just ask you to note? | depends on memory recall: **Builder 1 (ROOT-2)**. The Apple Note isn't read back by B3 | B1 |
| 7 | Open Spotify | "Opening Spotify." | spotify_play.open_app · B3 |
| 8 | Show me your brain | "Here's my brain." + the view opens | brain_display · B3 |
| 9 | What's my battery? | **"This Mac's on mains power — it doesn't have a battery."** (Mac Studio, pmset). If David means *eLo's* battery, that's "show me your health" / "your battery" → health view | `268b4c6` · B3 |
| 10 | Search for the latest AI news | "Looked it up on <source> — …" | web_search · B3 |
| 11 | Remember this: my studio is in Hackney Wick | "Got it — your studio's in Hackney Wick. I'll remember that." The fact is saved (facts.json "location"). No raw [CONTEXT] any more | `268b4c6` · B3 (the vault "Saved." line is B1's) |
| 12 | Where is my studio? | must say "Hackney Wick" without re-telling: **Builder 1 (ROOT-2 demonstration)**. The fact exists in memory/facts.json + user_profile | B1 |

## Seat re-check (Builder 3, 2026-10-08, after this week's routing changes; no live-server turns)
Run under the server's python, offline. Actions stubbed (notes, location/fact writes, state writes, system actions). Fingerprints of memory/facts.json, blender/user_location.json, blender_state.json and user_profile.json were unchanged.
- 1 weather → "Cloudy in Hackney Wick — 13°C, feels like 9°C." (real fetch) ✅
- 2 play some music → spotify play_music · 3 pause → spotify control:pause · 7 open Spotify → spotify open ✅ (classified only; Spotify not touched)
- 4 reminders → "You've got 14 open reminders: Buy Morning After Tea Green (due 26 Nov 2018); …" ✅ routes. ⚠️ Lists oldest first, so David will hear 2018 items first. Flagged, not changed.
- 5 note → "Made a note: “eLo capability demo complete 2026-10-06”." ✅ · 8 brain → "Here's my brain." ✅ · 9 battery → "This Mac's on mains power — it doesn't have a battery." ✅
- 10 search → web_search ✅ · 11 → "Got it — your studio's in Hackney Wick. I'll remember that." ✅
- 6 and 12 → no Builder 3 tool; memory recall (Builder 1, ROOT-2; d16a948 marks WKG facts AUTHORITATIVE). On 2026-10-07, 12 answered "Born in Fulham, raised in Brixton." Unverified since.
