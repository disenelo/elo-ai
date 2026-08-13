# WP_I — Cross-Embodiment Validation

**Status:** PENDING
**Priority:** HIGH
**Depends On:** WP_H (Spine frozen)
**Architecture Reference:** `docs/architecture/99_future_embodiments.md`

---

## Purpose

Validate that the same cognitive process behaves consistently across all active embodiments: Terminal, DISENELO Presence (Desktop Avatar), Unity (eLo-Planet game), and Robot (when ready). One Brain, many bodies.

---

## Objective

At the end of WP_I:
- Terminal responses and DISENELO Presence responses are behaviourally identical
- Unity Avatar correctly reads blender_state.json and responds
- Robot NeoPixel colour correctly tracks eLo OS mode
- The cross-embodiment contract (`blender_state.json`) is formally documented and frozen

---

## The Cross-Embodiment Contract

All embodiments read from `blender_state.json`. This file is the single shared state surface.

**Current schema:**

```json
{
  "mode":        "idle | listening | thinking | speaking | calm",
  "expression":  { "smile": 0.0, "mouth_open": 0.0, ... },
  "head_motion": { "gesture": "nod | shake | tilt | think | lookup", "ts": 0.0 },
  "trigger":     { "name": "wave | celebrate | jump | ...", "_ts": 0.0 },
  "vision":      { "active": false, "attention": 0.0, "focus": {...}, "app": "", "description": "" },
  "position":    { "x": 0.0, "y": 0.0 }
}
```

**Who writes it:** eLo OS (`server.py` → `blender_bridge/`)
**Who reads it:** DISENELO Presence (Unity), Robot (Raspberry Pi)

---

## Embodiment Validation Matrix

| Embodiment | Active | Validation Method | Status |
|---|---|---|---|
| Terminal | Yes | Direct server responses | |
| DISENELO Presence | Yes | Chat panel + avatar animation | |
| Unity (eLo-Planet game) | Partial | EloOSAvatarReceiver.cs | |
| Robot | No (future) | blender_state.json colour/pulse | |

---

## Per-Embodiment Validation Protocol

### Terminal

1. Start server via `python3 ~/elo-ai/server.py`
2. POST to `/chat` directly
3. Confirm responses match DISENELO Presence responses for same inputs

### DISENELO Presence

1. Start app
2. Confirm eLo is visible and animated
3. Run 20-turn conversation
4. Confirm avatar state matches blender_state.json mode field
5. Confirm voice fires on first bubble only
6. Confirm multi-bubble delivery
7. Confirm trigger animations fire correctly (wave, invade, scale)

### Unity (eLo-Planet)

1. Open eLo-Planet project in Unity
2. Start DISENELO Presence alongside it
3. Confirm EloOSAvatarReceiver.cs reads blender_state.json
4. Confirm mode changes drive correct animation states
5. Confirm SpawnWave fires when `"command": "spawn_wave"` is received

### Robot (Future)

When physical robot is available:
1. Confirm Raspberry Pi 5 reads blender_state.json correctly
2. Confirm NeoPixel colour matches mode:
   - idle → teal
   - listening → white
   - thinking → amber
   - speaking → coral
   - calm → violet
3. Confirm jaw servo responds to speaking mode

---

## Consistency Test

Send the same 10 inputs across all active embodiments. Confirm:
- Response text is identical (same backend, same session)
- blender_state.json transitions are the same
- Avatar behaviour is the same

---

## Known Issues at WP_I Start

| Issue | Embodiment | Severity | Notes |
|---|---|---|---|
| Avatar facing direction on upward movement | DISENELO Presence | Medium | DebugDump needs enabling |
| Vision intermittent | All | Medium | Screen Recording permission path — mitigated July 2026 |

---

## Freeze Criteria

- [ ] Terminal and Presence responses validated as identical
- [ ] Unity avatar state validated against blender_state.json
- [ ] SpawnWave command validated end-to-end
- [ ] Cross-embodiment contract documented and frozen
- [ ] Robot validation protocol documented (even if not yet executed)
- [ ] Regression tests pass (B through H regressions must pass)
