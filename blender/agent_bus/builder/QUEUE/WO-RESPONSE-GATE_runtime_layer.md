# WO-RESPONSE-GATE — eLo Response Gate as Runtime Cognitive Layer
**Seat:** Builder  
**Priority:** P1  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30; FREEZE_V1_LOCK LIFTED 2026-08-30 (Builder-only on executive.py)  
**Source:** BOARD COMMAND — eLo Response Authority + Universal Execution Governance Realignment.rtf §6; SOURCE_ALIGNMENT_REGISTER_2026-08-30.md CF-03; BA-04  
**Lane note:** Builder ONLY. `executive.py` is Builder-only per David L3 ruling 2026-08-30.

---

## Intent (verbatim source)

Source — eLo Intent Alignment §6:
> "This must be represented in the runtime, not merely described in a system prompt."

The eLo Response Gate currently exists ONLY as a paragraph in the system prompt. David's source documents are explicit: it must be a **runtime cognitive evaluation step** that runs after faculty output and before the final response is emitted.

The 10-point response reconciliation gate from BOARD COMMAND — eLo Response Authority is the spec. Builder implements it in the runtime loop.

---

## Scope

### The Gate — 10-point reconciliation (from source document, verbatim)

After faculty output, before `executive.py` emits the final response, run this evaluation:

1. **Identity check** — Does this response sound like eLo? (not generic assistant, not LLM-speak)
2. **Personality check** — Does this match eLo's active personality register (personality_evolution output)?
3. **Faculty leakage check** — Does this response expose internal faculty reasoning, planning steps, or system state? If yes → strip.
4. **Relevance check** — Does this respond to what David actually said/asked/meant?
5. **Action-truth check** — If eLo claims to have done something, did it actually execute? (Embodied Truth invariant)
6. **Authority check** — Does this response claim capabilities or memories eLo does not have? (D-2/D-3 guards are a subset; this is the cognitive-layer version)
7. **Register check** — Does the language register match CCM output (if available)?
8. **Length check** — Is this the right length? (no padding, no over-explanation — source: "no padding" rule)
9. **Reflection-as-default check** — Is this response describing the conversation instead of participating in it? If yes → rewrite to participate.
10. **Rest check** — Is this the simplest, most direct expression of the thought? (FEEL-NAME-SHAPE-EXPRESS-CHECK-REST loop final step)

### Implementation

Create `runtime/response_gate.py`:
- Class `ResponseGate` with method `evaluate(response: str, cognitive_state: CognitiveState, executive_context: dict) -> GateResult`
- `GateResult` has: `passed: bool`, `revised_response: str | None`, `flags: list[str]`
- If any check fails and a revision is possible → revise and flag
- If a check fails and revision is not possible → flag for logging (do not block the response; gate is a quality layer, not a hard blocker in v1)

Wire into `executive.py` AFTER faculty assembly and BEFORE response emission:
```python
gate_result = response_gate.evaluate(draft_response, cognitive_state, executive_context)
final_response = gate_result.revised_response or draft_response
```

### NOT in scope (v1)
- Checks 4, 5, 7 require full integration with CCM + embodiment state — implement as stubs in v1 that log "not yet evaluated" and pass.
- Checks 1, 2, 3, 6, 8, 9, 10 must be fully active in v1.

---

## Definition of Done

- [ ] AT-1: `runtime/response_gate.py` exists with `ResponseGate` class and `evaluate()` method.
- [ ] AT-2: A response containing generic assistant phrasing ("As an AI language model…", "Certainly!", "Of course!") is flagged by identity check (AT-1) and revised.
- [ ] AT-3: A response that describes the conversation ("I notice you're asking about…") is flagged by reflection-as-default check and rewritten.
- [ ] AT-4: A response that claims eLo has done something it has not (no embodied action logged) is flagged by action-truth check.
- [ ] AT-5: `response_gate.evaluate()` is called in `executive.py` before response emission — trace evidence in logs.
- [ ] AT-6: Gate logs all flags to `data/gate_log.jsonl` per turn.
- [ ] AT-7: Full test suite passes with no new failures.

---

## Files in scope

- `runtime/response_gate.py` (create)
- `runtime/executive.py` (wire gate call — Builder-only)
- `data/gate_log.jsonl` (create on first run)

## Files NOT in scope

- `runtime/response_authority_guards.py` (D-1/D-2/D-3 are a separate, lower-level layer — do NOT merge)
- Anything in Unity / Design / MT
