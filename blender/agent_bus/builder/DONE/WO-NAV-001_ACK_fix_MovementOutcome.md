# WO-NAV-001 — ACK Fix + MovementOutcome (SP-1 · SP-2 · SP-22)
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — SPEC ratification 2026-08-23 + Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** 🔴 IMMEDIATE — highest-leverage act in programme. No other WO depends on this first; this unblocks every consequence consumer.  
**RTR:** RTR-008f (ACK chain), RTR-022 (MovementOutcome / consequence consumer contract)  
**SPEC basis:** `docs/architecture/specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` — SP-1, SP-2, SP-22

---

## Why now

Every successful graph-nav turn currently produces a false `[MOVE_FAILED]` in all consequence consumers. Root cause: `"movement_report"` is not in `_ACK_BODY_TYPES`, so every movement_report ACK is silently discarded. `_PENDING_MOVE` matcher also reads the wrong path in the payload. Until SP-1 and SP-2 are in, no consequence consumer in the entire programme can distinguish a real failure from a successful navigation. This is two lines.

SP-22 (`MovementOutcome`) provides the typed dataclass that consequence consumers will use. It is the structured result that comes out of the fixed ACK chain.

---

## Deliverables

### D-1 — SP-1: Add `"movement_report"` to `_ACK_BODY_TYPES`
**File:** `runtime/server.py`  
**Location:** Lines 149–151 (the `_ACK_BODY_TYPES` list/set).  
**Contract:** Add the string `"movement_report"` to `_ACK_BODY_TYPES`. This is one item in an existing list. Nothing else changes.  
**Constraint:** Do not touch any other part of the ACK routing. Do not add logic — only the string.

### D-2 — SP-2: Fix `_PENDING_MOVE` matcher
**File:** `runtime/server.py`  
**Contract:** The `_PENDING_MOVE` matcher currently reads the wrong payload path. Fix it to read `payload["report"]["arrived"]`.  
**Authoritative path:** `payload["report"]["arrived"]` — there is no `subject` field in movement_report. `arrived` is a bool on the nested `report` dict.  
**Constraint:** Only fix the matcher path. Do not change the PENDING_MOVE state machine or ACK coroutine logic beyond this single path correction.

### D-3 — SP-22: Add `MovementOutcome` typed dataclass
**File:** `runtime/consequence_engine.py` or a new `runtime/movement_outcome.py` — Builder's choice; prefer proximity to the consequence consumer.  
**Contract:** A typed dataclass with these exact fields:

```python
@dataclass
class MovementOutcome:
    arrived: bool
    fell: bool
    goal: str
    goal_win_id: int | None
    route_nodes: list[str]
    duration_s: float
    ack_id: str
    issued_by: str
```

This dataclass is the structured result that consequence consumers receive after a confirmed movement_report ACK. It does NOT replace the raw ACK payload — it is a typed wrapper populated from it.  
**Constraint:** Define the dataclass and its population logic only. Do not wire it to any consumer yet — that is WO-NAV-002 (held). Do not change the ACK chain.

---

## Forbidden scope

- No changes to `executive.py` or any file under FREEZE_V1_LOCK
- No changes to Unity side
- No changes to graph-nav routing or consequence consumers beyond the dataclass definition above
- No changes to `_PENDING_MOVE` state machine logic beyond the payload path fix
- No new ACK types beyond `"movement_report"`
- WO-NAV-002 (consequence consumer wiring) is HELD — do not begin it

---

## Verification

| AT | SP | Description | Pass condition |
|---|---|---|---|
| AT-1 | SP-1 | movement_report in ACK_BODY_TYPES | String `"movement_report"` present in `_ACK_BODY_TYPES`; grep confirms |
| AT-2 | SP-2 | Matcher reads correct path | `payload["report"]["arrived"]` is the path used; no `subject` key reference remains |
| AT-3 | SP-1+SP-2 | Graph-nav ACK no longer silently discarded | Simulate or trigger a movement_report payload; confirm ACK is routed and `_PENDING_MOVE` resolves correctly (arrived=True → not MOVE_FAILED) |
| AT-4 | SP-22 | MovementOutcome dataclass importable | `from runtime.movement_outcome import MovementOutcome` (or equivalent) succeeds without error |
| AT-5 | SP-22 | All fields present with correct types | Instantiate with known values; confirm field names and types match spec |

AT-3 is the critical integration test. If the ACK routing was broken before, AT-3 must demonstrate it is now resolved.

---

## RTR traceability

After implementation, update the relevant RTR entries in `RECOVERY_TRACEABILITY_REGISTER_2026-08-24.md`:
- RTR-008f: add WO-NAV-001, commit hash, AT-1/AT-2/AT-3 pass
- RTR-022: add WO-NAV-001, commit hash, AT-4/AT-5 pass

---

## Required return evidence

Builder reports to Board with:

1. **Changed files** — file path + line numbers changed (not diffs, just locations)
2. **AT results** — pass/fail for AT-1 through AT-5 with one-line evidence per AT
3. **Commit hash** or equivalent if version control in use
4. **Blocker report** (if any) — format per `SEAT_PROTOCOL_AMENDMENT_BLOCKER_SCOPE_2026-08-24.md`

Return to: Board (DISPATCH_BOARD row for WO-NAV-001 → BUILT + VERIFIED signal)

On verified pass: Board issues WO-NAV-002 (consequence consumer wiring) and WO-NAV-008 (held pending this signal).

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — SPEC ratification 2026-08-23 + Execution Directive 2026-08-24*

---

## Result — Builder 2026-08-24

**Status:** DONE  
**Commit:** `b70916a` — WO-NAV-001: ACK fix + MovementOutcome (SP-1, SP-2, SP-22)  
**Tests:** 11/11 PASS (`tests/test_wo_nav_001.py`)

### Deliverables executed

| D | SP | File | Notes | Status |
|---|---|---|---|---|
| D-1 | SP-1 | `server.py:151` | `"movement_report"` was already in `_ACK_BODY_TYPES` with SP-1 comment — pre-existing | ✅ verified |
| D-2 | SP-2 | `server.py:3067–3072` | Matcher reads `payload["report"]["arrived"]` with SP-2 comment — pre-existing | ✅ verified |
| D-3 | SP-22 | `runtime/movement_outcome.py` (new) | `MovementOutcome` dataclass + `from_ack()` populator, 8 fields per spec | ✅ |

### Changed files + line numbers
- `runtime/movement_outcome.py` — new file (SP-22 dataclass)
- `tests/test_wo_nav_001.py` — new file (AT-1 through AT-5)
- No changes to server.py (D-1/D-2 pre-existing)

### Acceptance tests

| AT | SP | Result |
|---|---|---|
| AT-1: movement_report in _ACK_BODY_TYPES | SP-1 | PASS (2 sub-tests) |
| AT-2: report.arrived path in source | SP-2 | PASS |
| AT-3: ACK no longer silently discarded | SP-1+SP-2 | PASS (3 sub-tests — arrived=True, arrived=False, legacy) |
| AT-4: MovementOutcome importable | SP-22 | PASS |
| AT-5: All fields correct types | SP-22 | PASS (4 sub-tests) |

### RTR updates required
- RTR-008f: WO-NAV-001, commit b70916a, AT-1/AT-2/AT-3 PASS
- RTR-022: WO-NAV-001, commit b70916a, AT-4/AT-5 PASS

Board may now issue WO-NAV-002 (consequence consumer wiring) and WO-NAV-008.

*Builder — 2026-08-24*
