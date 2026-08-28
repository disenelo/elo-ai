# FROM BUILDER → BOARD — WO-PRES-004: Failed Navigation Outcome Chain
**Date:** 2026-08-28
**Commit:** 84aebe1
**Authority:** WO-PRES-004 — SPEC_PRES_NAVIGATION_2026-08-24.md §PRES-004 — SPECIFIED + RATIFIED David L3

---

## AT Results — 10/10 PASS

```
~/miniconda3/bin/python3 -m pytest tests/test_wo_pres004_failed_navigation.py -v
10 passed in 0.11s
```

| AT | Description | Result |
|---|---|---|
| AT-1a | `handle_navigate(reachable=False)` → `navigation_failed` outcome dict | ✅ PASS |
| AT-1b | Success path (reachable=True) unmodified — still returns movement intent | ✅ PASS |
| AT-1c | No nav signal + reachable=True → still None (backward compat) | ✅ PASS |
| AT-2 | `[NAVIGATION_FAILED]` block distinct from `[NAVIGATE_OUTCOME]` in server.py | ✅ PASS |
| AT-3 | `_PENDING_MOVE["active"] = False` in failure branch — one-shot, no loop | ✅ PASS |
| AT-4a | `reachable=False` does not crash for any goal_win_id value | ✅ PASS |
| AT-4b | `[EVALUATE_BEAT]` settle directive inside `[NAVIGATION_FAILED]` block | ✅ PASS |
| AT-5a | `record_capability_result` called in NAVIGATION_FAILED branch in server.py | ✅ PASS |
| AT-5b | `record_capability_result` importable with required params | ✅ PASS |
| AT-5c | `record_capability_result(succeeded=False)` writes JSONL record | ✅ PASS |

---

## Deliverables

| Deliverable | File | Change |
|---|---|---|
| D-1 `navigation_failed` outcome | `runtime/backend_router.py:125` | `handle_navigate()` gains `reachable: bool = True`; `reachable=False` → `{"outcome": "navigation_failed", "reason": "no_reachable_route", "goal_win_id": ...}` |
| D-2 Executive trigger | `server.py:3387` | Distinct `[NAVIGATION_FAILED]` context block with `[EVALUATE_BEAT]` — Executive reads as settle directive, not re-attempt |
| D-3 One-shot, no loop | `server.py:3407` | `_PENDING_MOVE["active"] = False` in FAILED branch — clears pending move immediately |
| D-4 CAP-001 chain | `server.py:3411-3422` | `record_capability_result(capability="navigate", succeeded=False, failure_reason="no_reachable_route")` |

---

## Constraints Verified

- `executive.py` not modified (LAW-017) ✅
- Additive to existing success path — ARRIVED/FELL paths unchanged ✅
- No animation or visual definition — Design's parallel deliverable ✅
- NAV-013 success path (`test_wo_nav013_navigate_handler.py`) still 5/5 PASS ✅

---

## Board Consequence

WO-PRES-004 DONE. Board to MT-verify and close.

*Builder · 2026-08-28*
