# FROM_BUILDER — WO-PRES-BUILD-001
**Status:** DONE — all 4 PRES specs already implemented (corrected audit verdict)
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Finding

All 4 PRES specs were already fully implemented. The audit agent raised this WO because it found spec cards in DONE with no matching result card — the implementation existed but was never confirmed. This card is the confirmation.

## PRES-001 — Run/Run-up Capability ✅ IMPLEMENTED

**Location:** `world/navigation.py:64-149` (WO-PRES-001 block)

Verified:
- `Candidate` dataclass has `requires_run_up: bool` and `route_nodes: list` fields (line 29-30)
- `generate_candidates()` accepts `run_capability` and `run_up_distance_px` params (line 64-66)
- Run-up candidate logic at lines 120-136: gap > jump_px but within `jump_px + run_up_bonus` (25%) → `requires_run_up=True`, `route_nodes=[run_on_current, jump(run_up=True)]`
- All 5 acceptance tests from spec pass in `tests/test_wo_nav010_candidate_generation.py`

## PRES-002 — Behind-Window Z-Order ✅ IMPLEMENTED

**Locations:** `server.py:154,1914,1943-1948` · `world/live_world_state.py:252,257-271,706` · `self/elo_self_model.py:179`

Verified:
- `_behind_window_id` global in server.py (line 154): `str | None`, set on Unity occlusion events (line 1943)
- Unity event handler writes to `blender/behind_window.json` (line 1946-1948)
- `LiveWorldState.behind_window_id` field (line 252): populated by `_resolve_behind_window()` which reads JSON if no explicit value
- `EloSelfState.behind_window_id: str | None = None` (line 179) — readable by Executive per turn
- `assemble_world_state()` passes `behind_window_id` through (line 706)
- Route leg types `move_behind` and `emerge_from` accepted by navigation planner (WO-PRES-005)

## PRES-005 — Alternative Route Evaluation ✅ IMPLEMENTED

**Location:** `world/navigation.py:163-end` (WO-PRES-005 block)

Verified:
- `evaluate_alternatives()` function exists with full 5-step evaluation ladder (lines 169-end)
- Ladder: DIRECT → INTERMEDIATE (≤3 candidates) → RUN-UP → WRAP → GIVE-UP
- Max 3 intermediates guard: `_MAX_INTERMEDIATES = 3` (line 166)
- `navigation_failed` sentinel: `_NAVIGATION_FAILED = {"outcome": "navigation_failed"}` (line 165)
- All 6 acceptance tests from spec pass in `tests/test_wo_pres_005_alternative_route.py`

## PRES-006 — SelfCapabilitySnapshot ✅ IMPLEMENTED

**Location:** `runtime/self_capability_snapshot.py`

Verified:
- `SelfCapabilitySnapshot` dataclass with all 8 fields: `jump_px`, `embodiment_scope`, `run_capability`, `run_up_distance_px`, `size_px`, `movement_speed_px_s`, `wrap_available`, `body_win_id`
- `build_snapshot(capability_set, spatial)` assembles per-turn snapshot from capability_set dict + elo_spatial dict
- Reads `body_rect_px[2]` for `size_px`; falls back to `capability_set["size_px"]` or 80.0

## Test results

```
32 passed in 0.49s
```

Tests covered:
- `tests/test_wo_pres_005_alternative_route.py` — PRES-005 acceptance tests
- `tests/test_wo_nav010_candidate_generation.py` — PRES-001 (run-up in candidate gen)
- `tests/test_wo_pres_003_planner.py` — PRES-002/003 planner integration
- `tests/test_wo_pres004_failed_navigation.py` — navigation_failed consequence chain

## No code change required

All 4 specs were already built. Result cards were never written. This card closes the audit gap.
