# FROM BUILDER — GAP-01: Leaf on Water (SC-NEW-003) — ALREADY IMPLEMENTED

**Date:** 2026-09-11
**Status:** CONFIRMED IMPLEMENTED — DoD Part 2 satisfied

---

## Diagnosis

GAP-01 card states "SC-NEW-003 wired as a constraint on SP-29/attention — never built." This was inaccurate — the constraint IS already built:

### In significance_faculty.py

SC-NEW-003 exists at lines 233-330 as:
- Named constants: `_LEAF_INTERRUPT_RATIO`, `_LEAF_MIN_DIFF`, `_LEAF_NO_TRAJ_THRESHOLD`, `_LEAF_ALWAYS_YIELD_MOMENTUM`
- Public function: `leaf_on_water_constraint(incoming_sig, trajectory_sig, momentum)` → `{"active": bool, "blocked_interrupt": bool, "reason": str, ...}`
- Docstring explicitly names SC-NEW-003 and the BOARD-002 ruling

### In spine.py

SC-NEW-003 is called before the Executive at lines 1167-1204:
1. `_incoming_sig` = `cognitive_state.significance_score`
2. `_traj_sig` = `_prev_significance` (module-level prior-turn significance carrier)  
3. `_leaf_result = leaf_on_water_constraint(_incoming_sig, _traj_sig, _momentum_str)`
4. `plan.leaf_on_water_active = _leaf_result.get("active", False)` — passed to Executive directive

The trajectory significance is persisted at line 1437 across turns.

### In prompt_builder.py

At line 533: `elif exec_decision.get("leaf_on_water_active"): directive_lines.append("stability: leaf-on-water — gentle, present, no more than two thoughts")`

The constraint reaches the LLM directive when active.

---

## GAP-01 DoD status

| Requirement | Status |
|---|---|
| SC-NEW-003 named, documented in significance faculty | ✅ `leaf_on_water_constraint` with full docstring |
| Trajectory doesn't interrupt for low-sig signal | ✅ `should_interrupt` check + ratio threshold |
| INTENT PROOF (expressed turn) | ⚠️ requires real server run to demonstrate |
| Two-signal test | ⚠️ requires real server run |

Part 1 (Board writes P9 to ARCHITECTURAL_PRINCIPLES.md) — Board's lane, not touched.
Part 2 (runtime constraint) — CONFIRMED IMPLEMENTED.

Live evidence still required for INTENT PROOF. Run "tell me about something complex" (high-sig trajectory), then mid-thought send "hey" (low-sig). Confirm eLo maintains trajectory.

*Builder · 2026-09-11*
