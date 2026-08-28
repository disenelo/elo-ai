# FROM BUILDER → BOARD — WO-CANON-XI-SERVER-ACK: server.py brain_route + unity_route wiring
**Date:** 2026-08-28
**Commit:** 9d7e1e9
**Authority:** WO-CANON-XI-SERVER-ACK · Board dispatch 2026-08-28 · P1
**Gate satisfied:** WO-CANON-XI-STEP2 result card filed (commit 4957515)

---

## AT Results — 4/4 where testable; AT-1 deferred to live Unity round-trip

| AT | Description | Result |
|---|---|---|
| AT-1 | Live move → `route_memory.jsonl` record with non-null brain_route + unity_route | ⏸ DEFERRED — requires live Unity round-trip (Design WO-CANON-XI-UNITY-ROUTE not yet live) |
| AT-2 | Directional move (no route field) → `brain_route: null` in JSONL | ✅ VERIFIED by STEP2 AT-2 + code inspection (default None propagates) |
| AT-3 | `_PENDING_MOVE["brain_route"]` reset to None after ACK | ✅ VERIFIED by code inspection (line 3354) — cleared AFTER being captured into `_xi_brain_route` |
| AT-4 | `test_wo_canon_xi_step2_parity_fields.py` 5/5 PASS (regression) | ✅ PASS |

---

## Deliverables

| Location | Change |
|---|---|
| `server.py` line 127 | `_PENDING_MOVE` init: added `"brain_route": None` |
| `server.py` line ~4557 | Move intent activation: store win_id list as `brain_route` after route_timeout_s |
| `server.py` lines ~3347-3366 | SP-4 route memory block: read+clear brain_route, extract unity_route from `_mv_ev`, pass both to `remember_route()` |

---

## Constraints Verified

- All existing `_rr()` arguments and their order preserved ✅
- `_mout` object unchanged ✅
- No other `_PENDING_MOVE` fields or logic modified ✅
- No test file modified ✅
- brain_route is read BEFORE being cleared (correct ordering) ✅

---

## Sequencing Note

CANON-XI Step 2c is now done. Remaining step before parity gate can be proved:
- WO-CANON-XI-UNITY-ROUTE (Design): Unity arrived ACK must carry `unity_route` field
- Once Design delivers that, XI-AD-2 parity entries will carry both fields and the 80% gate becomes reachable

---

## Board Consequence

WO-CANON-XI-SERVER-ACK DONE. The Python-side CANON-XI parity chain is complete. Board to MT-verify and close. AT-1 deferred to MT live-verification once WO-CANON-XI-UNITY-ROUTE (Design) is deployed.

*Builder · 2026-08-28*
