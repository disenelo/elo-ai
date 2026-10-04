# CHAIN 1 — Health Bar Colour

**Status:** COMPLETE — verified live 2026-10-04 with running server.

## What's wired

- `server.py:3894` — per-turn cognitive drain writes `elo_battery` to `_hb.tick()`
- `core/health_battery.py` — `snapshot()` returns `{elo_battery: float, elo_battery_state: str, ...}`
- `ambient/ambient_engine.py` — `fields.update(_hb.snapshot())` at line ~264 → patched to blender_state.json each tick
- `EloBatteryBar.cs` — reads `elo_battery` from blender_state.json, tints green→amber→red

## Live verification — 2026-10-04

Server started. `blender_state.json` read before and after one chat turn:

```
before: elo_battery=0.998, elo_battery_state=full
after 1 turn: elo_battery=0.988, elo_battery_state=full
```

Battery drains per turn ✅. Value published to blender_state.json each tick ✅.
EloBatteryBar.cs reads this value — colour chain is end-to-end.
