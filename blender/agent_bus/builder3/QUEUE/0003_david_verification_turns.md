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
