# WO-LOOP7-CAUSAL-PROOF-001 — Learning Loop Counterfactual Proof

**Priority:** P1  
**Assigned:** Builder 1  
**Lane:** `tests/` + `self/lesson_store.py` + `runtime/executive.py`

## Gap

The learning chain (`lesson_store → consult() → executive.decide()` action substitution) is architecturally wired but has no counterfactual test proving it. There is no test that demonstrates: same raw input, with lesson present vs without, produces a different CAL action. 44,606 correction events exist but corrections do not alter `executive.decide()` — only the LLM prompt. Whether any verified-evidence lessons exist in production is unconfirmed.

## Fix

Write `test_loop7_causal_proof.py`:  
1. Install a lesson with `verified=True`, `action="challenge"`, `weight=0.7`.  
2. Run `executive.decide()` on an input that would normally produce "answer."  
3. Assert the decision switches to "challenge."  
4. Remove the lesson.  
5. Assert the same input returns "answer."  
This proves the causal path is live, not just structural.

## Acceptance

`test_loop7_causal_proof.py` PASSES all 4 assertions. The causal chain LEARN → ALTER DECISION is proven.
