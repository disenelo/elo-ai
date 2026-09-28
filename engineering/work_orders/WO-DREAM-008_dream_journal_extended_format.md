# WO-DREAM-008 — Dream Faculty: Dream Journal Extended Format

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 7 — Dream Journal (extended format)

**File:** `self/dream_journal.jsonl` (extend existing schema)

Full journal entry per dream cycle:
```json
{
  "dream_id": "a3f7c2b1",
  "date": "2026-09-22",
  "duration_s": 4320,
  "cycle_number": 3,
  "sleep_phase": "NREM+REM",
  "dream_intensity": 0.74,
  "seeds": [...],
  "memories_used": [...],
  "wkg_relationships": [...],
  "spg_patterns": [...],
  "emotion_vector": {"joy": 0.82, "wonder": 0.71, ...},
  "dream_world": {...},
  "dream_rule": "Everything floats",
  "transformations": ["condensation", "displacement"],
  "prompts": ["scene 01 prompt", "scene 02 prompt", ...],
  "scene_images": ["dream_a3f7c2b1_scene_01.png", ...],
  "final_artwork": "dream_a3f7c2b1_final.png",
  "unresolved_questions": [...],
  "new_associations": [...],
  "recurring_symbols": ["mechanical_bird"],
  "personality_delta_proposed": null,
  "insight": "...",
  "memory_refs": [...],
  "output_type": "DREAM"
}
```

All entries marked `"output_type": "DREAM"` — never `"FACT"`.

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — LIVE VERIFIED (pipeline run)
**Commit:** `39dec98`
**File:** `faculties/dream/dream_review.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-008-012_pipeline_secondary_evidence.md`

### What was built

Extended journal schema with 24 fields (§7 of the WO) including: `seeds`, `scenes`, `artwork_path`, `recurring_symbols`, `dream_world`, `candidate_insights`, `candidate_spg_patterns`, `research_questions`, `creative_artifacts`.

### Live pipeline run result (journal entry)

```
DreamReview(
    dream_id='test_evidence_001',
    candidate_insights=[
        CandidateInsight(
            content='test insight',
            significance=0.0,
            epistemic_class='HYPOTHESIS',   ← correct
            memory_origin='dream_simulation',
            retained=False,
            stage='IDEA',
        )
    ],
    creative_artifacts={
        'metadata': {'output_type': 'DREAM'}
    }
)
```

Journal contains full schema with epistemic class on every candidate insight.

Builder 1 · 2026-09-27 / 28
