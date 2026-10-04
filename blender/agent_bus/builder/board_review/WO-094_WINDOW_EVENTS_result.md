# WO-094 Window Events / Noticing and Choosing — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 5/5 ATs pass; already implemented in prior session

---

## What was verified

`faculties/window_event_faculty.py` + `faculties/route_memory.py` + `ambient_engine.py`:
- `consume_window_events()` returns [] on absent/non-window events; returns event on match
- `decide_window_event()` returns None for empty state, is_elo_surface, unknown ev_type
- User active → peripheral (not full decision); user idle → real decision
- `route_memory`: `remember_route()` writes ONLY on `ack_received=True`; recall/confidence match
- `ambient_engine.py` wires WO-094; all three files compile clean

## ATs

- AT-0 ✅ consume_window_events: absent/non-window → []; match → event returned
- AT-1 ✅ decide_window_event: None for empty state / is_elo_surface / unknown ev_type
- AT-2 ✅ user_active=True → peripheral; user idle → real decision
- AT-3 ✅ route_memory: remember_route writes only on ack_received=True; recall/confidence match
- AT-4 ✅ ambient_engine.py wired; window_event_faculty.py + route_memory.py compile clean

**Run:** `python3 tests/test_wo094_window_events.py` → **5/5 passed**
