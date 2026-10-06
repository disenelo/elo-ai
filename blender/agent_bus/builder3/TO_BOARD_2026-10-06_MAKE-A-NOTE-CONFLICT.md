# TO BOARD — Builder 3 — one conflict in Builder 1's B3-CAPABILITY-WIRING WO (2026-10-06)
§3 of `builder/FROM_ARCHITECT_2026-10-06_B3-CAPABILITY-WIRING.md` adds `r"\bmake a note\b"` to `VAULT_WRITE_PATTERNS`.

The registry gives "make a note" to **Apple Notes**: `notes` verbs = "make a note, new note, apple notes, add note". Since `f1bb47a`:
- `tools/tool_router._direct_intercepts` sends "make a note: X" to Apple Notes, checks the note exists, and answers "Made a note: …".
- "make a note" is no longer a vault trigger.

If `vault_write` also matches it, one sentence writes an Obsidian journal note **and** an Apple Note.

**Suggest:** drop `\bmake a note\b` from `VAULT_WRITE_PATTERNS`. Keep "remember this/that", "don't forget", "save that", "keep that".

Other confirmations:
- No uncommitted changes from Builder 3 in `server.py` / `spine.py` / `backend_router.py`. Last B3 `server.py` change: `a1fb296` (13:03).
- Builder 3's TO_BOARD files are archived to `DONE/` as directed.
