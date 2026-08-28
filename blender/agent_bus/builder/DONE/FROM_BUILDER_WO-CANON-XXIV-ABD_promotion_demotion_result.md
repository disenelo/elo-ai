# FROM BUILDER → BOARD — WO-CANON-XXIV §A/B/D: Knowledge graph promotion, demotion, epistemic kind
**Date:** 2026-08-28
**Commit:** 59258be
**Authority:** WO-CANON-XXIV (AMENDED + RE-OPENED 2026-08-13) · Builder (Python) · P3 Tier B
**Gate satisfied:** "Blocked by: none for §A/§B/§D" per WO

---

## AT Results — 14/14 PASS + 5/5 regression PASS

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_canon_xxiv_promotion.py -v`

| Test | Description | Result |
|---|---|---|
| PT-1 | strength>=0.70 + 3 refs (2 sessions, 2 verified) → promoted_memory node written | ✅ PASS |
| PT-2 | All text-only (verified=False) → never promotes | ✅ PASS |
| PT-3 | promotion_pass/demotion_pass not called from server.py or spine.py | ✅ PASS |
| PT-4 | about_world=False → never promotes directly | ✅ PASS |
| DT-1 | 3 consecutive contradictions → retracted (>=3 = retract threshold) | ✅ PASS |
| DT-2 | Retracted node excluded from retrieve() | ✅ PASS |
| DT-3 | david_correction() → immediate retraction with reason="david_correction: ..." | ✅ PASS |
| DT-4 | Retracted node preserved: retracted_at + reason + original evidence intact | ✅ PASS |
| DT-5 | Consolidation refuses to demote authored fact (epistemic_kind="fact") | ✅ PASS |
| DT-6 | Re-promotion of retracted id skipped — must re-earn §A bar independently | ✅ PASS |
| AG-1 | Constants agree with LEARNING_LOOP_v1.md §3.4 (0.70/0.50/0.20/3/60d) | ✅ PASS |
| KT-1 | epistemic_kind distinct from type; fact/pm empty evidence rejected; perspective OK | ✅ PASS |
| KT-2 | check_referential_integrity() detects dangling from/to | ✅ PASS |
| KT-3 | build_context() returns "" on no match — no LLM backfill | ✅ PASS |

**Regression:** `python3 tests/test_canon_xxiv_world_graph.py` — 5/5 PASS (AT-0 through AT-4)
**Regression:** `pytest tests/test_canon_xxvii_governance.py` — 7/7 PASS

---

## Deliverables

| Location | Change |
|---|---|
| `memory/consolidation_faculty.py` | Added `import json`; added `promotion_pass()`, `demotion_pass()`, `david_correction()`; threshold constants `_KG_*` matching LEARNING_LOOP_v1.md §3.4 |
| `knowledge/graph_loader.py` | `retrieve()` entity results: `kind` now returns `epistemic_kind` (not ontology type); ontology type in new `type` field; contested/retracted excluded from retrieval; added `validate_graph_write()`, `check_referential_integrity()` |
| `tests/test_canon_xxiv_promotion.py` | New — 14 tests (PT-1/4, DT-1/6, AG-1, KT-1/3) |

---

## Constraints Verified

- Promotion runs timed-only — not callable from server.py/spine.py response path ✅
- Authored facts (epistemic_kind="fact") refused by demotion_pass and david_correction ✅
- Retracted nodes kept with full provenance (reason + retracted_at + evidence[]) — nothing deleted ✅
- Threshold constants agree with LEARNING_LOOP_v1.md §3.4 ✅
- Existing AT-0 through AT-4 (world graph tests) unaffected ✅
- XXVII governance tests unaffected ✅
- `relationships/world_graph.json` NOT modified (schema fields added at write time only) ✅

---

## Scope Not Covered (§C — Architect lane)

- §C: Cross-reference doc update in `docs/architecture/Volume_XXIV/03_Compression_and_Reasoning_Support.md` §3.4 and `LEARNING_LOOP_v1.md` §3.4 — **Architect lane**. Not Builder work.
- Vol VIII Consolidation timed wiring (promotion_pass host) — existing `consolidate()` is the host; promotion_pass is callable from it at session-close. No separate wiring WO needed.

---

## Board Consequence

WO-CANON-XXIV §A/B/D DONE. The promotion threshold exists as numbers in code, enforced by Consolidation only, timed only, verified-only, with mandatory provenance. The demotion/retraction/David-correction path exists and is behaviourally real. Epistemic `kind` is a distinct field; contested/retracted excluded from grounding. Board to MT-verify and close. §C (Architect cross-reference) remains open — Architect lane.

*Builder · 2026-08-28*
