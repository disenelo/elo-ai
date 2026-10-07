# TO BOARD — Builder 3 — 2026-10-07 — verification pass (no live turns)

## Spine capability selection gap (owner: Builder 1/2, spine)
Offline `runtime/spine/spine._capability_faculty()` candidates:
- "what's the weather like right now" → **[vision] only**. Weather is never surfaced. That's why a keyword weather intercept has existed since before B3.
- "what did I copy" → **[]**.
- News / calendar / last commit / tracker → correct (news, calendar, github, file_read).

Under WO-122 the Executive must select a data capability. These two can't be selected today. The B3 direct answers for them stay keyword-driven, but now **stand down when the Executive picks something else** (`8db420e`).

## Tests that wrote David's live data: fixed
- `tests/test_hard01_rs003_rs004.py` ran the real vault writer. **7 "Cats Are Great" notes** are in `obsidian_vault/07 Journal/`, the last one at 01:44 today from B3's test run. Now stubbed. B3 left the notes in place (no-delete rule).
- `tests/test_canon_vii_executive.py` IQ-7 wrote `test-id-001` into the live `decision_journal.jsonl`. Now uses a temp file. The row B3's run wrote is archived at `.memory-archive/decision_journal_test_rows_removed_2026-10-07.jsonl` and removed.
- `tests/capability_audit.py` appends 112 lines to the tracked `engineering/evidence/LIVE/capability_audit.jsonl` every run. B3 restored the file after its runs. Owner to decide whether it should write there.

## Regression check
83 test files import a B3-changed module. All were re-run, with fingerprints on journal, facts, location, reminders, Desktop, research ledger and decision journal: **no real data changed.**

Remaining reds, all pre-existing or other seats':
- `wo122` RT-3: the COG-004 time-intent guard strips the test's synthetic "the time". RT-3's own point, weather not firing, now holds.
- `canon_iii` RU-3: `server.py`.
- `wo103` PW-2: WO-100 open, "leave red".

## Verified by reading rather than running
- **Volume → no longer reaches the spine's canned "Sorted."** The spine and pipeline use `system_agent.detect()`, which no longer offers volume. Live proof still owed: verification row 21.
- **`[IMAGE_GEN]` / `[MODEL_GEN]` texts don't trip the world-graph gate** (checked with `graph_loader.retrieve`). Edge case: an image of an eLo-world entity ("an image of K-7") would.
- **Obsidian "what did I write in my notes about the robot"** matches `01 Identity/eLo Physical Body.md`. It moves from CHECK to working, from its demo turn.
