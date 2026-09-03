# WO-FACE-EMOTION-001 D-3 — Result Card

**Status:** DONE  
**Completed:** 2026-09-03  
**Authority:** Board WO-FACE-EMOTION-001 (dispatched by David L3 end-of-prior-session)  
**Seat:** Builder (D-3)

---

## What was fixed

### `runtime/spine/spine.py` — mood string serialisation

`_world_dict["mood"]` was being set to the raw `EmotionalTag` dataclass object instead of the
`dominant_emotion` string it contains. Unity's face trigger (D-2) reads `world_dict["mood"]` as a plain
string — the object was silently serialising as `<EmotionalTag ...>` and never matching any emotion state.

**Fix (line ~457):**

```python
_et = getattr(cognitive_state, "emotional_tag", None)
_world_dict["mood"] = getattr(_et, "dominant_emotion", "neutral") if _et else "neutral"
```

---

## Acceptance test

AT-1: `world_dict["mood"]` is a `str` → PASS  
AT-1 also confirmed that `isinstance(mood, str)` and value is drawn from `EmotionalTag.dominant_emotion`.

---

## Status of sibling deliverables

| Seat | Deliverable | Status |
|---|---|---|
| Designer (D-1) | Map existing faces → emotion states | WAITING DESIGNER |
| Game (D-2) | Unity face trigger | WAITING — depends on D-1 + D-3 (D-3 now DONE) |
| Game (D-4) | Speech jaw sync | WAITING — independent; can start any time |

---

## Phase 1 emotion set (confirmed)

`neutral` · `joy` · `curiosity` · `distress`

Jaw constraint: `JawOpening ≤ 20%` in all emotion poses.
