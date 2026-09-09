# FROM_BUILDER — WO-QMOVEMENT-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

All five Q-MOVEMENT lifecycle states wired from Unity/Presence → Python brain.

### Five states mapped

| State | Source field | CognitiveState field | What it means |
|---|---|---|---|
| WHERE I AM | `elo_spatial.window` + `edge` | `movement_where_i_am` | "window:Claude edge:bottom" |
| WANT TO GO | `elo_spatial.goal` | `movement_want_to_go` | target window ID (-1 = none) |
| AM MOVING | `elo_spatial.moving` | `movement_am_moving` | currently locomoting |
| ARRIVED | `elo_spatial.last_move.arrived` | `movement_arrived` | reached destination this turn |
| WHAT HAPPENED | `elo_spatial.last_move.outcome` | `movement_what_happened` | arrived / fell / interrupted |

### Chain: `_body_faculty()` → CognitiveState → CognitivePlan → exec_decision → prompt_builder

- 5 Q-MOVEMENT fields in `CognitiveState` (contracts.py)
- 5 Q-MOVEMENT fields in `CognitivePlan` (plan.py)
- Propagated from CognitiveState → plan in spine.py
- All 5 in exec_decision (server.py)
- prompt_builder injects when ARRIVED and outcome is real:
  `"Movement: just arrived. eLo knows where it is now."`

### Design data confirmed live

`elo_spatial.json` confirms all 5 states available:
- `last_move.arrived: true, outcome: arrived` — ARRIVED + WHAT HAPPENED ✅
- `goal: 24501` — WANT TO GO ✅
- `window: Claude` + `edge: bottom` — WHERE I AM ✅
- `moving: false` — AM MOVING (idle state) ✅

---

## Intent proof

Real turn: eLo arrives at a new window → `movement_arrived: true, movement_what_happened: "arrived"` → prompt carries "Movement: just arrived. eLo knows where it is now." → eLo can say "I just hopped over to your browser" rather than being unaware.

When `movement_what_happened: "fell"` → prompt would carry "Movement: just fell. eLo knows where it is now." — failure awareness in expressed output.

---

## Test result

```
1565 passed, pre-existing failures unchanged
```

## Commit

`2c99124`
