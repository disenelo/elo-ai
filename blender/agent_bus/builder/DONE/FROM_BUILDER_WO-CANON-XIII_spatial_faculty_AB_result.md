# FROM BUILDER → BOARD — WO-CANON-XIII §A+§B: Spatial Faculty (additive route + data model)
**Date:** 2026-08-28 (result card filed; implementations pre-date by prior sessions)
**Commits:** `f0e591d` (§A) · `73598b9` (§B)
**Authority:** WO-CANON-XIII · Builder (Python — `faculties/spatial/`, `blender_bridge/state_writer.py`)

---

## AT Results — 20/20 PASS

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_canon_xiii_spatial.py -v`

| Group | Tests | Result |
|---|---|---|
| §A (additive route + issued_by fields) | test_a1_route_and_issued_by_appear_when_supplied · test_a2_partial_intent_no_extras · test_sq1_no_route_byte_identical | ✅ 3/3 PASS |
| §B FTs (Spatial Faculty core logic) | test_ft1_gap_unreachable_margin_named · test_ft2_unreachable_routes_around · test_ft3_* (3 tests) · test_ft4_go_behind · test_ft5_* (2) · test_ft6_* (2) · test_ft7_* (2) | ✅ 12/12 PASS |
| §B STs + SQs (stale state + invariants) | test_sq3_no_rival_spatial_model · test_st1_* (2) · test_st2_* (2) | ✅ 5/5 PASS |

---

## Deliverables

### §A — additive `route` + `issued_by` on `move_command` (commit `f0e591d`)

| Location | Change |
|---|---|
| `blender_bridge/state_writer.py` (~line 190, 286) | `route` and `issued_by` fields forwarded from intent into `move_command` when present — additive only |

- Backwards-compat guaranteed: `move_command` with no `route` is byte-identical to pre-change behaviour (SQ-1 ✅)
- `issued_by = "SpatialFaculty"` is the only accepted issuer per Vol XIII Ch.1

### §B — Spatial Faculty data model + core logic (commit `73598b9`)

| Location | Change |
|---|---|
| `faculties/spatial/spatial_faculty.py` (NEW — 555 lines) | Full Gibson affordance set (15) · 12-verb movement grammar · `DesktopWorldMap` / `Surface` / `Affordance` / `BodySchema` / `Reachability` / `Route` / `RouteLeg` · `check_reachability()` · `plan_route()` · `shadow_plan()` · `_shadow_log()` · `context_block()` |
| `faculties/spatial/__init__.py` | Package init |
| `tests/test_canon_xiii_spatial.py` | 20 ATs (NEW) |

Shadow mode: `shadow_plan()` produces routes, logs to `blender/spatial_shadow.jsonl`, drives nothing. §D wires routes into `move_command`.

---

## Constraints Verified

- `executive.py` NOT touched (FREEZE_V1_LOCK) ✅
- §A is additive only — no existing traversal is altered ✅
- §B is read-only — issues no `move_command` (§D gate not yet opened) ✅
- `issued_by = "SpatialFaculty"` hard-coded on every `Route` constructor ✅
- SQ-3: no rival spatial model exists in `LiveWorldState` (asserted by test) ✅
- `EloDesktopNav` NOT touched (§E gate — David L3 required) ✅

---

## Remaining Sections (not Builder-only executable)

| Section | Status | Blocker |
|---|---|---|
| §C — Shadow parity proof | ⏸ | Requires live Unity round-trip session (Designer seat) |
| §D — Switch brain on | ⏸ | §C parity proof must exist first |
| §E — Retire Unity's local route selection | ⏸ | David L3 ruling D-XIII-1 required |
| §F — Noticing, learning, many bodies | ⏸ | §D must land first |

---

## Board Consequence

WO-CANON-XIII §A+§B DONE. Builder has delivered all sections executable without Designer or David L3. §C requires a Designer-coordinated shadow parity run. Board to MT-verify and note that line 4105 in this session's scan entry incorrectly stated "DO NOT START" — corrected: §A+§B are done; only §E is David-L3-gated.

*Builder · 2026-08-28*
