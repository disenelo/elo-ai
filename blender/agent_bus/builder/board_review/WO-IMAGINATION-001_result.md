# WO-IMAGINATION-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Commit:** 888916a  
**Status:** COMPLETE — 31/31 tests pass

---

## Gap closed

eLo had no deliberate simulation capability — no way to reason about hypothetical outcomes, counterfactuals, other perspectives, mechanism capabilities, or its own embodied capabilities without treating the result as fact. Imagination-generated claims were indistinguishable from vault knowledge.

---

## What was implemented

### `faculties/imagination/imagination_faculty.py`

**SimulationResult dataclass:**
- `simulation_type`: one of 5 valid types
- `hypothesis`: the simulated claim (non-empty, validated)
- `confidence`: float 0.0–1.0 (out-of-range raises ValueError)
- `evidence`: list[str] reasoning chain
- `expiry`: unix timestamp, defaults to now+3600
- `epistemic_status`: starts at "SIMULATED" — never promoted automatically
- `context`: dict of simulation inputs
- `timestamp`: creation time
- `is_expired` property: `time.time() > expiry`

**Epistemic gate** (immutable — promote/invalidate return new instances):
- `promote()`: SIMULATED → CANDIDATE → VERIFY → KNOWLEDGE (KNOWLEDGE is noop)
- `invalidate()`: any state → REMAINS_HYPOTHESIS

**Five simulation functions:**
1. `simulate_outcome(action, context, confidence)` — "If I do X, what happens?"
2. `simulate_counterfactual(past_event, alternative, context, confidence)` — "What if that had gone differently?"
3. `simulate_perspective(subject, situation, context, confidence)` — "How might X experience this?" (feeds CCM — subject named in evidence)
4. `simulate_design(mechanism, capability_query, context, confidence)` — "If this mechanism works this way, what can it do?"
5. `simulate_self(embodiment, capability_query, context, confidence)` — "What am I capable of in this embodiment?"

**`simulate(simulation_type, **kwargs)` dispatcher:**
- Validates type against `VALID_SIMULATION_TYPES`, raises ValueError on unknown
- Routes to correct function, logs at DEBUG

**`context_block(results) -> str`:**
- Filters: non-expired, epistemic_status == "SIMULATED" only
- Format: `[IMAGINATION — deliberate simulations, not facts. Treat as hypotheses only.]` header + per-result lines with type and confidence
- Returns empty string when nothing active

### `faculties/imagination/__init__.py`
Empty package init.

---

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC-1 | Five simulation types callable by Executive | ✅ |
| AC-2 | SimulationResult schema with confidence and expiry | ✅ |
| AC-3 | Outputs marked SIMULATED — never auto-promoted | ✅ |
| AC-4 | Epistemic gate between result and knowledge | ✅ |
| AC-5 | Perspective simulation feeds CCM (subject in evidence) | ✅ |

---

## Tests

`tests/test_wo_imagination_001.py` — 31/31:
- TestSimulationResultSchema (8): schema fields, confidence range, expiry, is_expired, empty hypothesis, unknown type
- TestFiveSimulationTypes (8): VALID_SIMULATION_TYPES count, all 5 simulation functions, dispatcher routing, unknown type raises
- TestEpistemicGate (8): initial SIMULATED, promote chain, KNOWLEDGE noop, invalidate, immutability
- TestContextBlock (5): empty, expired excluded, non-SIMULATED excluded, active result format, multiple results
- TestPerspectiveFeedsCCM (2): subject in hypothesis, subject in evidence

---

## Wire note

`context_block()` is ready for Executive injection. When intent signals a "what if" or simulation query, the Executive should call `simulate()` and pass results to `context_block()`, prepending the result to `_combined_vault` before the LLM call. This wiring is a follow-on step (not in scope for this WO).
