# WO-DREAM-014 — Dream Faculty: Implementation Manifest (Files to Create and Extend)

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## Files to create

| File | Purpose | WO |
|---|---|---|
| `faculties/dream/sleep_cycle.py` | Multi-cycle schedule, intensity, phase state machine | WO-DREAM-002 |
| `faculties/dream/dream_input.py` | Dream Input Field, emotional parser, memory gravity | WO-DREAM-003 |
| `faculties/dream/dream_work.py` | Seeds, condensation, displacement, symbolic transformation, Dream World | WO-DREAM-004 |
| `faculties/dream/prompt_builder.py` | 12-field structured prompt generator | WO-DREAM-005 |
| `tools/dream_fx.py` | CompositionDesigner FX pipeline (blob tracking, datamosh, VCR, summagator) | WO-DREAM-006 |
| `faculties/dream/layer_compositor.py` | Multi-frame layering engine, blend modes, emotional weighting | WO-DREAM-007 |
| `faculties/dream/dream_review.py` | Wake transfer gate, two output channels | WO-DREAM-009 |
| `faculties/dream/symbol_history.py` | Recurring symbol tracking and evolution | WO-DREAM-011 |

## Files to extend

| File | Change | WO |
|---|---|---|
| `faculties/dream/dream_faculty.py` | Wire all phases; replace single-cycle with multi-cycle; extend journal schema | WO-DREAM-002 through WO-DREAM-009 |
| `tools/image_gen_agent.py` | Fix silent failure (DREAM-1); multi-scene generation; call dream_fx | WO-DREAM-006 |
| `server.py` (Executive) | Write dream_phase/dream_intensity to blender_state.json; wire dream review to wake | WO-DREAM-010 |
| `core/health_battery.py` | Wire restore on wake_from_dream | WO-DREAM-012 |

---

## BUILDER RESULT — 2026-09-27 / 28

**Status:** ALL FILES DELIVERED
**Evidence:** `engineering/evidence/DREAM/` (three evidence files)

### Files to create — status

| File | Commit | Status |
|---|---|---|
| `faculties/dream/sleep_cycle.py` | `a2331e2` | DONE |
| `faculties/dream/dream_input.py` | `44340fb` | DONE |
| `faculties/dream/dream_work.py` | `6e76b89` + `5ad7016` | DONE |
| `faculties/dream/prompt_builder.py` | `74f8f71` | DONE |
| `tools/dream_fx.py` | `f877ff3` | DONE |
| `faculties/dream/layer_compositor.py` | `cc9ea5b` | DONE |
| `faculties/dream/dream_review.py` | `193e68b` | DONE |
| `faculties/dream/symbol_history.py` | `2701c39` | DONE |

### Files to extend — status

| File | Commit | Status |
|---|---|---|
| `faculties/dream/dream_faculty.py` | `4175cdf` + `7ed8dc2` | DONE — all phases wired |
| `tools/image_gen_agent.py` | `2266ac0` | DONE — `generate_dream_scene()` added |
| `server.py` | `55c7bd7` + server.py:1088/1094 | DONE — dream fields written, wake wired |
| `core/health_battery.py` | server.py:1094 | DONE — `on_wake_from_dream` wired |

All 8 files to create exist. All 4 files to extend are wired. No file in the manifest is undelivered.

Builder 1 · 2026-09-28
