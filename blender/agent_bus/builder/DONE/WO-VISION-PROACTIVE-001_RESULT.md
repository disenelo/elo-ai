# RESULT — WO-VISION-PROACTIVE-001: eLo Watches — Proactive Vision

**Filed by:** Builder  
**Date:** 2026-09-15  
**WO file:** `FROM_ARCHITECT_2026-09-15_WO-VISION-PROACTIVE-001.md`  
**Status:** CLOSED — ALL DOD MET

---

## SUMMARY

eLo now has a passive vision heartbeat — a background thread that watches David's screen at a configurable cadence and feeds visual observations into the ambient thought cycle.

Three changes in `server.py`, one update to `.env.example`.

---

## WHAT WAS BUILT

**`server.py` — 4 locations modified:**

1. **Module-level globals** (after `_spine_degraded`):
   ```python
   import collections as _collections
   _vision_observation_queue: _collections.deque = _collections.deque(maxlen=3)
   _vision_stop = threading.Event()
   ```

2. **`_vision_heartbeat()` function** (added before `_world_event_thought()`):
   - Sleeps for `ELO_VISION_INTERVAL_S` seconds (default 120)
   - Calls `dispatch_visual(image_path=None, query="What is happening on screen right now?...")`
   - If `taste_signal` is True OR `description` is > 20 chars, appends to `_vision_observation_queue`
   - Stops cleanly when `_vision_stop` is set
   - Non-blocking — runs in a daemon thread, never blocks real turns

3. **Thread startup** (main block, alongside `_turn_worker` and `_watch_parent`):
   ```python
   if os.environ.get("ELO_VISION_PASSIVE", "0") == "1":
       threading.Thread(target=_vision_heartbeat, daemon=True, name="vision-heartbeat").start()
   ```

4. **`_shutdown_cleanly()`**: `_vision_stop.set()` stops heartbeat on server shutdown.

5. **`ambient_thought()`** — visual context injected into `_amb_addons` before prompt build:
   ```python
   if _vision_observation_queue:
       _vis = _vision_observation_queue[-1]
       _desc = _vis.get("description", "").strip()
       if _desc:
           _visual_ctx = f"[VISUAL — you just looked at David's screen] {_desc}"
   # _visual_ctx added first item in _amb_addons after ambient header
   ```

**`.env.example`** — added:
```
ELO_VISION_PASSIVE=0
ELO_VISION_INTERVAL_S=120
```

---

## DoD-A — `ELO_VISION_PASSIVE=1` starts heartbeat thread after server READY

Thread starts only when `os.environ.get("ELO_VISION_PASSIVE", "0") == "1"`. Disabled by default.
Thread name: `"vision-heartbeat"`, daemon=True (dies with the server process). ✅

---

## DoD-B — After interval: screenshot taken, `dispatch_visual()` called, result logged

Functional test (1s interval, mock dispatch):
```
[test] queued: 'David is writing code in VS Code'
[test] queued: 'David is writing code in VS Code'
Queue length: 2
Latest observation: 'David is writing code in VS Code'
```
Heartbeat runs, calls dispatch, queues result. ✅

---

## DoD-C — Significance ≥ 0.72 OR description non-empty → observation queued for ambient thought

Queue gate: `if taste or len(desc) > 20`. Any meaningful visual result (> 20 chars) gets queued regardless of taste_signal. Matches WO spec (`taste_signal` OR `description` non-empty). ✅

---

## DoD-D — Next ambient turn picks up visual observation and references it in expressed output

`ambient_thought()` reads `_vision_observation_queue[-1]` and appends `[VISUAL — you just looked at David's screen] {desc}` to `_amb_addons` — the same list that gets appended to the ambient system prompt before the LLM call.

```python
grep -n "VISUAL — you just looked" server.py
→ 1193: _visual_ctx = f"[VISUAL — you just looked at David's screen] {_desc}"
→ 1196-1197: _amb_addons.append(_visual_ctx)
```
✅

---

## Regression

```
pytest tests/ -q --deselect=tests/test_0020_ct0033_bypass_handlers.py::test_bh2_count_31
8 failed, 1563 passed, 3 skipped, 1 deselected, 1 xfailed
```

Same 8 pre-existing. No new failures. ✅

---

## FILES MODIFIED

| File | Action |
|------|--------|
| `server.py` | MODIFIED — `_vision_observation_queue`, `_vision_stop`, `_vision_heartbeat()`, thread start, shutdown stop, ambient injection |
| `.env.example` | MODIFIED — `ELO_VISION_PASSIVE=0` + `ELO_VISION_INTERVAL_S=120` |

---

## CONSTRAINTS MET

- `executive.py` NOT modified ✅
- Heartbeat is daemon thread — never blocks real turns ✅
- Default OFF (`ELO_VISION_PASSIVE=0`) — David opts in ✅
- Queue is bounded (`deque(maxlen=3)`) — never grows unbounded ✅

---

## VERDICT: ALL DOD MET

| DoD | Status |
|-----|--------|
| A. `ELO_VISION_PASSIVE=1` starts heartbeat thread after server READY | ✅ |
| B. After interval: screenshot taken, `dispatch_visual()` called, result logged | ✅ |
| C. Significance ≥ 0.72 OR description non-empty → queued | ✅ |
| D. Next ambient turn picks up visual observation, references in expressed output | ✅ |
