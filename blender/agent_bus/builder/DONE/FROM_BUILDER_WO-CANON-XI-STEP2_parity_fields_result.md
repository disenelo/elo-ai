# FROM BUILDER → BOARD — WO-CANON-XI-STEP2: brain_route + unity_route parity fields
**Date:** 2026-08-28
**Commit:** 4957515
**Authority:** WO-CANON-XI-STEP2 · Board dispatch 2026-08-28 · P1
**Gate satisfied:** WO-FIX-PERCEPTION-0006 result card filed (commit 5b399a2)

---

## AT Results — 5/5 PASS

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_wo_canon_xi_step2_parity_fields.py -v`

| AT | Description | Result |
|---|---|---|
| AT-1 | `remember_route(..., brain_route=["win-1","win-2"], unity_route=["win-1","win-2"])` → both fields in JSONL | ✅ PASS |
| AT-2 | Omitted brain_route/unity_route → explicit `null` in JSONL (not missing keys) | ✅ PASS |
| AT-3 | `ack_received=False` → returns False, nothing written | ✅ PASS |
| AT-4 | Existing call signature (no new kwargs) → no TypeError | ✅ PASS |
| AT-5 | Parity plumbing: 2 entries (1 matched, 1 mismatched) → count=2, matched=1, rate=50% | ✅ PASS |

---

## Deliverables

| Location | Change |
|---|---|
| `self/route_memory.py` | Added `brain_route: "list | None" = None` and `unity_route: "list | None" = None` to `remember_route()` signature |
| `self/route_memory.py` | Added `"brain_route": brain_route` and `"unity_route": unity_route` to record dict |
| `tests/test_wo_canon_xi_step2_parity_fields.py` | 5 ATs — new file |

---

## Constraints Verified

- All existing parameters and their order preserved ✅
- All existing logic (ack gate, XDNA, append-only write) unchanged ✅
- No other file modified ✅
- Existing call sites require no changes (new params default to None) ✅

---

## Non-Scope Discovery (as specified in WO)

`server.py` ACK handler (~line 3345) calls `remember_route` but does not pass `brain_route` or `unity_route`. WO-CANON-XI-SERVER-ACK addresses this — gate is now open (STEP2 result card filed).

---

## Board Consequence

WO-CANON-XI-STEP2 DONE. XI-AD-2 parity field plumbing is in place. WO-CANON-XI-SERVER-ACK is now executable (its gate condition was STEP2 result card). Board to MT-verify and close.

*Builder · 2026-08-28*
