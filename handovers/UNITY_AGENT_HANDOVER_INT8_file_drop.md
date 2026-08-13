# INT-8 File Drop — Designer Handover
**From:** Builder (SEAT-ENG-001) `7276991`
**To:** Designer (SEAT-ENG-004)
**Date:** 2026-08-10
**Status:** Builder half DONE ✅ · Designer half NEEDED

---

## What Builder fixed (Python side — already committed)

Three bugs in `file_drop_handler.py` that were silently swallowing every drop:

1. **Circular import** — `from server import _voice_speak` always failed → eLo never spoke the result. Fixed: now imports directly from `voice.voice_engine.speak`.
2. **Missing state_manager** — `runtime.state_manager` doesn't exist. Fixed: module-level `_pending_drops` queue; `pop_pending_drops()` is called by `server.py` each turn and injects file content as `[FILE DROP]` context so eLo can reference what was dropped.
3. **Missing `_ts`** — if Unity's event doesn't include `_ts`, `0 > 0 = False` → event silently skipped forever. Fixed: falls back to `os.path.getmtime(unity_events.json)` when `_ts` absent.

**Result:** Python route is verified — `.txt`/`.md` → read, `.png`/`.jpg` → vision, `.pdf` → summary, `.fbx`/`.glb` → QuickLook, others → `open`. eLo speaks the result + knows about it on the next turn.

---

## What Designer needs to do

### INT-8a verify — EloFileDrop.cs format check

**File written:** `blender/unity_events.json`

**Expected format (add `_ts` if missing):**
```json
{
  "type": "file_drop",
  "path": "/absolute/path/to/dropped/file.png",
  "_ts": 1786370029.731
}
```

- `type` must be exactly `"file_drop"` (Python checks this)
- `path` must be the **absolute** macOS file path — not a relative path, not a URL
- `_ts` should be a **Unix epoch float** (`DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0` in C#). Python falls back to file mtime if absent, but adding `_ts` is cleaner and prevents any race conditions.

**Verify EloFileDrop.cs:**
1. Drop a `.txt` file onto the DesktopBuddy window
2. Check `blender/unity_events.json` — confirm it has `type:"file_drop"` + an absolute path
3. eLo should speak within ~1 second

### INT-8b — "eLo takes it" reaction gesture (WO-028 UNBLOCKED ✅)

WO-028 wave is confirmed done (`8f3fc23`). INT-8b is now buildable.

**Gesture spec (from board + WO-028 body-local rule):**

1. **Hit-test:** when a file is dropped on the DesktopBuddy window, check if it lands on eLo's bounds (not just anywhere in the window)
2. **"eLo takes it" one-shot gesture:** arm extends toward the drop point → closes (grab) → retracts to idle
   - Body-local axes — same pattern as `ArmWave.cs` (`_body.rotation * localAxis`)
   - Use `ArmReach.cs` (already parked WIP from INT-8b earlier) or extend ArmWave
   - DIRECTED gesture → compute aim geometrically (`FromToRotation` toward drop point on eLo's screen space) — no axis hunting
   - One-shot, returns to idle. No looping.
3. **After gesture:** Unity does NOT need to speak — Python already handles that. The gesture is the visual acknowledgement only.

**EloFileDrop.cs must write the event BEFORE the gesture plays**, so Python has time to process while the gesture runs.

---

## Contract summary

| What | Who | Status |
|---|---|---|
| Python reads event + speaks + injects context | Builder | ✅ DONE `7276991` |
| `unity_events.json` format (`type:"file_drop"`, absolute path, `_ts`) | Designer | ⬜ VERIFY |
| "eLo takes it" grab gesture (body-local, one-shot) | Designer | ⬜ BUILD |
| Hit-test (drop lands on eLo, not just window) | Designer | ⬜ BUILD |

David L3: drop a file on eLo → he reaches, grabs, speaks what it is.
