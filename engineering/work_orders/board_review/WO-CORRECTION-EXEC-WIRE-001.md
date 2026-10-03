# WO-CORRECTION-EXEC-WIRE-001 — Correction History into Executive Decision

**Priority:** P2  
**Assigned:** Builder 1  
**Lane:** `self_improvement/correction_store.py` + `runtime/executive_context.py` + `runtime/executive.py`

## Gap

`self/corrections_ledger.jsonl` has 44,606 entries. `correction_history_prompt_block()` is injected into the system prompt (`server.py` ~5055) — this reaches LLM text generation only. `search_corrections(raw_input)` exists in `correction_store.py` but is never called before `executive.decide()`. Corrections cannot lower confidence on recurring error types. The correction architecture exists but does not causally alter decisions.

## Fix

In `build_executive_context()`: call `correction_store.search_corrections(raw_input)`. If matching correction categories found with `frequency >= 3`: add `correction_alert: {"category": str, "frequency": int}` to `ExecutiveContext`. In `executive.decide()`: if `correction_alert` present → lower confidence threshold for current action selection, weight toward "reflect" if `frequency >= 5`.

## Acceptance

An input that matches a correction category with frequency 5+ results in lower-confidence action selection or "reflect" preference. `test_correction_exec_wire.py` verifies the counterfactual.
