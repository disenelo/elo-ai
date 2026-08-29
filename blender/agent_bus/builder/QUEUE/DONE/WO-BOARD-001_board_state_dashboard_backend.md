# WO-BOARD-001 — board_state.json → Dashboard Backend
**Date:** 2026-08-27  
**Priority:** P1  
**Authority:** Board / Lead Architect — Board Directive 2026-08-19 §15  
**After:** WO-GUARD-001  

---

## Intent

David must not have to hunt through trackers, queues, and markdown files to understand what is moving, what is stuck, and what needs him. The board_state.json file is the single source of truth maintained by the Board each session. Builder wires it into the dashboard backend so Design can render it.

---

## Source file

`blender/board_state.json` — maintained by Board/Lead Architect. Same directory as `company_state.json`.

Structure:
- `moving` — active work items per seat with status
- `overdue` — items with seat, description, days overdue, dispatch file name
- `needs_david` — specific decisions required, with urgency and what they unblock
- `build_list` — 10-section Build List with current status per section

---

## Deliverables

**D-1:** Read `blender/board_state.json` in the same location as `company_state.json` is read. Expose its contents under the key `board_state` in whatever structure already feeds the dashboard panel (alongside `company_state`).

**D-2:** `board_state` must be available to the dashboard panel at the same refresh cadence as `company_state`. If `board_state.json` is missing or malformed, log a warning and continue — do not crash.

**D-3:** Expose `board_state["overdue"]` count as a badge value so Design can surface it prominently (e.g., "3 overdue").

**D-4:** Expose `board_state["needs_david"]` count as a separate badge.

---

## Acceptance Tests

**AT-1:** `board_state.json` present → `board_state` key populated in dashboard data with correct field count.  
**AT-2:** `board_state.json` absent → warning logged, no crash, `board_state` key is `{}`.  
**AT-3:** `moving` array readable and contains at least one item when file is present.  
**AT-4:** `overdue` count returned correctly as integer.  
**AT-5:** `needs_david` count returned correctly as integer.  

Run on miniconda3. Return 5/5 PASS to Board.

---

## Constraints

- Do not modify `company_state_writer.py` — board_state.json is maintained by the Board directly, not by the state writer.
- `executive.py` untouched (LAW-017).
- This is a read-only operation on board_state.json. Builder does not write to it.

---

*Board / Lead Architect · 2026-08-27*
