# FROM BUILDER 3 — 2026-10-06 (evening) — rest of the capability-demo failures fixed in the tools
**David L3:** "complete your entire queue … and stop asking me things."
**Status:** built and committed. **No live-server turns** were run (no Board GO). Each fix was checked by calling the tool directly; real-world side effects were stubbed or cleaned up. Every item below is NOT DONE until David sees it (verification rows 13–20, added to `TO_BOARD_2026-10-06_TEST-WINDOW-REQUEST.md`).

| Demo failure | Cause found | Fix | Commit |
|---|---|---|---|
| "make a note: …" → mock filler | routed to Obsidian; Notes regex needed a space after "note"; `create_note` always said "created"; AppleScript escape order wrong | create forms → Apple Notes as a direct answer; the note count is checked before and after; "make a note" removed from the vault triggers | `f1bb47a` |
| message request → filler | never routed; `send_message` said "Sent" even on failure (it checked stdout, but errors go to stderr); `buddy "<name>"` | Contacts lookup → ask "Send … to <name>? say send it" → send to the real handle; success only on rc 0 | `54608a5` |
| Blender / robot / heat press claimed yes or invented | nothing told eLo these aren't built | `capability_status.not_built_answer()`: "Not yet — My robot body isn't connected to me." Mentions are left alone | `35143ad` |
| "read my eLo tracker" → filler | the file tool only took paths | trackers by name, newest copy; summary taken from the file (latest entry, status marks) | `9fa291f` |
| image → "I don't have that recorded"; 3D → invented "free3d.com" | the tools ran; the LLM overrode the outcome | `[IMAGE_GEN]` / `[MODEL_GEN]` outcome spoken directly | `efe506c` |

## Blocker: Contacts + Messages automation not permitted (-1743)
`osascript` → Contacts / Messages: "Not authorised to send Apple events". eLo now says so ("macOS hasn't given me permission to use Contacts yet") and never pretends to have sent. To enable, on David's Mac: System Settings → Privacy & Security → Automation → allow the app that runs `server.py` (Terminal, VS Code or DisenELO Presence's launcher) to control **Contacts** and **Messages**. Board to schedule; Builder 3 doesn't need it to proceed.

## Still with other seats (specs filed earlier)
- **Builder 1:** speak `execute()`'s result (volume "Sorted."); `app_open` immediate; `_direct_intercepts` context spoken raw; names → research before 0021; `vault_write` not selected; mock fallback on slow turns; epistemic-class case mismatch (blocks WKG writes from research); ROOT-7 anchor wiring.
- **Designer / Builder 1:** "where are you" too vague.
- **David:** Alexa skill account (setup guide ready).

## Addendum (later the same evening)
| Item | Fix | Commit |
|---|---|---|
| Volume answered "Sorted." (spine canned pool, result discarded) | volume / mute / dark mode / screenshot are answered in the tool layer with the Mac's own result. `system_agent.detect()` no longer offers them to the spine | `67249a4` |
| WO-018 capability gate bypassed (pre-existing: 2/6 before B3 touched the file) | every B3 direct answer checks the registry switch (fail-open); weather / news are called through `_AGENTS`. Suite **6/6** | `f180010` |

`test_canon_viii_memory.py` fails 3/18 both before and after Builder 3's changes (checked on the previous commit). Not Builder 3's; owner Builder 1.
