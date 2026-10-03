# WO-AMBIENT-EXEC-001 — Ambient Loop Executive Governance

**Priority:** P1  
**Assigned:** Builder 1  
**Lane:** `runtime/server.py` ambient loop + `blender_bridge/state_writer.py`

## Gap

`server.py` ambient dream loop (lines ~1013–1085) patches `blender_state.json` directly via `state_writer.patch` without a `CognitivePlan`. 16 `state_writer.patch` call sites in `server.py` — some are post-plan execution (correct), some are ambient process writes without a completed plan (not governed). Audit of `server.py` found patch calls at lines 1013, 1031 in the ambient dream loop that precede any `_executive_faculty()` call.

## Fix

Audit all 16 `state_writer.patch` call sites. For each: confirm it is either  
(a) conditional on a completed `CognitivePlan` value, or  
(b) emit a minimal plan stub (`action="dream"`, `source="ambient"`) before writing.  
No `blender_state` patch should be traceless — every write must carry a plan reference.

## Acceptance

No `state_writer.patch` call in `server.py` executes without a `CognitivePlan` reference in scope. Board can trace every `blender_state.json` write to an authorising plan.
