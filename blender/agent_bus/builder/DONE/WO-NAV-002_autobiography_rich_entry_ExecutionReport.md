# WO-NAV-002 — Autobiography Rich Entry + ExecutionReport Movement Fields
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — SPEC ratification 2026-08-23 + Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Signal:** WO-NAV-001 VERIFIED (commit `b70916a`, 11/11 PASS, SP-1/SP-2/SP-22 confirmed)  
**Priority:** 🟠 HIGH — Wave 2. Unlocks structured consequence data on every navigation turn.  
**RTR:** RTR-008f (autobiography), RTR-022 (ExecutionReport movement_outcome)  
**SPEC basis:** SP-3 + SP-23 — `SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md`  
**Dependency:** SP-1, SP-2, SP-22 — all complete (WO-NAV-001, commit `b70916a`)

---

## Why now

SP-3: The autobiography entry for movement currently writes only `f"moved ({_mv_desc}) — body ACK confirmed"` — the full `_mv_ev` payload (arrived, fell, goal, route, duration) is captured but discarded. This is a three-line addition.

SP-23: `ExecutionReport` movement fields are empty for navigation because MovementOutcome (SP-22) is not yet wired to them. The Executive sees no structured consequence data on the turn after a move. This is a wiring step.

---

## Deliverables

### D-1 — SP-3: Enrich autobiography entry with full movement payload

**File:** `server.py`  
**Location:** The autobiography write block inside the movement ACK handler (currently around lines 3088–3100; contains `# WO-115: autobiography — verified events only`).  
**Current code (simplified):**
```python
_mv_desc = _PENDING_MOVE.get("sub_type", "") or _PENDING_MOVE.get("direction", "unknown")
_ab_mv(
    f"moved ({_mv_desc}) — body ACK confirmed",
    kind="action",
    verified=True,
    source="body_ack",
    episode_ref=str(_mv_ev.get("_ts") or _mv_ev.get("report", {}).get("_ts", "")),
)
```

**Required change:**  
Populate `MovementOutcome` from `_mv_ev` and include the structured fields in the autobiography entry. At minimum:

```python
from runtime.movement_outcome import MovementOutcome as _MO
_mout = _MO.from_ack(_mv_ev, since=_PENDING_MOVE.get("since", 0.0))
_ab_mv(
    f"moved ({_mout.goal or _mv_desc}) — body ACK confirmed",
    kind="action",
    verified=True,
    source="body_ack",
    episode_ref=_mout.ack_id,
    metadata={
        "arrived":    _mout.arrived,
        "fell":       _mout.fell,
        "goal":       _mout.goal,
        "goal_win_id": _mout.goal_win_id,
        "route_nodes": _mout.route_nodes,
        "duration_s": _mout.duration_s,
        "issued_by":  _mout.issued_by,
    },
)
```

If `append_autobiography` does not accept a `metadata` keyword, add the structured fields to the description string or to an available keyword parameter — do not alter the autobiography API signature to accommodate this.  
**Constraint:** Only change the argument list passed to `_ab_mv`. Do not touch the ACK state machine. The `_MO.from_ack()` import should be local (inside the try block) to avoid import-time side effects.

---

### D-2 — SP-23: Wire MovementOutcome → ExecutionReport movement fields

**Files:** `runtime/contracts.py` (add fields) + `server.py` (populate at ACK resolution)

**Step A — contracts.py:**  
Add movement_outcome fields to `ExecutionReport`. These are the SP-23 canonical fields:

```python
# ── Navigation / Movement Outcome (SP-23) ──────────────────────────────────
move_arrived:       bool  = False    # True when eLo reached the intended platform
move_fell:          bool  = False    # True when eLo fell or missed
move_goal_win_id:   "int | None" = None  # Commanded destination node id
move_duration_s:    float = 0.0     # Travel time in seconds
move_issued_by:     str   = ""      # Who issued the move ("user_message" | "self_initiation" | ...)
```

Add these inside `ExecutionReport` (class in `runtime/contracts.py`, currently around line 345). Insert them in a clearly labelled section after the Interruption block. Do not rename or remove any existing fields.

**Step B — server.py:**  
Where `ExecutionReport` is constructed/populated (find the construction site — search for `ExecutionReport(` or assignment to its fields), populate these fields from `_mout` (the MovementOutcome built in D-1). If `ExecutionReport` is populated incrementally, add the movement fields at the point where `_move_acked` is processed:

```python
# SP-23: wire MovementOutcome → ExecutionReport
_exec_report.move_arrived    = _mout.arrived
_exec_report.move_fell       = _mout.fell
_exec_report.move_goal_win_id = _mout.goal_win_id
_exec_report.move_duration_s  = _mout.duration_s
_exec_report.move_issued_by   = _mout.issued_by
```

If `ExecutionReport` is constructed and returned in a single call, add these fields to that constructor call.  
**Constraint:** Do not change how `ExecutionReport` flows to `integrate_session()`. Only add the new fields and populate them at the right point.

---

## Forbidden scope

- No changes to `executive.py` or any file under FREEZE_V1_LOCK
- Do not alter the autobiography API signature
- Do not change the ACK state machine beyond the additions above
- Do not wire MovementOutcome to consequence consumers yet — that is WO-NAV-002's scope ceiling
- WO-NAV-008 is a separate WO issued alongside this one — do not merge its scope

---

## Verification

| AT | SP | Description | Pass condition |
|---|---|---|---|
| AT-1 | SP-3 | Rich payload in autobiography entry | After a simulated movement ACK, `append_autobiography` is called with `arrived`, `fell`, `goal`, `duration_s` values from the payload — not just the direction string |
| AT-2 | SP-3 | `MovementOutcome.from_ack()` called with `since=` | `_mout.duration_s > 0` when `since` is set; `ack_id` is non-empty string |
| AT-3 | SP-23 | ExecutionReport has move fields | `ExecutionReport().move_arrived` is accessible (default False); all 5 fields importable |
| AT-4 | SP-23 | Fields populated from ACK | After ACK resolution, `_exec_report.move_arrived == _mout.arrived` and `_exec_report.move_goal_win_id == _mout.goal_win_id` |
| AT-5 | SP-3+SP-23 | No regression on existing ACK path | Existing AT-1 through AT-3 from WO-NAV-001 still pass |

---

## Required return evidence

1. Changed files — file paths + line numbers
2. AT results — AT-1 through AT-5 pass/fail with one-line evidence
3. Commit hash
4. Blocker report if any (format per `SEAT_PROTOCOL_AMENDMENT_BLOCKER_SCOPE_2026-08-24.md`)

Return to: Board. On verified pass → Board assesses WO-NAV-009 (SP-9 + SP-12, Unity-WO-B1 dependency).

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — SPEC ratification 2026-08-23 + Execution Directive 2026-08-24*
