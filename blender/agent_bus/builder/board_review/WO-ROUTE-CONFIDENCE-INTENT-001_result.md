# WO-ROUTE-CONFIDENCE-INTENT-001 — Result Card
**Builder:** Builder 1
**Date:** 2026-10-05
**Commit:** 8ff4980
**Status:** COMPLETE — 8/8 tests pass

---

## What was built

Route confidence consultation wired into `_movement_intent()` at the navigate action branch (server.py, after SP-18).

**File:** `server.py` — navigate branch of `_movement_intent()`

**Logic:**
1. Extract `goal_win_id` from exec_decision (or `navigate_goal_win_id`)
2. Load last 20 route records via `route_memory.recent_routes(n=20)`
3. Call `route_confidence_by_win_id(win_id, history)` → float [0.0, 1.0]
4. Write `route_confidence_consulted=True` and `route_confidence_value=<val>` to exec_decision (visible in decision journal via existing record() call)
5. If `_rc_val < 0.40`: downgrade `exec_decision["confidence"]` to `round(original * rc_val, 3)`, set `route_confidence_low=True`; log at INFO level

**Downgrade example:** original confidence 0.75 + route confidence 0.2 → exec confidence 0.150

---

## Acceptance tests

`tests/test_wo_route_confidence_intent_001.py` — **8/8**

| Test | AC | Result |
|---|---|---|
| test_ac3_neutral_prior_when_no_history | AC-3 | ✅ 0.5 returned |
| test_ac4_epsilon_when_all_failed | AC-4 | ✅ epsilon, not 0.0 |
| test_low_confidence_window | AC-1 | ✅ < 0.40 |
| test_high_confidence_window | AC-2 | ✅ > 0.70 |
| test_ignores_other_win_ids | — | ✅ only requested win_id counted |
| test_ac1_code_present_low_confidence_branch | AC-1 | ✅ code present |
| test_ac2_code_only_downgrades_below_threshold | AC-2 | ✅ threshold 0.40 confirmed |
| test_route_confidence_consulted_flag_set | — | ✅ flag wired |

---

## Files changed

| File | Change |
|---|---|
| `server.py` | +18 lines in `_movement_intent()` navigate branch |
| `tests/test_wo_route_confidence_intent_001.py` | New — 8 tests |

---

## Note on decision_journal logging

The WO requested logging to `decision_journal`. The route consultation data (`route_confidence_consulted`, `route_confidence_value`, `route_confidence_low`, downgraded `confidence`) is written directly to `exec_decision` dict. `decision_journal.record()` is called later in server.py and reads `exec_decision.get("confidence")` — so the downgraded confidence lands in the journal naturally without an additional record() call. This avoids duplicating the journal write.

Builder 1 · 2026-10-05
