# WO-FACULTY-CONFLICT-EXEC-SIGNAL-001 — Faculty Conflict into Executive Action Selection

**Priority:** P2  
**Assigned:** Builder 1  
**Lane:** `runtime/executive_context.py` + `faculty_conflict_detector.py` + `runtime/executive.py`

## Gap

`faculty_conflict_detector.py` produces a conflict report and injects it into the system prompt (`server.py` ~5085). But `executive.decide()` cannot see faculty conflict — the conflict report reaches the LLM's text generation but cannot change the CAL action selection. When Memory and WKG disagree, Executive has no signal to route toward "reflect" rather than committing to a confident "answer."

## Fix

Add `faculty_conflict: {"detected": bool, "severity": str, "conflicting_faculties": list}` to `build_executive_context()` from `faculty_conflict_detector` output. In `executive.decide()`: if `faculty_conflict.detected` AND `severity=="high"` → weight toward "reflect" action over "build" or "answer." This tells Executive to hold when its information sources disagree.

## Acceptance

Input where Memory-endorsed interpretation and WKG-endorsed interpretation conflict → Executive selects "reflect" over "answer." Without conflict, same input → "answer."
