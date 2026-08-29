# WO-PRES-003-PLANNER — Bottom→Top Wrap as Navigation Route Leg

**From:** Board / Lead Architect — 2026-08-28
**Priority:** P1
**Gate:** None — all gates cleared (NAV-013 ✅ · DM-2/DM-3 ✅)
**Full WO spec:** `engineering/work_orders/WO-PRES-003-PLANNER.md`

**Authority:** PRES-003 RATIFIED David L3 2026-08-24 · RTR-055
**David L3 verbatim (2026-08-28):** "if he can't get to the window with a jump he jumps down from the bottom to the top, and then jumps or walks-and-jumps to the other window top"

---

## What to do

In `handle_navigate()` candidate generation: when target is outside direct jump reach, add a candidate route with `{"type": "wrap_bottom_to_top"}` as the first leg (drop off bottom → re-enter at screen top same x), then walk/jump to the target.

- Use live `capability_set.jump_px` from `elo_spatial.json` — NOT hardcoded value
- If direct OR wrap-via-top reaches target → include it in route
- If NEITHER works → `navigation_failed` (PRES-004 — already built)
- Move command `route` field must include wrap leg so Unity knows to execute the WO-075 drop-wrap

**5 ATs** — see full WO spec.

**Return:** `blender/agent_bus/builder/DONE/FROM_BUILDER_WO-PRES-003-PLANNER_result.md` · 5/5 PASS · commit hash
