# WO-DEVELOPMENT-PROOF-001 — Live Development Causal Proof

**Priority:** P1  
**Assigned:** Builder 1  
**Lane:** Cross-cutting — references WO-SELF-MODEL-EXEC-WIRE-001, WO-LOOP7-CAUSAL-PROOF-001, WO-CURIOSITY-QSTORE-READ-001, WO-PREDICTION-ERROR-EXEC-WIRE-001, WO-CORRECTION-EXEC-WIRE-001

## Gap

Most development mechanisms (curiosity, prediction error, corrections, self-model) reach the LLM's language generation but not `executive.decide()` as action-changing signals. Development is structurally scaffolded but not causally proven. The pattern across 13 categories: passing tests prove components work, but the seam between faculty output and Executive decision is broken for most development signals.

## Fix

This is the meta-WO. After the individual wiring WOs above are implemented, produce a live development proof:  
1. Run Session A — record a lesson (verified), a curiosity question, a correction event.  
2. Run Session B (same model, no code change) — demonstrate at least one of the following: different CAL action from lesson, curiosity question surfaced and referenced, correction lowers action confidence.  
3. Document the before/after in `evidence/`.

## Acceptance

A structured evidence file in `engineering/evidence/DEVELOPMENT-PROOF-001.md` shows Session A events and Session B behavioural differences. The difference is traced to the causal wiring, not to a different prompt or code change.

**Gate:** Execute after WO-SELF-MODEL-EXEC-WIRE-001, WO-LOOP7-CAUSAL-PROOF-001, WO-CURIOSITY-QSTORE-READ-001, WO-PREDICTION-ERROR-EXEC-WIRE-001, WO-CORRECTION-EXEC-WIRE-001 are all PASS.
