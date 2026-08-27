# WO-SPINE-002 — State Envelope (CognitiveState / EmbodimentState / ExecutionReport)
**Priority:** P1 — BUILD AFTER WO-SPINE-001
**Authority:** `_intake/SOURCE_2026-08-22_CA_build_directive_full_queue.md`
**Date:** 2026-08-22

---

## Problem

The Executive is called after assembly but receives a textual description of state, not structured state. It is effectively deaf to what was assembled around it.

## What to build

Wire the three defined state structures into the actual spine so the Executive receives them as structured data:

```
CognitiveState      (attention, working memory, focus)
EmbodimentState     (avatar, motor, presence)
ExecutionReport     (what happened last turn)
        ↓
Executive
        ↓
decision (informed by actual state, not text description of state)
```

Source contracts: Volume VII (Executive Cortex), Volume VI (Working Memory & Attention), Volume XI (Motor Cortex).

## Acceptance

- Executive receives `CognitiveState` as a structured object, not a prose summary
- Executive receives `EmbodimentState` as a structured object
- Previous turn's `ExecutionReport` reaches Executive before planning
- Executive decision demonstrably uses state fields (e.g. attention level affects response)

## Hard constraints

- Do not redesign the Executive
- Do not add new state structures beyond the three defined
- Do not merge these structures into one blob

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** `memory/execution_context.py` — `CognitiveState`, `EmbodimentState`, `ExecutionReport` wired into `ExecutionContext`. Executive receives structured state fields, not prose descriptions.

**Acceptance:** `tests/test_spine002_state_envelope.py` — 27/27 passed (commit `0653d20`). Executive context has `cognitive_state`, `embodiment_state`, `execution_report` fields; `as_dict()` exposes all EC state keys; `build_executive_context()` accepts and forwards them; spine.py carries `_prev_embodiment_state` and `_prev_execution_report` module vars.

**Re-verified 2026-08-28:** MT relay reported 6/27 — discrepant with prior DONE. Builder re-ran, identified and fixed gaps, achieved 27/27 under VP-2 rule (miniconda3 python3). Board 2026-08-10 ruling: tests pass = DONE.
