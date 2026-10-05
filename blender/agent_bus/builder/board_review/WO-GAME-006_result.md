# WO-GAME-006 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Status:** COMPLETE — game event bus module created, schema agreed, commit febc879

---

## What was done

### Commit febc879 — new runtime/game_event_bus.py

New module: `runtime/game_event_bus.py`

**Bus path:** `blender/game_events.json` (ring buffer, max 50 events)

**Agreed schema:**
```json
{
  "embodiment": "game",
  "event_type": "item_collected | enemy_encountered | life_lost | level_cleared | player_action",
  "detail": {},
  "timestamp": "ISO8601",
  "consumed": false
}
```

**Public API:**
- `emit_event(event_type, detail)` — validates event_type against `VALID_EVENT_TYPES`, writes to bus. Raises `ValueError` on unknown type.
- `poll_events(mark_consumed=True)` — returns unconsumed events; marks consumed atomically via tmp-file replace.
- `ingest_event(event)` — converts raw event to context string: `[GAME EVENT — embodiment:game, context:simulated] David just collected an item: ...`
- `clear_bus()` — empties the bus.

**VALID_EVENT_TYPES:**
```python
{"item_collected", "enemy_encountered", "life_lost", "level_cleared", "player_action"}
```

---

## Acceptance tests — all pass

`tests/test_wo_game_mode.py` AT-1..AT-5, AT-8:
- AT-1: emit_event writes valid event with correct schema
- AT-2: all required event types in VALID_EVENT_TYPES
- AT-3: invalid event_type raises ValueError
- AT-4: poll_events returns pending events and marks consumed correctly (double-poll = 0)
- AT-5: ingest_event produces labelled [GAME EVENT] context block with embodiment:game
- AT-8: runtime.game_event_bus fully importable from server.py's path

---

## Files changed

| File | Change |
|------|--------|
| `runtime/game_event_bus.py` | New file — 124 lines |

**Commit:** `febc879`
