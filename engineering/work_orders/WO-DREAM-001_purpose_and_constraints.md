# WO-DREAM-001 — Dream Faculty: Purpose and Constraints

**Status:** OPEN — P0 CLEARED 2026-09-26
**Priority:** P1 | **Assigned:** Builder 1 | **Authored:** 2026-09-27 (David L3)
**Source:** engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md

---

## Purpose

Build the complete Dream Faculty as defined by the canonical source. Dream State is eLo's offline generative period in which experiences, memories, relationships, patterns, emotions and unfinished ideas are recombined into new associations, hypotheses and creative artefacts, with all dream-derived material remaining distinguishable from verified knowledge and waking experience.

The artwork is what the dream leaves behind.

---

## What must NOT happen

- Dream material silently written as fact. Every output tagged: `DREAM / HYPOTHESIS / CREATIVE ASSOCIATION`
- Dream Faculty speaking directly to David on wake. Executive routes what surfaces.
- Prompt generation that summarises rather than transforms. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
- Single image per dream. The architecture generates scenes per REM cycle, then composites them.

---

## Canonical source

`docs/architecture/_intake/SOURCE_2026-09-22_DAVID_eLo_DREAM_STATE_COMPLETE_ARCHITECTURE.md` (CANONICAL — verbatim, do not paraphrase)

**Supersedes:** DREAM-1, DREAM-2, DREAM-3, DREAM-4 briefs (all previous dream specs fold into this WO family)

---

## BUILDER RESULT — 2026-09-27/28

**Status:** BUILT + UNIT TESTED — LIVE VERIFIED (pipeline run)
**Evidence:** `engineering/evidence/DREAM/WO-DREAM-001-005_pipeline_core_evidence.md`

### Epistemic class constraints — confirmed

All dream outputs carry `HYPOTHESIS`, `SYMBOLIC`, or `SOURCE_ATTRIBUTED` epistemic class via `dream_review.py`. The `review()` function confirms `epistemic_class='HYPOTHESIS'` in live evidence (not `FACT`/`VERIFIED`). Dream Faculty does not write to long-term memory directly — wake transfer gate (`dream_review.py::DreamReview.retained`) holds all outputs until threshold met.

### Dream material not silently written as fact — confirmed

The `review()` output shows `retained=False` for outputs below significance threshold. No dream output reaches the Executive without going through the review gate.

### Single-image prohibition — confirmed

`layer_compositor.py` composites multiple scenes per dream; `dream_fx.py` applied per scene. The architecture generates scenes per REM cycle then composites them — not a single image.

### Files delivered

| File | Commit |
|---|---|
| `faculties/dream/sleep_cycle.py` | `a2331e2` |
| `faculties/dream/dream_input.py` | `44340fb` |
| `faculties/dream/dream_work.py` | `6e76b89` + `5ad7016` |
| `faculties/dream/prompt_builder.py` | `74f8f71` |
| `faculties/dream/dream_review.py` | `193e68b` |
| `faculties/dream/layer_compositor.py` | `cc9ea5b` |
| `faculties/dream/symbol_history.py` | `2701c39` |
| `tools/dream_fx.py` | `f877ff3` |

**Not LIVE VERIFIED on the live server** — no dream has fired on the running DesktopBuddy instance. Unit-tested and pipeline-run (evidence file above). Board runs live verification.

Builder 1 · 2026-09-28
