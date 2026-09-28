# WO-DREAM-004 — Dream Faculty: Dream Seeds and Dream-Work Engine

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 3 — Dream Seeds + Dream-Work Engine

**File:** `faculties/dream/dream_work.py` (new)

### 3a. Dream Seeds

Each seed is a structured object:
```json
{
  "source": "Robot arm successfully moving",
  "emotional_weight": {"achievement": 0.94, "wonder": 0.71},
  "associated_concepts": ["robot", "childhood", "building", "movement", "control", "creation"],
  "spg_pattern": "Repeated theme of making imagined things physical",
  "wkg": {"robot": ["machine", "embodiment", "movement", "creation"]},
  "unresolved": "What does eLo become when physically embodied?"
}
```

The engine selects 3–7 seeds per dream cycle. Seed selection weighted by memory gravity.

### 3b. Dream-Work — three mechanisms

**Condensation:** Multiple seeds merge into one image concept.
- robot + childhood toy + workshop → "A gigantic mechanical toy standing in a childhood workshop, its articulated limbs built from unfinished machines."
- Sources condensed, not listed.

**Displacement:** Emotional importance shifts onto a different subject.
- eLo uncertain about robot → "A tiny robot stands at the edge of an enormous mechanical cliff."
- Actual subject may not appear.

**Symbolic Transformation:** Concept becomes symbol.
- "Starting again" → abandoned staircase growing new steps
- "Learning" → small machine copying movements of a giant machine
- "Memory" → transparent rooms stacked inside one another
- "Childhood" → enormous playground buried beneath a modern city

Apply all three mechanisms per cycle. Intensity (0.0–1.0) controls how far each transformation goes.

### 3c. Dream Worlds

Each dream cycle constructs a Dream World before generating scenes:
```json
{
  "location": "Abandoned childhood workshop",
  "physical_rule": "Everything floats",
  "emotional_rule": "Nothing can be completed",
  "recurring_symbol": "Mechanical birds",
  "primary_emotion": "wonder",
  "secondary_emotion": "nostalgia",
  "narrative_tension": "Something is trying to become alive"
}
```

All scenes in a cycle obey the Dream World's rules. This produces coherence even in surreal content.

### 3d. Dream Scenes

One scene per REM peak. Scenes progress in intensity:
- Scene 01 (early REM): Grounded. The literal location.
- Scene 02 (mid REM): Transformation. Objects begin to change.
- Scene 03 (strong REM): Condensation fires. Multiple seeds merge.
- Scene 04 (late REM): Abstraction. The world folds.

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — LIVE VERIFIED (pipeline run)
**Commits:** `6e76b89` (initial) + `5ad7016` (defect fix — verbs in noun slots)
**File:** `faculties/dream/dream_work.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-001-005_pipeline_core_evidence.md`

### What was built

- Dream seeds with condensation, displacement, symbolic transformation
- `DreamWorld` object: `location`, `physical_rule`, `emotional_rule`, `recurring_symbol`, `primary_emotion`, `secondary_emotion`, `narrative_tension`
- 3-stage scene arc: grounded → associative → symbolic
- `run_dream_work(dif, intensity)` → `DreamWorkResult`

### Live pipeline run result

```
res = run_dream_work(dif, intensity=0.7)
scenes: 3
world: DreamWorld(
    location='An abandoned dream hallway',
    physical_rule='Everything floats',
    emotional_rule='Nothing can be completed',
    recurring_symbol='small doors set too high',
    primary_emotion='wonder',
    secondary_emotion='tenderness',
    narrative_tension='Something is being remembered wrongly'
)
```

Recurring symbol ('small doors set too high') feeds WO-DREAM-011. Seed sources trace back to actual user utterances.

### Defect fixed

`5ad7016` — concept extraction was putting verbs in noun slots (e.g. `"A enormous david standing in a stayed"`). Corrected extraction filters by POS candidates.

### Tests

`test_dream_work` — 24 passed

Builder 1 · 2026-09-27 / 28
