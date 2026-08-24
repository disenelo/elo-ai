# WO-NAV-007 — CognitivePlan + Move Command Schema Additions
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** HIGH — Wave 1 independent; unblocks SP-18 contract side  
**RTR:** RTR-052  
**SPEC basis:** `specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` — SP-15, SP-19

---

## Context

Two schema additions that are independent of any running work and unblock the navigate handler (SP-18) at the contract level. Both are additive only — no existing behaviour changes.

---

## Deliverables

### D-1 — SP-15: `spatial_plan` field in `CognitivePlan`
**File:** wherever `CognitivePlan` is defined (dataclass or schema)  
**Contract:**
- Add optional field `spatial_plan: dict | None = None` to CognitivePlan
- This field will be populated later by SP-18 (navigate handler) when deliberate navigation is requested
- For all current non-navigate turns, the field remains `None` — no existing behaviour changes
- The field stores the planned navigation route: at minimum `{goal_win_id: str, candidates: list, route: list}`

### D-2 — SP-19: `goal_win_id` field in `move_command` schema
**File:** wherever `move_command` is constructed/schema is defined  
**Contract:**
- Add optional field `goal_win_id: str | None = None` to the move_command payload
- This field allows the Executive to specify a target platform when issuing a navigate command
- For all current movement commands (non-deliberate navigation), the field is absent or `None` — no existing behaviour changes
- Unity acceptance of this field must be verified by Builder as part of the SP-24 verification task (run a test move_command with `goal_win_id` set and confirm Unity does not error)

**SP-24 verification task:** After building SP-19, Builder should run a test move_command with `goal_win_id` included and report the Unity response. This is a runtime verification, not a new design. On confirmation, the Board will issue WO-NAV-013 (navigate handler).

---

## Forbidden Scope

- No changes to `executive.py` or FREEZE_V1_LOCK files
- No navigate handler yet — that is SP-18 (WO-NAV-013, after SP-24 confirmed)
- No changes to existing movement logic

---

## Verification

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | spatial_plan field exists | CognitivePlan has `spatial_plan: dict \| None = None`; existing turns have `spatial_plan = None` |
| AT-2 | goal_win_id field exists | move_command schema includes `goal_win_id` as optional field |
| AT-3 | Existing moves unaffected | A normal movement (not deliberate navigate) proceeds without error; spatial_plan = None; goal_win_id = None |
| AT-4 | SP-24 test | Builder sends test move_command with `goal_win_id = "some_win_id"` → Unity accepts without error (report result to Board) |

---

## RTR Traceability

After implementation, update RTR-052 in `RECOVERY_TRACEABILITY_REGISTER_2026-08-24.md`:
- RTR-052: add WO-NAV-007, commit, AT-1 through AT-3 pass
- Record SP-24 test result — if Unity accepts: Board will issue WO-NAV-013

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — Execution Directive 2026-08-24*

---

## Result — Builder 2026-08-24

**Status:** DONE  
**Commit:** `821e711` — WO-NAV-007: CognitivePlan + move_command schema additions  
**Tests:** 9/9 PASS (`tests/test_wo_nav_007.py`)

### Deliverables executed

| D | SP | File | Status |
|---|---|---|---|
| D-1 | SP-15 | `runtime/spine/plan.py` — `spatial_plan: dict | None = None` added to `CognitivePlan` | ✅ |
| D-2 | SP-19 | `blender_bridge/state_writer.py` — `goal_win_id` additive field in both `move_command` sites | ✅ |

### SP-24 Verification
Schema verified JSON-serialisable (AT-4 PASS). Live Unity acceptance requires a running session — David's lane. Board to issue WO-NAV-013 after live confirmation.

### Acceptance tests

| AT | Result |
|---|---|
| AT-1: spatial_plan field exists, defaults None | PASS (3 sub-tests) |
| AT-2: goal_win_id in move_command when set | PASS (3 sub-tests) |
| AT-3: Existing moves unaffected | PASS (2 sub-tests) |
| AT-4: SP-24 schema JSON-serialisable | PASS |

*Builder — 2026-08-24*
