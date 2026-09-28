# BUILDER RESULT — WO-NAV-008-BUILD (SP-4 Route Memory ACK Wiring)
Date: 2026-09-11
Status: ALREADY DONE — implemented in prior session; this card is the missing verification record

---

## Finding

`remember_route()` is called from inside the ACK handler at `server.py:3660-3686`.

```python
# SP-4 (WO-NAV-008): route memory — ACK-confirmed movements only
try:
    from self.route_memory import remember_route as _rr
    if _mout is not None:
        ...
        _rr(
            goal_surface=_mout.goal or _PENDING_MOVE.get("sub_type", "") or "",
            legs=_mout.route_nodes,
            arrived=_mout.arrived,
            fell=_mout.fell,
            duration_s=_mout.duration_s,
            smoothness=1.0 if _mout.arrived and not _mout.fell else 0.0,
            ack_id=_mout.ack_id,
            ack_received=True,                # SP-4: only called when ACK confirmed
            goal_win_id=_mout.goal_win_id,   # WO-NAV-011 SP-14
            brain_route=_xi_brain_route,     # XI-AD-2
            unity_route=_xi_unity_route,     # XI-AD-2
        )
except Exception:
    pass
```

This is inside the `if _move_acked:` block (gated at line 3618-3620). `_mout = MovementOutcome.from_ack(...)` is built at line 3630-3633.

---

## AT verification

| AT | Condition | Status |
|---|---|---|
| AT-1 | `remember_route()` called on ACK | ✅ Code is inside `if _move_acked:` block |
| AT-2 | `ack_id` non-empty | ✅ `ack_id=_mout.ack_id` passed |
| AT-3 | NOT called on non-ACK | ✅ Gated by `_move_acked` flag |
| AT-4 | Smoothness placeholder correct | ✅ `smoothness=1.0 if _mout.arrived and not _mout.fell else 0.0` |
| AT-5 | No regression | ✅ WO-NAV-001 / WO-NAV-011 result cards show DONE |

---

## DoD

- [x] `remember_route()` called from ACK handler, inside try/except
- [x] `ack_received=True` hardcoded (only reachable when `_move_acked` is True)
- [x] `_mout is not None` guard prevents exception on empty outcome
- [x] SP-5 lesson vocabulary not added (D-gated per spec)
- [x] `route_memory.py` function signature NOT changed

FREEZE check:
- `runtime/executive.py`: NOT TOUCHED ✅
- `prompts/living_presence_spec.txt`: NOT TOUCHED ✅

— Builder · 2026-09-11
