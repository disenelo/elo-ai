# FROM BUILDER → BOARD: WO-FIX-WKG-ISOLATION Result
**Date:** 2026-08-29
**WO:** WO-FIX-WKG-ISOLATION — Fix WKG test suite ordering dependency
**Implementation commit:** (this commit)

---

## Result: ✅ 3/3 PASS

| AT | Test | Result |
|---|---|---|
| AT-1 | `test_wkg_phase2.py` 82/82 in full suite (was 66 failures) | ✅ PASS |
| AT-2 | Full suite delta: no additional failures introduced | ✅ PASS |
| AT-3 | No implementation file modified — test_canon_xxiv_promotion.py only | ✅ PASS |

Test run: `~/miniconda3/bin/python3 -m pytest tests/ -q`

---

## Root cause

`tests/test_canon_xxiv_promotion.py` — one test's `finally` block restored only `{"entities": original_graph_entities, "relationships": []}` instead of the full `original_graph.copy()`. This left `knowledge.graph_loader._graph` without its `wkg_claims`, `wkg_sources`, `wkg_claim_relationships`, and other keys. Since `test_canon_xxiv_promotion.py` runs before `test_wkg_phase2.py` alphabetically, all 82 phase-2 tests that call `_gl._graph.get("wkg_claims", [])` received `[]`.

## Fix

`tests/test_canon_xxiv_promotion.py` line ~238: changed `finally: gl._graph = {"entities": original_graph_entities, "relationships": []}` to `finally: gl._graph = original_graph` (already captured at line 228 via `.copy()`).

No implementation files touched. `_wkg_meta`, `wkg_claims`, `wkg_sources`, `wkg_entities`, `wkg_claim_relationships` all now survive the test boundary.

*Board / Lead Architect acting as Builder · 2026-08-29*
