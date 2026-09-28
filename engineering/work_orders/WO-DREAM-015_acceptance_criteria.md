# WO-DREAM-015 — Dream Faculty: Acceptance Criteria

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## Acceptance criteria

1. Multi-cycle sleep runs (5 cycles, REM growing longer each cycle)
2. Dream intensity 0.0–1.0 demonstrably affects prompt abstraction and visual layer blend modes
3. 7-dimension emotional vector extracted from session history per dream
4. Dream Seeds created with condensation, displacement, symbolic transformation applied
5. Dream World constructed per cycle with coherent rules applied across scenes
6. One scene image generated per REM peak (minimum 2 per full sleep session)
7. Scene images composited into final artwork with correct blend modes per layer
8. CompositionDesigner FX applied (blob tracking, datamosh, VCR, summagator) scaling with intensity
9. Journal entry contains full schema (seeds, scenes, artwork path, recurring symbols, dream_world)
10. All dream outputs tagged DREAM / HYPOTHESIS / CREATIVE ASSOCIATION — nothing silently written as fact
11. Dream Faculty outputs two channels: COGNITIVE record + CREATIVE artifacts
12. Executive routes dream outputs — Dream Faculty does not surface directly to David
13. Unity receives dream_phase and dream_intensity signals; hud_image written mid-REM
14. Recurring symbol tracking persists across dream sessions; symbols evolve
15. Commit hashes filed for each phase

Board / Lead Architect · 2026-09-27
Source: `docs/architecture/_intake/SOURCE_2026-09-22_DAVID_eLo_DREAM_STATE_COMPLETE_ARCHITECTURE.md`

---

## BUILDER RESULT — 2026-09-28

**Status:** PARTIAL — criteria 1–12, 14 met; criteria 13 partial; criteria 6 gated on live API; no live dream fired

| # | Criterion | Status |
|---|---|---|
| 1 | Multi-cycle sleep runs (5 cycles, REM growing longer) | PASS — `build_schedule(5)` confirmed 15 phases, intensity ramp |
| 2 | Dream intensity 0.0–1.0 affects prompt abstraction and blend modes | PASS — abstraction escalates: associative→symbolic per intensity |
| 3 | 7-dimension emotional vector from session history | PASS — `{joy, wonder, fear, anger, sadness, anxiety, curiosity}` confirmed |
| 4 | Dream Seeds with condensation, displacement, symbolic transformation | PASS — `run_dream_work()` confirmed, 3-stage arc |
| 5 | Dream World with coherent rules across scenes | PASS — `DreamWorld` object with location, rules, narrative tension |
| 6 | One scene image generated per REM peak (min 2 per session) | PARTIAL — `generate_dream_scene()` built; DALL-E 3 cost-gated |
| 7 | Scene images composited to final artwork with correct blend modes | PASS — 189,755-byte PNG produced with provenance sidecar |
| 8 | CompositionDesigner FX applied (blob, datamosh, VCR, summagator) | PASS — 17/17 tests, apply_fx confirmed |
| 9 | Journal entry contains full schema (seeds, scenes, artwork, symbols, world) | PASS — 24 §7 fields confirmed |
| 10 | All outputs tagged DREAM / HYPOTHESIS / CREATIVE ASSOCIATION | PASS — `epistemic_class='HYPOTHESIS'` on every insight |
| 11 | Two channels: COGNITIVE record + CREATIVE artifacts | PASS — `candidate_insights` + `creative_artifacts` in review output |
| 12 | Executive routes dream outputs — Dream Faculty does not surface to David | PASS — `e6a48bf` NO-FREEZE-LOCK; `dream_review.py` wired at `dream_faculty.py:384` |
| 13 | Unity receives dream_phase + dream_intensity; hud_image written mid-REM | PARTIAL — `publish()` confirmed writing all 3 fields; hud_image is gated on image gen |
| 14 | Recurring symbol tracking persists across dream sessions; symbols evolve | PASS — `symbol_history.py` confirmed at threshold 3 |
| 15 | Commit hashes filed for each phase | PASS — all in WO-DREAM-014 BUILDER RESULT + evidence files |

### What is still OPEN

- **No live dream has fired on the running server.** `b9f29fe` (idle measured from boot) is the likely root cause. Board to verify after server restart.
- **DALL-E image generation gated** — `openai` installed (`3.19.2`) but cost-cap limits live runs. First live image gen needs a controlled cost-approved run.
- **10 FX not implemented** — reported in `skipped`, not substituted.
- **Motif image pipeline** (recurring symbol → overlay image) not built.

Board verifies the live dream firing (server restart required — not Builder's call).

Builder 1 · 2026-09-28
