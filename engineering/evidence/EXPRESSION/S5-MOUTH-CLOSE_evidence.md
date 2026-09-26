# Evidence — S5: Mouth Close During Locomotion

**Date**: 2026-09-26  
**Commit**: `45b786b`  
**File changed**: `expression/expression_mapper.py` (+7 lines, −13 lines)

---

## Spec

> "expression_mapper.py — mouth close while walking: Drop `MouthOpen.Slightly: 0.1` from all base/idle mode tables (13 tables). eLo's mouth should be closed during locomotion."

Source: `blender/agent_bus/builder/START_HERE_B2.md`

---

## Fix Applied

Removed all 13 `MouthOpen.Slightly` entries from three tables:

### `_MODE_EXPRESSION` (6 removals)
| Mode | Old value | New state |
|---|---|---|
| idle | 0.1 | key removed |
| thinking | 0.25 | key removed |
| observing | 0.3 | key removed |
| building | 0.35 | key removed |
| resting | 0.05 | key removed |
| exploring | 0.4 | key removed |

`celebrating` mode was untouched — it uses `MouthOpen.Wide: 0.85` which is correct for that state.

### `_ACTION_BONUS` (4 removals)
| Action | Old value | New state |
|---|---|---|
| CHALLENGE | 0.2 | key removed |
| REFLECT | 0.1 | key removed |
| GROUND | 0.05 | key removed |
| ANSWER | 0.15 | key removed |

### `_AMBIENT_FLICKER_POOL` (3 removals)
| Entry | Old value | New state |
|---|---|---|
| entry 0 (Smile.L/R) | 0.1 | key removed |
| entry 2 (Huh) | 0.2 | key removed |
| entry 4 (Confident) | 0.15 | key removed |

---

## Verification

```
$ grep -n "MouthOpen.Slightly" expression/expression_mapper.py
(no output)
```

Zero occurrences remaining. `MouthOpen.Wide` in `celebrating` mode and `CELEBRATE` action bonus are intact (intentional — open mouth during celebration is correct behaviour).

---

## Status

PASS — all 13 occurrences removed, committed `45b786b`. Board crosscheck required before WO close.
