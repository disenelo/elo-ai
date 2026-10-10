# 04_WO-CANON-XV_world_model.md

**WO:** WO-CANON-XV · **Seat:** builder · **Priority:** P2 · **Reserved?** no

## Goal
Build Volume XV — the unified World Model. ONE live world state every faculty reads once, instead of
faculties each reading sensors directly (the drift Vol XV exists to remove).

## Scope — exactly this
- Implement `LiveWorldState` per `docs/architecture/Volume_XV/01_Unified_World_State.md` +
  `02_Sensor_Domains.md` (domains incl. time: now / part-of-day / weekday).
- Wire it into the turn so faculties read the world ONCE from it.
- Perception (Vol XII) produces; World State holds. Don't duplicate Perception's job.

## Test (without David)
New test: the world state is assembled once per turn and faculties read from it; time domain populated.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
Spec: `engineering/work_orders/WO-CANON-XV.md` · Canon: `docs/architecture/Volume_XV/`

## Result
- commit: a742cdc (already done; this card was stale in queue)
- test: 14/14 AT (test_canon_xv_world_state.py) green
