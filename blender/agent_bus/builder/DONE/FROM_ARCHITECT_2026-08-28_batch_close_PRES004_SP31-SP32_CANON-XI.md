# FROM ARCHITECT → RECORD — Batch Close: WO-PRES-004 + WO-PRES-004B + WO-SP31-SP32 + WO-CANON-XI
**Date:** 2026-08-28
**Authority:** Board / Lead Architect — independent source verification + live test run

---

## WO-PRES-004 ✅ ARCHITECTURALLY CLOSED

**Claim:** `handle_navigate(reachable=False)` returns `navigation_failed` outcome; `[NAVIGATION_FAILED]` block distinct from `[NAVIGATE_OUTCOME]` in server.py.

**Evidence:**
- Builder result card: `FROM_BUILDER_WO-PRES-004_result.md` — 10/10 PASS (commit 84aebe1)
- Board live run: `~/miniconda3/bin/python3 -m pytest tests/test_wo_pres004_failed_navigation.py tests/test_wo_pres004b_nav_fail_state_write.py -q` → **14/14 PASS**
- FREEZE_V1_LOCK clean: change is in backend_router.py, not executive.py.

---

## WO-PRES-004B ✅ ARCHITECTURALLY CLOSED

**Claim:** `nav_fail` + `nav_fail_ts` written to blender_state.json from the `[NAVIGATION_FAILED]` handler.

**Evidence:**
- Builder result card: `FROM_BUILDER_WO-PRES-004B_AT6_result.md` — 4/4 PASS (commit 0c7b899)
- Board live run: included in the 14/14 PASS above.
- Covered by same test batch.

---

## WO-SP31-SP32 ✅ ARCHITECTURALLY CLOSED

**Claim:** `runtime/self_initiation.py` implements ATTENDING detection (A1/A2/A3) + HARD-QUIET detection (Q1-Q4) + SP-32 autonomous spine call path.

**Evidence:**
- Builder result card: `FROM_BUILDER_WO-SP31-SP32_self_initiation_gate_result.md`
- Board live run: `~/miniconda3/bin/python3 -m pytest tests/test_sp31_sp32_self_initiation.py -q` → **13/13 PASS**
- FREEZE_V1_LOCK clean: `runtime/self_initiation.py` (new module) — executive.py untouched.

---

## WO-CANON-XI (§A/§D Builder side, Step 2) ✅ ARCHITECTURALLY CLOSED

**Claim:** `route_memory.jsonl` records `brain_route` + `unity_route` parity fields (commit 4957515).

**Evidence:**
- Builder result card: `FROM_BUILDER_WO-CANON-XI-STEP2_parity_fields_result.md` — 5/5 PASS
- Board live run: `~/miniconda3/bin/python3 -m pytest tests/test_wo_canon_xi_step2_parity_fields.py -q` → **5/5 PASS**
- MT dispatch for Unity round-trip: `FROM_ARCHITECT_2026-08-28_MT_dispatch_CANON-XI_round_trip.md` (AT-D1 through AT-D5).
- Board ruling AT-5: terminal `leg_win_id` is sufficient — per-leg stream = FUTURE CAPABILITY.

**Note:** MT round-trip verification (AT-D1–D5) still pending return. Python Builder side confirmed.

---

*Board / Lead Architect · 2026-08-28*
