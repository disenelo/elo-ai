# FROM BUILDER → BOARD — WO-PRES-003-PLANNER: wrap_bottom_to_top route leg
**Date:** 2026-08-28
**Commit:** 2afc687
**Authority:** WO-PRES-003-PLANNER · Builder (Python) · P1
**Gate satisfied:** NAV-013 ✅ · DM-2 ✅ · DM-3 ✅ (all per WO)

---

## AT Results — 5/5 PASS + 5/5 NAV-013 regression PASS

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_wo_pres003_planner_wrap_route.py -v`

| AT | Description | Result |
|---|---|---|
| AT-1 | gap_px(500) > jump_px(100) → route[0].type == "wrap_bottom_to_top", from_win_id == body_win_id | ✅ PASS |
| AT-2 | gap_px(50) <= jump_px(200) → no "route" field (direct path preferred) | ✅ PASS |
| AT-3 | jump_px=0 → outcome == "navigation_failed", reason == "no_reachable_route" | ✅ PASS |
| AT-4 | jump_px=10, gap_px=50 → wrap route added (confirms live jump_px, not hardcoded) | ✅ PASS |
| AT-5 | route JSON-serialisable; route[0].type == "wrap_bottom_to_top"; route[1].goal_win_id == 999 | ✅ PASS |

**Regression:** `pytest tests/test_wo_nav013_navigate_handler.py` — 5/5 PASS (AT-2 unaffected — route field present but not asserted absent)

---

## Deliverables

| Location | Change |
|---|---|
| `runtime/backend_router.py` | `_ELO_SPATIAL_PATH` constant; `_read_spatial_for_nav(_elo_spatial_path=None)` helper; `_directly_reachable(body, goal, edges, jump_px)` helper; `handle_navigate()` extended with `_elo_spatial_path` kwarg + wrap route candidate block |
| `tests/test_wo_pres003_planner_wrap_route.py` | New — 5 ATs with injected spatial JSON stubs |

---

## Constraints Verified

- D-3 satisfied: jump_px read LIVE from `elo_spatial.json` capability_set each call — never hardcoded ✅
- `executive.py` NOT touched (FREEZE_V1_LOCK) ✅
- NAV-013 AT-2 (`handle_navigate({"goal_win_id": 7})` → name="move", goal_win_id=7) still passes ✅
- `elo_spatial.json` unreadable → graceful fallback, original intent emitted (no crash) ✅
- No locomotion changes (D-5 scope) ✅

---

## Behaviour Summary

When `goal_win_id` is set in the Executive navigate decision:

1. `elo_spatial.json` is read live to get `(body_win_id, edges, jump_px)`.
2. **Direct path:** if an edge `from=win-{body}` → `to=win-{goal}` exists with `gap_px <= jump_px` → emit intent with no route field.
3. **Wrap path:** if not directly reachable and `jump_px > 0` → emit intent with `route = [{type: wrap_bottom_to_top, from_win_id, to_position: screen_top_same_x}, {type: jump, goal_win_id}]`.
4. **No capability:** if `jump_px <= 0` → return navigation_failed outcome dict.
5. **Spatial unavailable:** if elo_spatial.json unreadable → fall through, emit original intent (no route).

Directional (`type`, `direction`) nav calls are unaffected by this change.

---

## Board Consequence

WO-PRES-003-PLANNER DONE. The wrap_bottom_to_top route leg now lives in the Python planner layer. The locomotion layer (Unity / Design) already has the physical wrap implemented (WO-075 + 2026-08-27 roam fixes). Board to MT-verify and close. No follow-on WO required from Builder for this item.

*Builder · 2026-08-28*
