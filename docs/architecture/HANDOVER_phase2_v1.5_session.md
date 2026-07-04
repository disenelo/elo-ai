# eLo OS Phase 2 — Handover: v1.5 Executive Faculty

## What you are

eLo OS AI Agent. You work strictly within `~/elo-ai/`. You never touch Unity `.cs` files.
You never modify `runtime/executive.py` or `prompts/` without being explicitly told to — those are protected by FREEZE_V1_LOCK.md.

## What v1.5 is

The Executive Faculty. The only entity permitted to make decisions.

**File**: `runtime/spine/executive_faculty.py`

v1.5 does NOT replace `runtime/executive.py`. It wraps it. The identity/personality layer in `executive.py` is frozen. This module reads the executive's output from the attention model and enriches the CognitivePlan with:
1. Relationship context (from v1.4 Relationship Faculty)
2. EmotionalVector — 10 continuous 0.0–1.0 values

## What was built

```
runtime/spine/executive_faculty.py
    enrich(plan, relationship, attention) -> CognitivePlan
    _compute_emotional_vector(plan, relationship) -> EmotionalVector

    _ACTION_TO_STATE — maps CAL action → ELE state name
    _VALENCE_WARMTH  — maps valence string → warmth float
    _MOMENTUM_ENERGY — maps momentum string → energy float
```

`enrich()` is called by `spine.py` AFTER the raw executive decision is loaded into the plan. It runs the emotional vector computation and stamps it onto `plan.emotional_vector`.

## How to verify it works

```bash
cd ~/elo-ai
python3 -c "
from runtime.spine.plan import CognitivePlan
from runtime.spine.relationship_faculty import RelationshipContext
from runtime.spine.executive_faculty import enrich

plan = CognitivePlan(raw='yo building something', conversation_action='build', valence='positive', momentum='building', confidence=0.9)
rel  = RelationshipContext(relationship_type='creator', familiarity=0.95, trust=0.90)
plan = enrich(plan, rel, {})

print('ev state :', plan.emotional_vector['state'])    # creative_discovery
print('ev energy:', plan.emotional_vector['energy'])   # 0.82
print('ev warmth:', plan.emotional_vector['warmth'])   # ~0.93
"
```

Expected: `ev state: creative_discovery, ev energy: 0.82`

## Freeze state

This commit is tagged: `v1.5-executive-faculty`

What is frozen at this tag:
- `executive_faculty.py` — `enrich()` and `_compute_emotional_vector()` interfaces
- `plan.py` — `EmotionalVector` dataclass and `CognitivePlan.emotional_vector` field

Do not change the field names on `EmotionalVector` — the Light Engine reads them.
Do not change the `_ACTION_TO_STATE` keys without updating `docs/architecture/11_emotional_light_engine.md`.

## What the next session (v1.6) builds on top of

v1.6 — Cognitive Plan Object: extend `plan.py` with `presence_plan` field and `PresencePlan` dataclass. The Emotional Light Engine (v1.8) populates this field and all downstream embodiments read from it.

---
Built: Phase 2 session — 2026-07-04
Status: LIVE ✅ tested end-to-end in server pipeline
