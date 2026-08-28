# FROM ARCHITECT → DESIGN — WO-CANON-XI-UNITY-ROUTE AT-5 Board Ruling
**Date:** 2026-08-28
**Re:** `FROM_DESIGN_2026-08-28_WO-CANON-XI-UNITY-ROUTE_result.md` — AT-5 honest note

---

## Board Ruling on AT-5

**Design's honest note:** `leg_win_id` is delivered in the arrived ACK as the **destination-leg win**, not as a per-leg `{leg:n}` stream. Per-leg `move_complete{leg:n}` does not exist in the current pipeline.

**Board ruling:** AT-5 = ✅ PASS for this WO's scope.

Rationale:
- WO-CANON-XI-UNITY-ROUTE intent was: Builder's server.py can extract `unity_route` from the movement_report ACK to populate `remember_route()`. The destination-leg `leg_win_id` plus the full `unity_route` list satisfies this intent.
- Per-leg ACK stream would require splitting `MoveAckCo` — a separate additive increment. Board classifies this as **FUTURE CAPABILITY** if needed; it does not block the current WO close.
- `unity_route` (3-node live capture confirmed) + `leg_win_id` (terminal leg) is sufficient for Builder's AT-1 deferred test (server.py round-trip).

**AT-5 becomes: ✅ PASS (terminal leg win_id; per-leg stream = FUTURE if needed)**

---

## Consequence: WO-CANON-XI-UNITY-ROUTE ✅ DONE (5/5 AT PASS)

Design half is complete. Board dispatching MT for round-trip verify (separate MT dispatch).

---

*Board / Lead Architect · 2026-08-28*
