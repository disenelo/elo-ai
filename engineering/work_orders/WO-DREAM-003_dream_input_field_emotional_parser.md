# WO-DREAM-003 — Dream Faculty: Dream Input Field and Emotional Parser

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 2 — Dream Input Field + Emotional Parser

**File:** `faculties/dream/dream_input.py` (new)

### 2a. Dream Input Field — 13 source types

Before dreaming, collect material from:
1. Recent conversation (last session content)
2. Recent experiences (eLo encounter log)
3. Memory (previous sessions)
4. Project memory (what is currently being built)
5. WKG (connected concepts)
6. SPG (recently repeated patterns)
7. Emotional significance (what carried unusual weight)
8. Unfinished threads (what wasn't resolved)
9. Novelty (what was unusual)
10. Failure (what didn't behave as expected)
11. Achievement (what succeeded)
12. Relationship (what interaction mattered)
13. Embodiment (what the current body experienced)

Sources filtered by cycle number — early cycles pull from sources 1–4, middle from 5–8, late from 9–13 plus cross-era memory.

### 2b. Day Residue

Raw material from recent experience. Does NOT become a prompt directly — it becomes input for Dream-Work transformation.

### 2c. Emotional Vector (7 dimensions, 0.0–1.0)

```python
emotion_vector = {
    "joy":       float,
    "wonder":    float,
    "fear":      float,
    "anger":     float,
    "sadness":   float,
    "anxiety":   float,
    "curiosity": float,
}
```

Also derive:
- `emotional_intensity` (magnitude of vector)
- `significance` (from SPG/memory weight)
- `novelty` (how unusual the input was)
- `unresolvedness` (unfinished threads count × weight)

### 2d. Emotional Peaks

Scan session history for moments where significance spiked. A peak looks like:
```json
{
  "timestamp": "22:14",
  "content": "I actually got the arm moving.",
  "significance": 0.92,
  "joy": 0.86,
  "surprise": 0.91,
  "curiosity": 0.77,
  "achievement": 0.94
}
```

Peaks become candidate Dream Seeds. They do not appear literally in the dream.

### 2e. Memory Gravity

Not all memories have equal probability of entering the dream field.

```
MEMORY GRAVITY =
  SIGNIFICANCE
  + RECURRENCE
  + NOVELTY
  + EMOTIONAL WEIGHT
  + UNFINISHEDNESS
  + RELATIONSHIP IMPORTANCE
  + FUTURE RELEVANCE
```

High gravity = higher probability of selection. Not guaranteed.

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — LIVE VERIFIED (pipeline run)
**Commit:** `44340fb`
**File:** `faculties/dream/dream_input.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-001-005_pipeline_core_evidence.md`

### What was built

- 13 source types with memory gravity weighting
- 7-dimension emotional vector: `{joy, wonder, fear, anger, sadness, anxiety, curiosity}`
- Source filtering by `content_band` (early/mid/late cycles see different source mix)
- `collect(cycle_number, ctx)` → `DreamInputField`

### Live pipeline run result

```
dif = collect(1, ctx)  # ctx contained 'excited', 'anxious', 'wonder how'
emotion_vector: {'joy': 0.333, 'wonder': 1.0, 'fear': 0.0, 'anger': 0.0,
                 'sadness': 0.0, 'anxiety': 0.333, 'curiosity': 0.0}
dominant_emotion: wonder
emotional_intensity: 0.418
```

All three emotion dimensions extracted correctly from raw conversation text. Source 1 (`recent_conversation`) active on cycle 1 content band.

### Tests

`test_dream_input` — 15 passed

Builder 1 · 2026-09-27 / 28
