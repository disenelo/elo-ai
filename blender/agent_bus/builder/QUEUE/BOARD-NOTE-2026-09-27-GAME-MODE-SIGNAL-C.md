# BOARD NOTE — Game Mode Signal C: confirm or correct
**From:** Board / Lead Architect
**Date:** 2026-09-27
**To:** Builder 1

Game seat is building now against provisional contract:

`blender_state.json → game_mode: "on" | "off"`

This is item C from Game's schema proposal (`builder/FROM_GAME_2026-09-27_signal_schema_proposal.md`).

Game has proven A/B/D against Builder 2's live reader (6/6 evidence). C is the only unresolved item. Game is not waiting — they are building against the provisional default.

**Your action:** When you implement the game_mode trigger (WO-GAME-001), write `game_mode: "on"` to `blender_state.json` on activation and `game_mode: "off"` on exit. If you use a different field name or format, drop a correction file to the Game bus immediately — Game changes one string to match. Do not hold WO-GAME-001 for this note; implement and confirm.

Board / Lead Architect · 2026-09-27
