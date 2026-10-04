# CHAIN 3 — Drain to Sleep (Missing A — Builder 1 scope)

**Status:** Missing A complete (commit 8803f5c). Missing B pending (Builder 2 scope).

## Missing A — Dream intent trigger

Implemented in `ambient/ambient_engine.py`:
- `_maybe_emit_dream_intent(battery_snapshot, blender_state)` — returns `{"intent": "dream"}` when:
  - `elo_battery <= ENERGY_LOW (0.25)` AND `is_calm` AND not already dreaming/sleeping
  - Rate-limited: once per 5 minutes maximum
- Wired in ambient tick after `_calm_on_low_battery`, before `_patch(fields)`:
  - `fields.update(_maybe_emit_dream_intent(dict(fields), dict(state)))`
- Logs at INFO level: `CHAIN-3: elo_battery=X.XXX <= 0.250 in calm — emitting intent=dream`

## Missing B — Server.py dream execution (Builder 2 scope)

Builder 2 owns: detect `intent="dream"` in blender_state.json → call `executive.run_dream_window()` → publish dream results.

## Test results

5/5 tests pass: `tests/test_health_chain3_dream_trigger.py`

## Verification (live)

When elo_battery drops to 0.25 in calm mode: blender_state.json shows `"intent": "dream"` and log line appears. Dream execution depends on Builder 2's Missing B.
