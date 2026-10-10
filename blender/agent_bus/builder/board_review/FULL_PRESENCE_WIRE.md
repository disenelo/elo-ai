# FULL PRESENCE WIRE — Board Review

**Moved by**: Builder 1  
**Date**: 2026-10-08  
**Commit**: b104a63

---

## What was built

Added 4 new event consumers to `server.py`'s `_poll_unity_events()` loop (lines 2490–2582), wiring the Full Presence relay asks that had no consumers before this session:

| Consumer | Event type | Action |
|---|---|---|
| `auto_action` | eLo's reflex/timer self-chosen action | logs subject+payload; writes to WKG as "eLo chose X on his own" |
| `brain_action` | brain-sent movement intent result | logs subject, ok, why; on failure writes reason to WKG for learning |
| `water_play` | eLo doing something fun in water | logs moment; writes experience to WKG with `fun: True` |
| `weather_request` | app open event triggers weather fetch | launches `get_current_weather()` in daemon thread; result lands in next blender_state.json cycle |

---

## What was already done (verified before building)

- `_WORLD_MOVE_VOCAB` frozenset in `runtime/spine/presence_faculty.py` — all §2 intents already present ✅
- HP cost keys in `ambient/ambient_engine.py`'s `_consume_movement_costs()` — all keys already present ✅
- `get_current_weather()` in `tools/tool_router.py` — already documented and working ✅

---

## Implementation notes

- All 4 consumers wrapped in `try/except` — consumer error never kills poller
- WKG writes wrapped independently — WKG import failure never kills the event consumer
- `weather_request` uses `threading.Thread(daemon=True)` so the 0.1s poller loop is never blocked
- Pattern follows existing `elif _ev_type` blocks in the same function

---

## Live verification needed

Board/David to confirm Presence events (`auto_action`, `brain_action`, `water_play`, `weather_request`) are being emitted by Unity/Presence and that the server log shows the new `PRESENCE …` lines when they fire.

---

## Status

✅ Code committed  
⚠️ Live verification pending (requires David to trigger events from Presence)
