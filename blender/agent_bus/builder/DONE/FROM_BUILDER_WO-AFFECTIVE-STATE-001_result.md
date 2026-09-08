# FROM_BUILDER — WO-AFFECTIVE-STATE-001
**Status:** DONE  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## What was built

13-dimensional continuous `AffectiveState` space — the new affective primitive replacing flat emotion strings.

### `runtime/contracts.py` — AffectiveState dataclass

13 dimensions:
- `valence` — positive/negative tone (−1.0 to +1.0)
- `arousal` — activation level (0.0–1.0)
- `safety` — felt security (0.0–1.0)
- `novelty` — encountering new things (0.0–1.0)
- `curiosity` — openness and interest (0.0–1.0)
- `confidence` — certainty and groundedness (0.0–1.0)
- `uncertainty` — complement of confidence (0.0–1.0)
- `attachment` — relational closeness (0.0–1.0)
- `tension` — internal friction (0.0–1.0)
- `comfort` — ease and calm (0.0–1.0)
- `agency` — sense of capacity to act (0.0–1.0)
- `significance` — perceived importance of turn (0.0–1.0)
- `reward` — positive feedback signal (0.0–1.0)

Methods: `to_dict()`, `label()` (returns human-readable region label).

### `runtime/significance_faculty.py` — `derive_affective_state()`

Maps SP-29 significance scores → AffectiveState via heuristic derivation.  
Text input signals (distress/positive/creative patterns) modulate valence, arousal, tension.  
All mappings marked `[ESTIMATE]` pending David L3 calibration.

### `runtime/spine/spine.py` — integration

- `assemble_cognitive_state()` calls `derive_affective_state()` and attaches to `CognitiveState`
- `affective_state` propagated from `CognitiveState` → `CognitivePlan` in `run()` after `_conversation_faculty(plan)`
- Inner-child trigger prefers `AffectiveState.curiosity` over SP-29 proxy when available

### `runtime/spine/plan.py`

```python
affective_state: "AffectiveState | None" = None
```

### `server.py`

`exec_decision` dict now carries `affective_state` (serialized to dict via `.to_dict()`).

### `runtime/prompt_builder.py`

Affective register voice shading injected after CCM context:
- `arousal > 0.7` → forward, alive register
- `comfort < 0.3 and tension > 0.6` → gentler, grounded register
- `curiosity > 0.7` → open, wondering register
- `uncertainty > 0.65` → honest uncertainty register

---

## JEG CHECK — Does affective state actually shade eLo's voice?

### Before (flat emotion string, no affective shading):
Prompt contained: `Emotional state: curious`  
No register instruction based on intensity.

### After (AffectiveState-driven shading):
When `curiosity=0.82, arousal=0.6`:  
Prompt injects: `"Be open and wondering — let the curiosity lead."`

When `tension=0.75, comfort=0.2`:  
Prompt injects: `"Be gentle and grounded. Something heavy is here."`

The affective geometry drives register instruction, not the label — meaning the same "curious" label at high vs low intensity produces different voice posture.

---

## Test result

```
1566 passed (baseline), all pre-existing failures unchanged
```
