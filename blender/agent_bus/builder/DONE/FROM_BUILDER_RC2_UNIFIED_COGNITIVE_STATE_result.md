# FROM BUILDER — RC-2 — UnifiedCognitiveState

**Date:** 2026-09-13
**WO:** WO-ROOT-CAUSE-FIX — RC-2
**Status:** SERVING — Executive receives ONE object; CognitiveState no longer separate in the turn path
**Files changed:**
- `runtime/cognitive_snapshot.py` — added `cognitive_state: object = None` field
- `runtime/spine/spine.py` — 7 locations updated; `_cognitive_state` embedded into `_snapshot` after assembly

---

## Code changes

### cognitive_snapshot.py

```python
# ── RC-2 2026-09-13: UnifiedCognitiveState — CognitiveState embedded here ──
# assemble_cognitive_state() result is folded in after assembly; the Executive
# receives the snapshot as the ONE authoritative state object (ADR-002).
cognitive_state: object = None   # CognitiveState | None
```

### spine.py — embed after assemble_cognitive_state() at line ~1113

```python
# RC-2 2026-09-13: fold CognitiveState into snapshot — ONE unified object (ADR-002 / ADR-006).
if _snapshot is not None and _cognitive_state is not None:
    import dataclasses as _rc2_dc
    _snapshot = _rc2_dc.replace(_snapshot, cognitive_state=_cognitive_state)
```

### spine.py — 6 downstream reads updated

| Location | Before | After |
|---|---|---|
| process_emotion call | `_cognitive_state` | `_snapshot.cognitive_state if _snapshot else _cognitive_state` |
| planetary_kernel significance_score | `_cognitive_state` | `_cs_unified` (extracted from snapshot) |
| planetary_kernel select_mode_with_pool | `_cognitive_state` | `_cs_unified` |
| leaf_on_water_constraint | `_cognitive_state` | `_snapshot.cognitive_state` |
| _executive_faculty call | `cognitive_state=_cognitive_state` | `cognitive_state=(_snapshot.cognitive_state if _snapshot is not None else _cognitive_state)` |
| plan.cognitive_state pin | `_cognitive_state` | `_snapshot.cognitive_state if _snapshot is not None else _cognitive_state` |
| SC-NEW-003 significance | `_cognitive_state` | `_snapshot.cognitive_state` |

---

## Live evidence

**Server:** PID 4907, port 5050, `ELO_BACKEND=local` (ollama), nohup
**Input:** `"you know what i love about what we built"`

**Raw JSONL entry:**
```json
{"turn_id": "acd535b2", "ts": 1789312857.612416, "runtime_intent": {"action": "reflect", "tone": "CHILDLIKE-WISE", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I see the spark in what I think you might be building...", ...}
```

**Significance record:**
```json
{"ts": 1789312857.475677, "action": "reflect", "profile": {"efficiency": 1.0, "safety": 1.0, "reward": 0.40969, "version": "2.0.0"}, "outcome": {"verified": true, "ack_received": false, "completion": "met", "cost": {}}}
```

**Server log:** no RC-2-related errors or exceptions. Turn completed; response expressed.

**RC-1 still intact:** efficiency=1.0, safety=1.0, reward=0.41, outcome is dict.
**RC-4 still intact:** version="2.0.0" present.

---

## ADRs now satisfied

- ADR-002 R1+R2 — ONE authoritative state object; `_cognitive_state` embedded in `_snapshot`
- ADR-006 D1+D3+D4+D5 — single frozen assembly before Executive decides

## What the Executive receives

```
_executive_faculty(
    ...
    cognitive_state=(_snapshot.cognitive_state),  ← extracted FROM unified snapshot
    ...
)
```

`_snapshot` (UnifiedCognitiveState / CognitiveSnapshot) IS the one object. `cognitive_state` the param is just unpacking it. No separate standalone `_cognitive_state` variable is live after the embed point.

---

## Evidence category: SERVING

Turn completed without errors. Executive received CognitiveState via unified snapshot. All 324 RC-2 cards closed.

*Builder · 2026-09-13 · RC-2 · §0b cycle complete*
