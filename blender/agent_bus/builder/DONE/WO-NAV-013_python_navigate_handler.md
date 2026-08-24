# WO-NAV-013 — Python Navigate Handler
**Seat:** Builder  
**Issued:** 2026-08-24  
**Authority:** Board — SP-24 D-2 ACCEPTED; SP-18, SP-20, SP-21 gates cleared  
**SPEC:** `docs/architecture/specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` (SP-18, SP-20, SP-21)  
**Gate:** SP-24 D-2 ACCEPTED (Unity receiver side) — Unity-WO-B2 (DesktopBuddy pathfinder) is a separate parallel track; WO-NAV-013 proceeds now.  
**Depends on:** WO-NAV-001 ✅ · WO-NAV-003 ✅ · WO-NAV-004 ✅

---

## Scope

Implement the Python-side `navigate` CAL action handler in `runtime/backend_router.py` (currently exists in priority router with NO handler — confirmed `backend_router.py` has the `navigate` CAL action but no implementation). Wire it to the surface graph + capability constraints already in place from WO-NAV-003/004.

---

## SP items

### SP-18 — Navigate action handler
- `navigate` CAL action in `backend_router.py` receives `{ goal_win_id, type, direction }` from Executive
- Handler reads `world_dict["surface_graph"]` (WO-NAV-004 ✅) to find reachable path to `goal_win_id`
- Handler reads `capability_set.jump_px` (WO-NAV-004 ✅) as the reachability constraint
- Emits a `move_command` structured body to the Unity UP channel with `goal_win_id`, `type`, `direction`
- Returns a `NavigateIntent` (or equivalent) to the consequence chain

### SP-20 — Navigate result wiring
- When `movement_report` ACK arrives (now wired via SP-1, WO-NAV-001 ✅), the consequence chain must map `arrived=True/False` to the ongoing navigate intent
- `MovementOutcome.from_ack()` (WO-NAV-001 ✅) is already the ACK parser — use it
- On `arrived=True`: navigation SUCCEEDED → log to autobiography (rich entry from WO-NAV-002 once verified)
- On `arrived=False`: navigation FAILED → trigger consequence (failure note, not a loop)

### SP-21 — Navigate → Executive feedback
- The result of SP-20 must be accessible to the Executive on the next turn
- Navigation outcome must be in `executive_context` (or equivalent) so the Executive can observe it had a movement goal and what happened

---

## Acceptance tests (AT)

| AT | Description | Pass criterion |
|---|---|---|
| AT-1 | `navigate` CAL action received with `goal_win_id=5` → `move_command` emitted with `goal_win_id=5` | move_command present in UP channel with correct win_id |
| AT-2 | `movement_report` with `arrived=True` → `MovementOutcome.arrived=True` → navigate SUCCEEDED | outcome logged; no failure note |
| AT-3 | `movement_report` with `arrived=False` → `MovementOutcome.arrived=False` → navigate FAILED | failure consequence fires; no infinite retry |
| AT-4 | Navigate result appears in executive_context on next turn | executive_context contains movement outcome |
| AT-5 | `navigate` with no `goal_win_id` (directional only) → handler does NOT crash, routes directional | directional `move_command` emitted; `goal_win_id` absent |

---

## Lane rules
- `.py` only. No `.cs`, no test creation.
- Do not touch established WO-NAV-001/003/004 contracts — extend, never break.
- `elo_spatial.json` / `surface_graph` reads are already wired — use them.

## Return evidence
File `FROM_BUILDER_WO-NAV-013_result.md` in `builder/DONE/` with: commit hash · AT-1–5 pass/fail · any defects found.

---

*Board / Lead Architect · 2026-08-24*
