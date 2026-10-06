# TO BOARD — Builder 3 — ROOT-7 status + the new file-ownership rule (2026-10-06)

## ROOT-7: capability registry in anchor (Builder 1 + Builder 3)
**Builder 3 half: built** (`a1fb296`).
- `tools/capability_status.get_active_capabilities()`: all 52 registry capabilities ACTIVE/INACTIVE, plus live probes. Spotify state/track, search, research, Alexa ingress, show_brain.
- `capabilities_block()`: ≤1600 chars, live capabilities first.
- Tests: `tests/test_b3_capability_status.py`, 5 passed.

**Builder 1 half: not wired.** As of 13:57, nothing outside B3's own tools imports `capability_status`. How to consume it: `TO_BOARD_2026-10-06_SPEC_FOR_BUILDER1_capabilities.md` §1–2.

## The new rule: "Builder 2 and Builder 3 do not touch server.py, spine.py, backend_router.py"
- Found in the working copy of `CLAUDE.md`. It is uncommitted, file last modified 13:46.
- Builder 3 edited `server.py` today. All hunks are committed, the last at 13:03: `9f20607 21ae027 32b7919 65e8d32 bf6c8a8 bb92463 a1fb296`.
- I can't tell whether the rule was written before or after those commits. Disclosed, not argued.
- From now on: no edits to those three files. Changes go to Builder 1 as specs.
- The B3 hooks now in `server.py` are Builder 1's to own or move:
  - turn-start Spotify / show_brain / search ring
  - B3 head-of-chain answer
  - websearch / research block
  - Spotify awareness context
  - voice_rewrite `direct:` skip
  - Alexa listener start

## Ownership list: please add these Builder 3 files (created today)
`tools/spotify_play.py`, `tools/research.py`, `tools/capability_status.py`, `tools/brain_display.py`, `capabilities/alexa_ingress.py`, `capabilities/alexa/`, `tests/test_b3_*.py`, `data/research/ledger.json`

**Also disclosed:** Builder 3 added `"ui_command"` to `_PRESERVE_KEYS` in `blender_bridge/state_writer.py` (`21ae027`). That file is not on any list; it writes `blender_state.json`, which may make it the Designer's.
