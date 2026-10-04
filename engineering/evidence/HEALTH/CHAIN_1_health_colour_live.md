# CHAIN 1 — Health Bar Colour

**Status:** Wired. Requires live server to confirm elo_battery value in blender_state.json.

## What's wired

- `server.py:3894` — per-turn cognitive drain writes `elo_battery` to `_hb.tick()`
- `core/health_battery.py` — `snapshot()` returns `{elo_battery: float, elo_battery_state: str, ...}`
- `ambient/ambient_engine.py` — `fields.update(_hb.snapshot())` at line ~264 → patched to blender_state.json each tick
- `EloBatteryBar.cs` — reads `elo_battery` from blender_state.json, tints green→amber→red

## Verification required

David must restart server.py and check blender_state.json for `elo_battery` changing during conversation.
Expected: value decreases on each turn, increases when calm, triggers amber at 0.5, red at 0.25.

Builder 1 cannot verify live (no running server access). Code chain is confirmed complete.
