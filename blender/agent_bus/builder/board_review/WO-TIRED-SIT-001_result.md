# WO-TIRED-SIT-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-04  
**Status:** DONE — already implemented (prior session)

---

## Finding

Both parts were already implemented when checked this session.

**Part A** — `_emit_tired_signal()` at `ambient/ambient_engine.py:344-374`  
Called from the battery tick at lines 265-270:
```python
_emit_tired_signal(
    str(fields.get("physical_state", "")),
    state.get("motion", {}) or {},
)
```
Rate-limited (60s per band), guards: dreaming, already resting, non-tired band.

**Part B** — `server.py:7513-7541`  
When `physical_tired:*` is live in `EloSelfState.inner_events` AND `_inner_thought` contains a sit keyword (`sit`, `legs`, `rest`, `settle`, `sit down`), emits `motion: {animation: "Sit_hold", mode: "sit"}` to `blender_state.json` via `state_writer.patch()`. Guards: `_PENDING_SIT["active"]` prevents re-issue while sit is in-flight.

---

## Test results

- `tests/test_s4_tired_signal.py` — **8/8 PASS**
- `tests/test_wo035_sit_command.py` (custom runner) — **6/6 PASS**

---

## Files changed

None this session — implementation was already present.
