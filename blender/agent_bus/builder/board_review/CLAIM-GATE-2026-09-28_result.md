# claim_gate dispatch 2026-09-28 — RESULT
**Builder 1 | 2026-09-28**
**Dispatch:** `FROM_ARCHITECT_2026-09-28_BUILDER1-CLAIM-GATE.md`

---

## What was built

**Check 16: `_check_cognitive_claim_origin()`** added to `runtime/response_gate.py`.

Wires `can_claim_occurred()` enforcement at the response layer as required by the dispatch.

### Approach

The dispatch said `can_claim_occurred()` lives in `claim_gate.py` — it's actually in
`runtime/cognitive_state.py:133`. Corrected silently (same function, right file).

The `cognitive_state` param received by `response_gate.evaluate()` is a dict (confirmed from
existing checks 5 and 7 which both do `isinstance(cognitive_state, dict)`). There is no
`cognitive_state_enum` field in the `contracts.py` CognitiveState data class — the enum value
must be extracted from a state string key.

### Constants added

```python
_OCCURRENCE_CLAIM_PATTERNS = [
    "i remember", "i recall", "i experienced", "i witnessed",
    "i dreamed that", "i dreamt that", "in my dream i",
    "i know because i", "i was there", "i felt it",
    "i heard it happen", "i saw it happen",
    "it happened to me", "that happened to me",
    "i went through that", "i've been through that", "i have been through that",
]

_INTERNALLY_GENERATED_STATE_NAMES = frozenset({
    "dream", "simulation", "imagination", "prediction", "hypothesis",
})
```

### Check logic

1. Scan response for occurrence claim patterns
2. Extract state string from cognitive_state dict (`state`, `cognitive_mode`, `cognitive_state`, `current_state` keys)
3. Fallback: `dream_phase` boolean from ambient engine
4. If state not determinable → conservative pass (no false positives)
5. If state is MEMORY / OBSERVATION / ACTION / KNOWLEDGE / INSTINCT → allowed (pass)
6. If state is DREAM / SIMULATION / IMAGINATION / PREDICTION / HYPOTHESIS → call `can_claim_occurred()`
7. If `can_claim_occurred()` returns False → advisory flag (no hard block)

### Advisory-only

Check 16 is log-only — it flags without hard-blocking. Check 5 (`action_truth`) owns the
hard-block path for capability claims. Occurrence claims from internally-generated states are
flagged so the Board can see them in `data/gate_log.jsonl`.

---

## Commit

**`75e3962`** — `runtime/response_gate.py`

Lines changed:
- +17 lines: `_OCCURRENCE_CLAIM_PATTERNS` and `_INTERNALLY_GENERATED_STATE_NAMES` constants
- +55 lines: `_check_cognitive_claim_origin()` function
- +2 lines: check_16 registered in `evaluate()` checks list
- +3 lines: module and class docstrings updated

---

## Tests

6/6 inline tests pass:
- T1: dream state + "I remember" → flagged ✓
- T2: simulation state + "I recall" → flagged ✓
- T3: no state info → conservative pass (no false positive) ✓
- T4: memory state + "I remember" → allowed ✓
- T5: dream state but no occurrence claim → no flag ✓
- T6: `dream_phase=True` boolean fallback → flagged ✓

---

## For Board

- Check 16 advisory flags appear in `data/gate_log.jsonl` under key `cognitive_claim_origin:unverifiable:<state>:<phrase>`
- No live server restart needed — response_gate is imported fresh per request
- Board to verify flag fires in live testing when eLo references dream content as memory
