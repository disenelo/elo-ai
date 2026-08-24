# WO-NAV-008 — Route Memory ACK Wiring (SP-4)
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — SPEC ratification 2026-08-23 + Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Signal:** WO-NAV-001 VERIFIED (commit `b70916a`, 11/11 PASS)  
**Priority:** 🟠 HIGH — Wave 2. Ensures route memory records only confirmed movements.  
**RTR:** RTR-043 (route memory, SP-4)  
**SPEC basis:** SP-4 — `SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md`  
**Dependency:** SP-1, SP-2, SP-22 complete (WO-NAV-001). SP-5 schema is D-gated — placeholders allowed per EXECUTION_QUEUE_2026-08-24.md.

---

## Why now

`route_memory.remember_route()` currently runs independently of the ACK path — it records routes without confirmation that movement was physically acknowledged. This violates ADR-Exec-005: "Outcomes written ONLY on verified body ACK". The `ack_id` field exists in the schema but is never set from a real ACK event.

SP-4 fixes this: `remember_route()` is called from inside the confirmed movement ACK handler, receives `ack_id` from `MovementOutcome`, and is gated on `ack_received=True`. This makes route memory a consequence of confirmed physical movement, not an assumption.

---

## Deliverable — D-1: Call `route_memory.remember_route()` from ACK handler

**File:** `server.py`  
**Location:** The movement ACK handler, inside the `if _move_acked:` block (currently around lines 3080–3100). This is the same block that WO-NAV-002 D-1 is modifying — add this call AFTER the autobiography write.

**Pre-condition:** `_mout` (the `MovementOutcome` populated in WO-NAV-002 D-1) is available. WO-NAV-002 must run first OR the `MovementOutcome.from_ack()` call can be shared — Builder chooses the cleanest approach, ensuring `_mout` is available when this call executes.

**Call to add (inside the `try` block, after autobiography write):**

```python
# SP-4: route memory — ACK-confirmed movements only
try:
    from self.route_memory import remember_route as _rr
    _rr(
        goal_surface=_mout.goal or _PENDING_MOVE.get("sub_type", "") or "",
        legs=_mout.route_nodes,            # SP-5: lesson fields may be added later (D-gated)
        arrived=_mout.arrived,
        fell=_mout.fell,
        duration_s=_mout.duration_s,
        smoothness=1.0 if _mout.arrived and not _mout.fell else 0.0,  # [ESTIMATE] placeholder
        ack_id=_mout.ack_id,
        ack_received=True,                 # SP-4: only called when ACK is confirmed
    )
except Exception:
    pass
```

**Constraint notes:**
- `smoothness=1.0/0.0` is an `[ESTIMATE]` placeholder. SP-5 (lesson vocabulary) is D-gated — do not wait for it. Record smoothness as 1.0 on arrived, 0.0 on fell/failed. David will refine the scoring formula later.
- `legs=_mout.route_nodes` — this is the `route_nodes` list from the movement_report payload. It may be empty for directional moves (no graph-nav destination). That is correct — empty list is valid.
- `ack_received=True` is hardcoded here because this code is only reached when `_move_acked` is True.
- Keep the call inside a try/except so a route_memory failure never breaks the ACK handler.

---

## Forbidden scope

- Do not change `route_memory.py` function signature
- Do not add SP-5 lesson vocabulary content — D-gated; placeholders only
- Do not alter the `remember_route()` logic — only call it
- Do not change the ACK state machine beyond this one call
- WO-NAV-002 scope is separate — coordinate on `_mout` availability only

---

## Verification

| AT | SP | Description | Pass condition |
|---|---|---|---|
| AT-1 | SP-4 | `remember_route()` called on ACK | A simulated ACK sets `_move_acked=True`; route_memory log receives a new entry with `ack_received=True` |
| AT-2 | SP-4 | `ack_id` non-empty | Written record has `ack_id` matching `_mout.ack_id` (non-empty string) |
| AT-3 | SP-4 | NOT called on non-ACK | If `_move_acked` is False, no route_memory entry is written |
| AT-4 | SP-4 | Smoothness placeholder correct | `arrived=True, fell=False` → smoothness=1.0; `fell=True` → smoothness=0.0 |
| AT-5 | SP-4 | No regression | WO-NAV-001 AT-1 through AT-3 still pass |

---

## Required return evidence

1. Changed files — file path + line numbers
2. AT results — AT-1 through AT-5 pass/fail with one-line evidence
3. Commit hash
4. Blocker report if any (format per `SEAT_PROTOCOL_AMENDMENT_BLOCKER_SCOPE_2026-08-24.md`)

Return to: Board. On verified pass → Board notes RTR-043 updated and assesses WO-NAV-011 (SP-14 route_confidence — requires accumulating data).

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — SPEC ratification 2026-08-23 + Execution Directive 2026-08-24*
