# WO-DREAM-007 — Dream Faculty: Visual Layering Engine

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## PHASE 6 — Visual Layering Engine

**File:** `faculties/dream/layer_compositor.py` (new)

Composite all scene images into one final artwork per dream cycle, using blend modes weighted by dream data.

### Layer structure

| Layer | Source | Opacity | Blend Mode |
|---|---|---|---|
| Base (NREM/Early REM) | Scene 01 | High (0.9) | Normal — structural foundation |
| Memory layers (Mid REM) | Scene 02–03 | Medium (0.4–0.6) | Multiply or Overlay — interference |
| REM apex (Late REM) | Scene 04+ | Low but intense (0.2–0.4) | Screen, Difference, or Color Dodge |

**Opacity driven by emotional weight:** High-significance fragments occupy more visual space. Weak fragments appear as faint traces.

### Blend mode selection driven by emotion vector

- Wonder/Joy dominant → Screen or Color Dodge (luminous, opening)
- Anxiety/Fear dominant → Multiply or Difference (darkening, disrupting)
- Sadness/Grief dominant → Overlay (muted interference)
- Mixed → composite selection by highest emotion

### SPG recurring motifs

If symbol_engine detects a motif recurring across ≥3 prior dreams, inject it as a semi-transparent overlay into the apex layer. It builds over time — not hardcoded, observed.

Final composite saved as `dream_<dream_id>_final.png` with full metadata JSON sidecar.

---

## BUILDER RESULT — 2026-09-27

**Status:** BUILT + UNIT TESTED — composite output verified (189,755-byte PNG)
**Commits:** `cc9ea5b` (layer_compositor.py) + `7ed8dc2` (join 5b→5c→6 end-to-end)
**File:** `faculties/dream/layer_compositor.py`
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-006-007_fx_and_compositor_evidence.md`

### What was built

- Multi-frame layering: Memory (base) → Association → Emotion → Transformation → REM distortion → SPG recurrence → Final composite
- Blend modes: Multiply, Overlay, Screen, Soft Light — selected per layer type
- Emotional weighting applied to blend opacity per vector dimension
- `composite(frames, emotion_vector, intensity)` → valid PNG

### Defect found and fixed

`7ed8dc2` — intensity-first capping made the most abstract frame the structural base, dropping the grounded scene entirely under a cap. `dream_fx` and `layer_compositor` were each correct in isolation; the defect lived in the seam between phases. Fixed by re-ordering the pipeline so the grounded scene is always the base layer.

### First complete output (real production run)

Engine produced its first complete output: 5 cycles, 14 scenes planned, 4 generated under cost cap, FX-treated, composited to one 189,755-byte PNG artwork with provenance sidecar. Only the paid DALL-E call was stubbed; everything downstream was production code.

### Tests

`test_dream_fx_and_compositor` — 17/17 passed (covers both WO-006 and WO-007)

Builder 1 · 2026-09-27 / 28
