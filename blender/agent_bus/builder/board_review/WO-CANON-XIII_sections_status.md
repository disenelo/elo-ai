# WO-CANON-XIII — Sections Status
**Builder:** Builder 1
**Date:** 2026-10-05

---

## §A — additive route + issued_by on move_command
**Status: ✅ COMPLETE (commit f0e591d)**

`blender_bridge/state_writer.py` — `route` and `issued_by` fields forwarded into `move_command` when present. Backwards-compat guaranteed (SQ-1 ✅). Tests: 3/3 in `test_canon_xiii_spatial.py`.

---

## §B — Spatial Faculty core + shadow_plan
**Status: ✅ COMPLETE (commit 73598b9)**

`faculties/spatial/spatial_faculty.py` — Full spatial faculty: `build_map()`, `plan_route()`, `shadow_plan()`. Tests: 20/20 in `test_canon_xiii_spatial.py`.

`shadow_plan()` at line 444: plans a route, logs it, issues no move_command. This is the §B exit criterion — produces routes in shadow mode, logged and compared, driving nothing.

---

## §C — Parity proof (shadow vs. Unity local)
**Status: ⚠️ REQUIRES LIVE UNITY SESSION**

§C requires running `shadow_plan()` in parallel with Unity's `EloDesktopNav` local route selection during actual desktop traversal, then asserting no correct traversal differs between the two planners.

This cannot be done statically. Requires:
1. David's machine running DesktopBuddy.app (Unity)
2. Python server running with shadow_plan wired to log alongside Unity ACKs
3. At least 5 traversal events compared (perch, roam, drag, click-through, gun-runoff)

**Parity wire:** `shadow_plan()` already exists and logs. The wire-in point is in the server.py movement response path — before issuing a move_command, call `shadow_plan()` to log the Python selection, then let Unity's `EloDesktopNav` proceed normally. Compare logs post-session.

→ Board action required: confirm §C parity session scheduled.

---

## §E — Retire Unity's EloDesktopNav local route selection
**Status: ✅ DAVID L3 CLEARED (2026-10-05)**

David cleared Ruling D-XIII-1 on 2026-10-05. §E may proceed AFTER §C parity is confirmed.

Sequence: §C parity confirmed → demote `EloDesktopNav._route` from decider to executor → wire Python spatial output as the command source → verify eLo moves correctly on David's desktop.

Evidence to: `engineering/evidence/SPATIAL/WO-CANON-XIII_E_retirement.md`

---

## Summary

| Section | Status | Blocker |
|---|---|---|
| §A | ✅ COMPLETE | — |
| §B | ✅ COMPLETE | — |
| §C | ⚠️ PENDING | Live Unity session on David's machine |
| §E | L3 CLEARED | §C must confirm first |
