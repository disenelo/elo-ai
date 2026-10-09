# TO BOARD — Builder 3 — test window + David verification request (2026-10-06)
Supersedes `TO_BOARD_2026-10-06_TEST_WINDOW_REQUEST.md`. Follows the procedure in `FROM_ARCHITECT_2026-10-06_TEST-WINDOW-BREACH.md`.

## 1 · Disclosure: more live turns ran during David's session this afternoon
- **14:04–14:4x:** capability demo, about 60 `/chat` turns (`tools/capability_demo.py`). Then re-tests of each tool fix, about 15:00–16:00, around 20 turns.
- These ran on **David's direct instruction**: *"You do not need a test window, you need to be able to show all the capabilities of eLo."*
- Presence was connected for all of them. Their inner thoughts almost certainly reached David's chatlog without the responses, the same effect as the 11:5x–12:2x breach.
- Real side effects:
  - Spotify played (David's playlist; paused at the end).
  - One reminder fired (15:25).
  - A screenshot was saved to the Desktop.
  - Calculator opened and was closed.
  - The test suite wrote two Obsidian journal notes (see `TO_BOARD_2026-10-06_VAULT_SAVE_FINDINGS.md`).
- **Builder 3 runs no more live turns until the Board issues GO.**

## 2 · Window request: nothing new to run
- Every turn below already ran on the real server this afternoon (results: `DONE/FROM_BUILDER3_2026-10-06_TOOLS-FIXED.md`).
- None of them counts until David sees it, so **no window is needed for Builder 3 to re-run**.
- The request is §3: David's verification in his next session.
- If the Board wants a confirmed-empty re-run first: same turns, ~10 min, after GO.

## 3 · David verification: what David says, and what he should see in his chatlog
| # | David says | Should see | WO |
|---|---|---|---|
| 1 | Can you play Four Brothers Soundtrack in Spotify | "Playing your Four Brothers Soundtrack playlist." + music | B3-SPOTIFY-001 |
| 2 | Can you pause Spotify | "Paused." + music stops | B3-SPOTIFY-001 |
| 3 | resume the music | "Back on — <track>." + music | B3-SPOTIFY-001 |
| 4 | skip this song | "Skipped — now <next track>." | B3-SPOTIFY-001 |
| 5 | can you control spotify? | "Yeah, I can — … Right now Spotify's <state>." (no denial) | B3-SPOTIFY-001 / ROOT-7 |
| 6 | when did the Berlin Wall fall | **"I know this one — The Berlin Wall fell on 9 November 1989…"** | WO-RESEARCH-001 |
| 7 | what is a capybara | "Didn't know that one — looked it up on Wikipedia: …" | WO-RESEARCH-001 |
| 8 | what is a capybara (again, later in the session) | "Looked that up before — …" / "I know this one — …" | WO-RESEARCH-001 |
| 9 | what's the weather like right now | "<conditions> in Hackney Wick — <temp>…" | tool fix |
| 10 | remind me in 2 minutes to stretch | "Got it — I'll remind you in 2 minutes to stretch." + one notification | tool fix |
| 11 | what's on my calendar today | his day, or "Nothing … Next up: …" | tool fix |
| 12 | show me your brain | "Here's my brain." + the brain view opens | B3-SHOW-BRAIN-001 |

**Row 6 is the acceptance criterion** (David L3, 2026-10-06) **from a prior session**:
1. **The node:** research ledger claim, status KNOWLEDGE, sources Wikipedia + auswaertiges-amt.de, plus vault memory `GN·LN·2610·5·67d88` (epistemic_class verified), written at 14:0x today from eLo's own lookup.
2. **The retrieval:** `tools/research._recall` reads that claim.
3. **The changed response:** "Didn't know that one — looked it up…" at 14:06 (audit in `engineering/evidence/CAPABILITY_DEMO/2026-10-06_1404/report.md`) becomes "I know this one — …".

Caveat: the node is in the vault + ledger, **not the WKG**. The WKG write is blocked by the epistemic-class case mismatch (TO_BOARD #16, Builder 1).

## 4 · ROOT-7, Builder 3 half: confirmed clean and committed
`tools/capability_status.py` (last change `995d48b`), `tests/test_b3_capability_status.py` 5/5. Clean imports: `capabilities_block, get_active_capabilities, last_results, tool_result, record_result`. Nothing uncommitted. Ready for Builder 1 to wire (spec: `TO_BOARD_2026-10-06_SPEC_FOR_BUILDER1_capabilities.md`).


## 3b · Verification rows added 2026-10-06 evening (`FROM_BUILDER3_2026-10-06_QUEUE-CLEARED.md`)
| # | David says | Should see |
|---|---|---|
| 13 | make a note: eLo verification test | "Made a note: “eLo verification test”." + the note in Notes |
| 14 | text <a real contact> that eLo says hi | "Send “eLo says hi” to <full name>? …" **or** the Contacts-permission line. Then "cancel" → "Okay — not sent." |
| 15 | can you connect to your robot body | "Not yet — My robot body isn't connected to me." |
| 16 | can you open a scene in Blender and render it | "Not yet — Blender isn't connected to me." (or "Can't do that one yet — …") |
| 17 | read my eLo tracker | "eLo AI OS — Development Tracker. Latest entry …" |
| 18 | what did I copy | "You copied: “…”" |
| 19 | what was the last commit on my elo-ai repo | "Last commit on elo-ai: … GitHub's N commits behind." |
| 20 | generate an image of a red apple on a table | "Made it — …, with DALL-E 3. It's open in Preview." (uses image credit) |

| 21 | what's the volume at | "Volume's at N%." (not "Sorted.") |
