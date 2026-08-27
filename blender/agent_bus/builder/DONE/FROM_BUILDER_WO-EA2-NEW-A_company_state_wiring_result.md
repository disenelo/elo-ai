# FROM_BUILDER — WO-EA2-NEW-A Result Card
**WO:** WO-EA2-NEW-A — Company State → One Brain Cognitive Wiring  
**Seat:** Builder  
**Date completed:** 2026-08-27  
**Authority:** David L3 — Initiative 01  
**Status:** ⏳ IN_REVIEW — evidence complete, awaiting Board/LA architectural close

---

## Deliverables

**D-1 — Read `blender/company_state.json` in world state assembly**  
File: `world/live_world_state.py`  
- Added `_COMPANY_STATE_PATH` constant pointing to `blender/company_state.json`.
- Added reading block in `assemble_world_state()`: reads file, extracts only the 6 programme-state fields (`today_priorities`, `waiting_for_approval`, `blocked`, `roadmap`, `board`, `voiced_briefing`).
- Fault-tolerant: absent file or malformed JSON returns `{}`, never raises.
- `money` and `seats_sample` excluded (Board ruling required before LLM exposure).

**D-2 — `LiveWorldState` field**  
File: `world/live_world_state.py`  
- Added `company_state: dict = field(default_factory=dict)` to `LiveWorldState` dataclass.
- Pattern matches `capability_results`, `surface_edges`, `win_id_to_surface` — additive only.

**D-3 — `attention_in` inclusion in spine**  
File: `runtime/spine/spine.py`  
- Added `"company_state": dict(getattr(world, "company_state", {})),` to `_attention_in["world_state"]` dict.
- One-line addition following the `capability_results` pattern at that same block.
- `executive.py` not touched (FREEZE_V1_LOCK / LAW-017 confirmed).

---

## Acceptance Test Results

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_wo_ea2_new_a_company_state_wiring.py -v`  
Date confirmed: 2026-08-27

| AT | Description | Result |
|----|-------------|--------|
| AT-1 | `LiveWorldState` has `company_state` field (dict, default `{}`) | ✅ PASS |
| AT-2 | `assemble_world_state()` populates with required keys from valid file | ✅ PASS |
| AT-3 (×2) | Absent file → `{}` no crash; malformed JSON → `{}` no crash | ✅ PASS |
| AT-4 | `attention_in["world_state"]["company_state"]` present after spine turn | ✅ PASS |
| AT-5 | `money` and `seats_sample` NOT in exposed company_state | ✅ PASS |
| AT-6 | `executive.py` syntax-clean, `spine.py` is wiring point (not executive.py) | ✅ PASS |

**7/7 PASS**

---

## Regressions

- `test_wo002_live_world_state.py` — 6/6 PASS (live_world_state direct coverage)
- `test_wo014_spine_wiring.py` — 5/5 PASS (spine wiring direct coverage)

---

## What was NOT done (non-scope)

- `executive.py` not modified (FREEZE_V1_LOCK).
- No capability registration for `company.*` intents (that is WO-EA2-2, Gap B).
- `voiced_briefing` not passed as direct LLM output — available in structured data only; eLo synthesises.
- `money` and `seats_sample` not exposed (Board ruling required).

---

## Board/LA Close Criteria (from WO)

Board/LA independently confirms:
- `company_state` key present in `attention_in["world_state"]` after a live turn, containing fields from `company_state.json`.
- `executive.py` diff empty.

This WO provides the world-state foundation for WO-EA2-2's `company.*` voice intents.

---

*Builder Seat · 2026-08-27 · WO-EA2-NEW-A Gap A · David review: ☐ APPROVE (→ DONE)  ☐ LOOP BACK:*
