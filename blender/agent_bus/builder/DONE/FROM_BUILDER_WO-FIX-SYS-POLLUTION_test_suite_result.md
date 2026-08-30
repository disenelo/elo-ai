# FROM BUILDER — WO-FIX-SYS-POLLUTION Test Suite Cause A

**Source:** `FROM_MT_2026-08-29_DEFECT_test_suite_sys_modules_pollution.md` — Cause A  
**Priority:** P1 (corrupts every AT verdict from the suite per MT)  
**Authority:** Programme goal — test suite integrity; MT explicitly identified Builder's files  
**Date:** 2026-08-30  
**Commit:** `3e1748b`

---

## What was fixed

`tests/test_wo025_spatial_sensor.py` and `tests/test_wo023_screen_position.py` were
registering incomplete stub packages at module level during pytest collection. These stubs
persisted for the entire test session, causing `ModuleNotFoundError` and `AttributeError`
in ~29 tests across 13 unrelated files (Cause A from MT's report).

**Root cause:** `sys.modules["blender_bridge"] = types.ModuleType("blender_bridge")` — a stub
without `__path__`; Python cannot find submodules through it. `sys.modules["blender_bridge.state_writer"]`
was a stub missing `.patch` and `.write`.

**Fix (both files):** Save originals before injection → inject stubs → exec_module → restore originals.
Real modules (`blender_bridge.state_writer`, `desktop.window_state`, `desktop.spatial_state`) import
cleanly from the repo. Lazy imports in test functions now get real modules.

## Verified

```
tests/test_wo025_spatial_sensor.py (8) + test_wo023 (10) + test_w0_ack_channel (7)
+ test_wo_mobile001 (5) → 30/30 PASS (was: 5 failures in ack_channel when run together)
```

## Cause B (separate — NOT fixed here)

MT's report also identified 101 real failures (not ordering-induced):
- WKG-001: `retrieve_wkg_context_items` function never implemented (23 failures)
- BWKG-02: eLo corpus claims never ingested (31 failures)
- Other smaller clusters (~47)

These require separate WOs with L3 authority. NOT in scope for this fix.

*Builder / Board — 2026-08-30*
