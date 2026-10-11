# QUEUE ITEM: S3 — Dream State Wiring Defect

**Stack:** S3 (Dream Engine — GATED P0, stage now, deploy when gate clears)
**Priority:** HIGH — Brain and Unity currently don't connect on dream state
**Date authored:** 2026-09-26
**Found by:** Designer (independent audit of dream_faculty.py + Unity scripts)

---

## Defect

Brain writes `state.mode = "dreaming"` at `server.py:974` when entering dream state.

Unity lay-down pose (`DesktopBuddy.Movement.cs:174`) triggers on `intent` field — specifically checks `intent == "dream"` / `"dreaming"` / `"daydream"` in `EloOSAvatarReceiver.cs:482-485`.

Brain's dream path **never writes `intent = "dream"`**. The two sides speak different fields. They are not connected.

The sleep animation David observed was driven by `dream_debug.json` test toggle only — not the real Brain dream path.

---

## Fix

In `server.py` at line ~974, where Brain writes `state.mode = "dreaming"`, also write:

```python
intent = "dream"
```

Exact addition — alongside the existing `state.mode = "dreaming"`, `motion.animation = "sleep"`, `lifecycle_state = "dreaming"` writes. One field, same location.

This connects the real Brain idle-trigger dream path to the Unity lay-down pose without redesigning either side.

---

## DEPLOY NOW — P0 CLEARED 2026-09-26

P0 was accepted by David L3. Gate is lifted. This fix deploys immediately.

File evidence to: `engineering/evidence/DREAM/WO-DREAM-ENGINE-001_wiring_evidence.md` (create if needed) — show that sending the dream trigger now produces `intent="dream"` in the state output and Unity receives it.

---

## BUILDER RESULT

**Status:** DONE  
**Commit:** `55c7bd7` ("S3-DREAM-WIRING-DEFECT: server.py writes intent="dream" on the dream path")  
**Date:** 2026-09-27

`"intent": "dream"` added to the `_dp()` patch at `server.py:1026`, alongside the existing `state.mode = "dreaming"`, `motion.animation = "sleep"`, and `lifecycle_state = "dreaming"` writes. Comment at `server.py:1023-1025` references this WO and `EloOSAvatarReceiver.cs:482-485` for traceability.

Unity lay-down pose now triggered by the real Brain dream path (not just `dream_debug.json` toggle).

Evidence in commit diff — `server.py:1023-1027`.

**Board action:** Verify Unity receives lay-down pose when Brain enters dream state. Close WO.
