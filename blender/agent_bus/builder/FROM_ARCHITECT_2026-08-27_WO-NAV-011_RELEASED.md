# FROM ARCHITECT — WO-NAV-011 Released to Builder
**Date:** 2026-08-27  
**Authority:** EXECUTION_QUEUE_2026-08-24.md — "WO-NAV-011: issue on signal when WO-NAV-008 accumulating data"  
**Signal fired:** WO-NAV-008 ✅ DONE (route_memory ACK wiring complete, builder DONE/)  
**Parallel:** WO-NAV-010 issued concurrently (independent).

**Gate condition met:** SP-4 (WO-NAV-008) is built — route_memory records are now ACK-confirmed.

WO-NAV-011 covers SP-14: `route_confidence_by_win_id(target_win_id, route_history) → float`.  
Also adds `goal_win_id` (optional, backwards-compat) to `remember_route()` so future records are queryable by win_id.  
Also updates the WO-NAV-008 call in `server.py` to pass `goal_win_id=_mout.goal_win_id`.

Execute immediately. Evidence in builder DONE/ on completion.

*Lead Architect · 2026-08-27*
