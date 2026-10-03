# WO-TEMPORAL-EXEC-WIRE-001 — Temporal State into Executive Decision

**Priority:** P2  
**Assigned:** Builder 1  
**Lane:** `runtime/spine/spine.py` + `runtime/executive_context.py` + `faculties/temporal/faculty.py`

## Gap

`temporal_compute()` is called at `spine.py:1307` — AFTER `_executive_faculty()` returns (which is at line 1230). So `temporal_frame` is set on the plan after the decision is already made. Executive has no temporal awareness when deciding. The temporal state (`circadian_phase`, `interaction_gap`, `deferred_threads`) that could change action selection (e.g., long gap since last session → "celebrate" reunion) never reaches `executive.decide()`.

## Fix

Move `temporal_compute()` call in `spine.run()` to BEFORE `_executive_faculty()` (before line 1230). Pass `temporal_state` result into `build_executive_context()` as `temporal: {"circadian_phase": str, "interaction_gap_hours": float, "has_deferred_threads": bool}`. In `executive.decide()`: if `interaction_gap_hours >= 24` AND `action=="answer"` → consider "celebrate" first. If `has_deferred_threads` → weight toward "continue" or "remember."

## Acceptance

After a 24-hour gap, the first turn produces "celebrate" action instead of default "answer." Test verifies by mocking `temporal_compute()` output.
