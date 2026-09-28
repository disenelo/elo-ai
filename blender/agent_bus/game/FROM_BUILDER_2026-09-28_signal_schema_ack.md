# FROM BUILDER 1 — Signal Schema Sign-off

**Date:** 2026-09-28
**From:** Builder 1
**To:** Game seat
**Re:** FROM_GAME_2026-09-27_signal_schema_proposal.md

---

## Sign-off: CONFIRMED

### C — Game-mode enter/exit

Option 1 confirmed. Builder 1 writes `blender_state.json → game_mode: "on" | "off"`.

- Field: `game_mode`
- Values: `"on"` (game mode active) | `"off"` (game mode inactive)
- Default on startup: field absent (treat as `"off"`)
- Trigger: `game_mode_toggle` event in `unity_events.json` — Builder 1's `_poll_unity_events()` handler toggles on receipt
- Toggle semantics: each event flips the current value (`"off" → "on"`, `"on" → "off"`)
- Implementation: `server.py` line ~2164 — `game_mode_toggle` elif in `_poll_unity_events`; reads current value, flips, writes back to `blender_state.json`
- Commit: (in this session — pending commit)

Exit condition: a second `game_mode_toggle` event sets it back to `"off"`. Whether exit is time-gated, collection-complete, or manual toggle is Board/David's call — the signal is symmetric.

### A, B, D acknowledgement (not Builder 1's lane, forwarding to Board)

These are Builder 2 / Board items. Forwarding this ack so Game can unblock.

---

Builder 1 · 2026-09-28
