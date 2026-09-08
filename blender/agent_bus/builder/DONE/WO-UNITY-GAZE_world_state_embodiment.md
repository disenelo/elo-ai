# WO-UNITY-GAZE — Gaze Direction + World State (Unity Digital Embodiment)
**Owner:** Builder
**Priority:** P3
**Status:** DISPATCHED 2026-08-30
**Dispatched by:** Board / Lead Architect (16th-pass BSU, 2026-08-30)
**Source:** Build List §8 DIGITAL EMBODIMENT — "Gaze", "World state", "Movement", "Consequence reporting" [SOURCE_ARCHIVE: eLo — FINISHING : BUILD LIST.rtf]
**Lane:** Builder ONLY (Unity C# side + Python embodiment bridge). No prompt changes.

---

## Intent

Wire eLo's gaze direction and world-state signal into the Unity embodiment layer so the digital body responds to cognitive state — where eLo is looking reflects what it is attending to, and world state (what is present in eLo's environment) feeds back into the cognitive spine as a contextual signal.

---

## Background

WO-B1 (Unity body_win_id emission) is DONE. The body signal bridge exists. Q-MOVEMENT WOs (Wave 1) are DONE. Movement signals are live. The remaining gap in §8 Digital Embodiment for Builder is:
- **Gaze**: no Unity C# gaze controller wired to cognitive state
- **World state**: no world-state feedback from Unity → Python spine

Consequence reporting (WO-CAP-001) and Visual brainiser (WO-VISUAL-BRAINISER) are separate WOs.

---

## Scope

### VERIFY FIRST
```bash
# Check existing Unity embodiment signals
grep -rn "gaze\|world_state\|EmbodimentState" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/ 2>/dev/null | grep -v ".pyc" | head -30

# Check contracts.py for EmbodimentState fields
grep -A 20 "class EmbodimentState" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/contracts.py 2>/dev/null

# Check Unity bridge
find /sessions/eager-inspiring-hopper/mnt/elo-ai -name "*unity*" -o -name "*bridge*" -o -name "*embodiment*" 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -20

# Check existing Q-MOVEMENT signals for reference pattern
grep -rn "WHERE_I_AM\|WANT_TO_GO\|AM_MOVING\|ARRIVED" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/ 2>/dev/null | head -20
```

### Work item A — Gaze controller (Unity C#)
- `GazeController.cs` in Unity: reads `CognitiveState.focal_thread` (or equivalent attention signal) from the Python → Unity bridge JSON each turn
- Maps focal_thread value to a target object/direction in the Unity scene
- Gaze smoothly interpolates to target (no snap — eLo looks naturally)
- Default gaze: slightly downward-left (internal processing) when no focal target

### Work item B — World state feedback (Unity → Python)
- Each Unity tick (or on scene change), Unity emits a `world_state` payload to the Python bridge:
  ```json
  {
    "world_state": {
      "present_entities": ["<list of named objects in scene>"],
      "elo_location": "<current room/zone>",
      "ambient_light": "<value>",
      "timestamp": "<iso>"
    }
  }
  ```
- Python bridge receives this and attaches `world_state` to `EmbodimentState` in `contracts.py`
- Spine reads `embodiment_state.world_state` and makes it available to the Executive as environmental context

### Work item C — EmbodimentState extension
If `EmbodimentState` does not already have `gaze_target` and `world_state` fields, add them (Builder extends contracts.py only — no other runtime changes):
```python
gaze_target: Optional[str] = None       # object name or direction label
world_state: Optional[dict] = None      # from Unity tick
```

---

## Acceptance Tests

1. `grep -n "gaze_target\|world_state" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/contracts.py` — both fields exist in EmbodimentState.
2. Run spine with Unity bridge active: `python3 tests/test_unity_bridge.py --signal gaze` — gaze_target is non-None after a turn with a focal_thread set; value is a string.
3. `python3 tests/test_unity_bridge.py --signal world_state` — world_state dict is non-None; contains `present_entities` key.
4. `python3 tests/test_embodiment_integration.py` — full turn with Unity bridge: EmbodimentState populated with gaze_target + world_state; no exceptions.
5. `python3 -c "from runtime.contracts import EmbodimentState; e = EmbodimentState(); print(e.gaze_target, e.world_state)"` — prints `None None` (correct defaults).
