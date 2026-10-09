# FROM BUILDER 3 — 2026-10-06 — tools fixed after the capability demo (David: "if the tool is needed for the tools to work fix it")
**Status: built, run on the real server, NOT DONE.** David was in session; the turns did not appear in his chatlog as responses, and he hasn't verified them. Verification list: `TO_BOARD_2026-10-06_TEST-WINDOW-REQUEST.md` §3.

| Capability | Before (demo 14:04) | After (live turn, audit id) | Commit |
|---|---|---|---|
| Weather | "[CONTEXT: Weather in Manchester…" spoken raw | "Partly sunny in Hackney Wick — 20°C, feels like 24°C." (`5d184274`) | `1eb5844` |
| Reminders | reminder **and** timer; "Timer set: …" | "Got it — I'll remind you in 2 minutes to check the reminder fix." — one reminder file, no timer (`f3e76bf5`) | `6bfef1a` |
| News | "Ran into something…" (listed a folder "the") | "Top from BBC News: …" (`48ff1ffe`) | `9a5e08e` |
| Calendar | "I don't have that recorded." (AppleScript timeout) | "Nothing on your calendar today. Next up: Emma Mcgill's Birthday — Saturday 17 October, all day." (`45463181`) | `7f32056` |
| Clipboard | "I don't have that recorded." | "You copied: …" (`f614c216`) | `7f32056` |
| Last commit | mock filler | "Last commit on elo-ai: … GitHub's 1272 commits behind." (`e0335a54`) | `7f32056` |
| Dark mode | "I can't switch to dark mode" | "It's already in dark mode." (`39ad90e5`) | `995d48b` |
| Screenshot | "Shall I take a screenshot?" (nothing) | "Screenshot saved to your Desktop." + file (`eda07ead`) | `995d48b` |
| Brightness | denied / then a false "Done." | not offered as an action; INACTIVE in capability list (honest) | `9a5e08e` |

## Also fixed
- **Location:** `tests/test_wo030` wrote "Manchester" into the live `user_location.json` and David's facts. Tests are now isolated. Location comes from eLo's knowledge (Hackney Wick). New AT-14.
- **Research:** names researched in context. "Sam" → asks. Corroborated facts are stored on the first lookup. (`c064128`)
- **Spotify:** "play mode in Unity" is no longer a Spotify request (`0f40b87`).
- **Alexa:** invocation name `elo` + David's four phrases (`1763bd9`).

## Waiting on Builder 1 (specs filed)
- Speak `execute()`'s result, not "Sorted."/"Done." (volume).
- `app_open` without confirmation.
- `_direct_intercepts` context spoken raw.
- Names → research before the 0021 gate.
- `vault_write` not selected by the plan.
- LLM falling to the mock backend on slow turns.
