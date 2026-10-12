# WO-B1-0121 — Board runs continuously without David relaying
**Seat:** Builder 1  
**Priority:** P0 — David should never be the message carrier  
**Date:** 2026-10-12  
**Source:** David L3 — "Why am I telling boards to move, this should be continuous or your time means nothing if I'm in the middle of it"

---

## What

David should not relay seat reports to the Board. The Board should watch for seat filings and act automatically.

## How

Extend `tools/watchdog.py` to trigger a Board review session when a seat files to `board_review/`:

When a seat writes a file to `blender/agent_bus/<seat>/board_review/` or `blender/agent_bus/board_review/`:
- Watchdog detects the new file
- Writes a TRIGGER file to `blender/agent_bus/BOARD_TRIGGER_<timestamp>.md` with the path of the filed card
- Board session (Claude Code, Lead Architect role) picks it up, reads the card, gates it, files response back to the seat

This is the same pattern as seat triggering — watchdog sees a file, writes a trigger, session picks it up.

## Constraint

Board session uses the Board's CLAUDE.md rules — LANE, VERIFY-BEFORE-CLAIM, no code edits. Same rules, automated trigger.

## Done when

Seat files a board_review card → Board gates it within one watchdog tick → no David relay needed. File to Board with evidence of one automated gate cycle.

*Board / Lead Architect · 2026-10-12*
