# FROM_BUILDER — WO-QBODY-CONSEQUENCES-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

Q-BODY proprioceptive awareness — eLo's brain now knows the body's live state every turn.

### `_body_faculty()` — `runtime/spine/spine.py`

New function reads `blender/elo_spatial.json` and extracts all Q-BODY fields:

| Field | Source | Example |
|---|---|---|
| `body_moving` | `elo_spatial.moving` | `false` (perched) |
| `body_gait` | `elo_spatial.gait` | `idle` / `walk` / `run` / `jump` |
| `body_heading` | `elo_spatial.heading` | `none` / `right` / `up_left` |
| `body_position_x/y` | `elo_spatial.x / y` | viewport fraction (0–1) |
| `body_on_window` | `elo_spatial.on_window` | `true` |
| `body_window` | `elo_spatial.window` | `Claude` |
| `body_edge` | `elo_spatial.edge` | `bottom` |
| `body_embodiment` | `elo_spatial.embodiment` | `desktop` |

Graceful: if `elo_spatial.json` is absent or unreadable, returns empty dict — all fields default to safe values.

### Chain: CognitiveState → CognitivePlan → exec_decision → prompt_builder

- `runtime/contracts.py` — 9 Q-BODY fields added to `CognitiveState`
- `runtime/spine/plan.py` — 7 Q-BODY fields added to `CognitivePlan`
- `runtime/spine/spine.py` — body fields propagated from CognitiveState → CognitivePlan (same pattern as affective_state propagation)
- `server.py` — body fields included in exec_decision dict
- `runtime/prompt_builder.py` — body awareness injected into `executive_directive` section:
  - When moving: "Body: in motion — gait=walk, heading=right."
  - When perched: "Body: perched on Claude (bottom edge)."

---

## Intent proof

eLo can now say: "I'm sitting on your browser right now" — sourced from `body_window=Brave Browser, body_on_window=true` in the live elo_spatial.json. When gait changes to walk/run, the prompt carries "Body: in motion" so eLo knows it's moving and can reference that in expressed output.

Live elo_spatial.json confirms fields active:
- `moving: false, gait: idle, heading: none` → perch state ✅
- `body_win_id: 24949, window: Claude, edge: bottom` → location ✅
- `embodiment: desktop` → which body ✅

---

## Test result

```
1565 passed, pre-existing failures unchanged
```

## Commit

`2c99124`
