# FROM BUILDER — WO-NAV-011 Route Confidence by Win ID
**Seat:** Builder  
**WO:** WO-NAV-011 — SP-14 (route_confidence_by_win_id)  
**Date:** 2026-08-27  
**Authority:** Released by Architect 2026-08-27 (WO-NAV-008 done — SP-4 ACK wiring complete)

---

## D-1 — SP-14: route_confidence_by_win_id() ✅

`self/route_memory.py`:
```python
def route_confidence_by_win_id(target_win_id: int, route_history: list) -> float:
    """SP-14: arrivals/attempts for records where goal_win_id == target_win_id."""
```

Formula: `arrivals / attempts` for matching records.  
- No matching records → `0.5` (neutral prior)  
- All failed → `_EPSILON = 0.01` (non-zero floor, stays in candidate set)  
- All succeeded → `1.0`  

---

## D-2 — goal_win_id added to remember_route() ✅

`self/route_memory.py` — `goal_win_id: int | None = None` added as optional backwards-compatible parameter.  
Stored in record as `"goal_win_id": int(goal_win_id) if goal_win_id is not None else None`.

---

## D-3 — server.py ACK call passes goal_win_id ✅

`server.py` SP-4 (WO-NAV-008) call updated:
```python
goal_win_id=_mout.goal_win_id,  # WO-NAV-011 SP-14
```

Directional moves with no win_id target → `goal_win_id=None` recorded as `null`. No-op for SP-14 lookup.

---

## ATs — 7/7 PASS ✅

```
python3 -m pytest tests/test_wo_nav011_route_confidence_win_id.py -v
7 passed in 0.06s
```

AT-1 no history → 0.5 ✅  
AT-2 no matching win_id → 0.5 ✅  
AT-3 all arrivals → 1.0 ✅  
AT-4 all failures → epsilon (not 0.0) ✅  
AT-5 mixed 2/4 → 0.5 ✅  
AT-6 records without goal_win_id not counted ✅  
AT-7 remember_route records goal_win_id to JSONL ✅  

---

## Note on WO-NAV-012 gate

WO-NAV-012 (SP-13 candidate_surfaces in world_dict + SP-25/26) issues when WO-NAV-010 AND WO-NAV-011 are both complete. Both are now done.

*Builder · 2026-08-27*
