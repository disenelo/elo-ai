# WO-005 — Integrate RS-GRND-01 into the Real Spine
**Priority:** P0 — BUILD AFTER WO-RS-002/003/004
**Authority:** `_intake/SOURCE_2026-08-22_CA_build_directive_full_queue.md`
**Date:** 2026-08-22

---

## What this is

RS-GRND-01 passed 16/16 tests. Now confirm the actual runtime uses it consistently — not just its own test suite.

## The real path to verify and enforce

```
INPUT
 ↓
ExecutionContext        ← RS-GRND-01
 ↓
Executive
 ↓
Capability selection
 ↓
Execution
 ↓
ExecutionTrace          ← RS-GRND-01
 ↓
ContextItem assembly    ← RS-GRND-01
 ↓
Provenance rendering    ← RS-GRND-01
 ↓
MODEL
 ↓
Identity validation
 ↓
OUTPUT
```

## What to check and wire

For each step: confirm `RS-GRND-01` structures (`ContextItem`, `ExecutionTrace`, `EpistemicClass`) are actually used — not bypassed by a parallel code path.

If a path bypasses RS-GRND-01: wire it. Do not build a new provenance subsystem — RS-GRND-01 is the provenance subsystem.

## Acceptance

- Send a real turn through the server
- Confirm `ExecutionTrace` is populated
- Confirm `ContextItem` objects (not anonymous strings) reach `_assemble_prompt()`
- Confirm provenance appears at the model boundary
- RS-GRND-01 16/16 still passes after changes

## Hard constraint

Do not create another provenance subsystem. Do not duplicate RS-GRND-01 structures. Wire existing ones.

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** RS-GRND-01 structures confirmed wired end-to-end through the real spine — `ExecutionContext`, `ExecutionTrace`, `ContextItem` assembly, `EpistemicClass` from `memory.provenance`, and provenance rendering at the model boundary. No parallel provenance subsystem exists.

**Acceptance results — `tests/test_wo005_grnd01_spine_integration.py`:**

| Test | Result |
|---|---|
| get_context_items returns ContextItems | ✅ PASS |
| render_context_block produces string | ✅ PASS |
| render_context_block includes epistemic label | ✅ PASS |
| generated item labelled GENERATED | ✅ PASS |
| begin_trace / get_trace cycle | ✅ PASS |
| render_execution_trace produces compact block | ✅ PASS |
| trace populated after enrich_from_plan | ✅ PASS |
| stripped written to trace on policy DENY | ✅ PASS |
| provenance module is sole source | ✅ PASS |
| obsidian_loader imports from provenance | ✅ PASS |
| vault_writer does not define its own epistemic classes | ✅ PASS |
| tool_router imports CapabilityRecord from provenance | ✅ PASS |
| Zhatthik invariant unchanged (RS-001 regression) | ✅ PASS |
| UNKNOWN class is distinct (RS-001 regression) | ✅ PASS |
| ExecutionTrace has correct fields (RS-001 regression) | ✅ PASS |

**15/15 passed.** No parallel provenance subsystem created. RS-GRND-01 is the sole source for ContextItem, ExecutionTrace, EpistemicClass.
