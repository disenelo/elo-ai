# FROM ARCHITECT → RECORD — WO-CONV-001: One Brain Convergence Architectural Close
**Date:** 2026-08-28
**Authority:** Board / Lead Architect — source verification across all 7 test items
**Gate satisfied:** All prerequisite WOs (WO-RS-001..004, WO-SPG-001..002, WO-WKG-001..004) in DONE

---

## WO-CONV-001 ✅ ARCHITECTURALLY CLOSED

**Objective:** Verify the signal path INPUT → CLASSIFY → WKG/SPG/MEMORY → CURRENT STATE → CAPABILITIES → EXECUTIVE → RESPONSE → LEARNING is wired, structured, and intact.

---

### Item 1: Input classifies correctly ✅
- `runtime/spine/spine.py` — `_attention_in` assembled from `attention_engine` with `intent`, `valence`, `momentum`; forwarded to `_exec_decide_fn` each turn.

### Item 2: WKG claim reaches Executive as ContextItem with epistemic_class ✅
- WO-WKG-004 closed (8/8 PASS, commit 816594b): `retrieve_wkg()` returns `ContextItem` records with `epistemic_class` field wired into the cognitive state each turn.
- Board/LA verified live 2026-08-27.

### Item 3: SPG self-state reaches Executive as structured data ✅
- `faculties/spatial/spatial_faculty.py` (555 lines, WO-CANON-XIII §B, 20/20 PASS).
- `runtime/spine/spine.py:337` — `company_state` in `_attention_in["world_state"]` (WO-EA2-NEW-A, 7/7 PASS).
- `self/elo_self_model.py` + `self/elo_self_state.json` — self-state structured and present each turn.

### Item 4: Memory retrieval reaches Executive as ContextItem ✅
- `self/lesson_store.py:440` — `recall()` returns confirmed lessons.
- `runtime/spine/spine.py:248-255` — `_ls_recall(context=..., k=3)` called each turn; result passed to `prompt_builder` via `lessons=_recalled_lessons`.
- Board/LA verified live 2026-08-28: 1 confirmed lesson in ledger; recall path live.

### Item 5: REVIEW_STATE blocks all writes end-to-end ✅
- WO-RS-001..004 all in DONE (epistemic_grounding, review_state_enforcement, identity_conflict_boundary, review_contamination).
- `test_one_brain_no_second_authority.py` — 6/6 PASS (Board live 2026-08-28). AT: `test_one_brain_p0_review_verdict_on_disk` confirms on-disk gate.

### Item 6: Response generated without provenance contamination ✅
- WO-GUARD-001 closed (6/6 PASS, commit d621ee1, Board/LA 2026-08-28): identity_guard → response_authority_guards → shadow_capture order confirmed server.py:4839/4844/4865.
- `test_one_brain_no_second_authority.py` AT5: `test_no_runtime_faculty_returns_exec_decision_dict` — 6/6 PASS.

### Item 7: Learning writes only where authorised ✅
- WO-095: `reflection_faculty.py` write side — lessons only on session_summary with significance gate.
- WO-096B: `promote_pass` every 10 turns — promotion requires 3+ distinct episode_refs, 2+ sessions, 2+ verified entries.
- `MemoryFaculty.submit()` (Vol VIII Invariant 7): all LTM writes route through single logical owner.
- WO-FIX-TESTDEFECTS-BATCH: store_interaction removed (commit 84758ea) — no unauthorized write path.

---

**Integration test — 6/6 PASS:** `~/miniconda3/bin/python3 -m pytest tests/test_one_brain_no_second_authority.py -v`

**Prerequisite result cards in DONE:** WO-RS-001, WO-RS-002, WO-RS-003, WO-RS-004, WO-SPG-001, WO-SPG-002 ✅

---

*Board / Lead Architect · 2026-08-28*
