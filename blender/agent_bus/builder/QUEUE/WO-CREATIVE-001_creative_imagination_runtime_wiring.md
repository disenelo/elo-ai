# WO-CREATIVE-001 — Creative Imagination Runtime Wiring
**From:** Board / Lead Architect
**Date:** 2026-08-28
**Priority:** P2
**Authority:** Vol XXVI Ch.1+Ch.3 (implemented in faculties/creative/creative_imagination.py); Build List §1 Creative Imagination

---

## Status

`faculties/creative/creative_imagination.py` is complete (divergent phase, symbolic synthesis, evaluation). It is NOT imported by `runtime/spine/spine.py` or any runtime module. This WO wires it in.

**Rule (ADR-Exec-002):** This module proposes and scores — never selects. Executive selects. The creative_imagination module must NEVER call executive.py or return a final decision.

---

## What to build

### D-1 — Wire creative_imagination into spine.py

In `runtime/spine/spine.py`, after the learning advice block (~line 274), add a creative imagination consultation using `diverge()` + `evaluate()`:

```python
_creative_candidates = []
try:
    from faculties.creative.creative_imagination import diverge as _ci_diverge, evaluate as _ci_evaluate
    _intent = _attention_in.get("intent", "")
    _focal = getattr(cognitive_state, "focal_thread", "") if cognitive_state else ""
    if _intent:
        _seeds = [_intent, _focal] if _focal else [_intent]
        _raw_candidates = _ci_diverge(goal=_intent, seeds=_seeds, breadth_budget=3)
        _creative_candidates = [_ci_evaluate(c, goal=_intent) for c in _raw_candidates] if _raw_candidates else []
except Exception as _ci_err:
    _log.debug("creative_imagination failed (non-critical): %s", _ci_err)
```

**Key:** `executive_select()` is for the Executive only — spine NEVER calls it.

### D-2 — Pass creative candidates to CognitiveState

Add `creative_candidates: list = field(default_factory=list)` to `CognitiveState` (in `runtime/contracts.py` or wherever CognitiveState is defined). Populate from `_creative_candidates` when assembling the state.

### D-3 — Expose in cognitive_snapshot

In `runtime/cognitive_snapshot.py`, include `creative_candidates` (≤3, `epistemic_status="imagined"` tag) in the snapshot for downstream readers.

---

## Constraints

- **DO NOT TOUCH `executive.py`** — FREEZE_V1_LOCK
- **DO NOT TOUCH `runtime/executive.py`** — creative_imagination must never call into it
- creative_imagination.py proposes → spine/CognitiveState carries → Executive reads from cognitive state (same pattern as learning_advice)
- Additive only — no existing code removed

---

## Tests

Write `tests/test_wo_creative001_imagination_wiring.py` — 4 ATs:
- AT-1: `creative_imagination.diverge()` returns a list (may be empty — non-critical path); `evaluate()` scores the candidates
- AT-2: spine.py imports `generate` from `faculties.creative.creative_imagination` (grep check)
- AT-3: `CognitiveState` has `creative_candidates` field (or equivalent)
- AT-4: executive.py has 0 references to `creative_imagination` (FREEZE_V1_LOCK clean)

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_wo_creative001_imagination_wiring.py -v`

---

## Return

Result card: `blender/agent_bus/builder/DONE/FROM_BUILDER_WO-CREATIVE-001_result.md`
Required: AT results (X/4 PASS) + commit hash + confirmation executive.py untouched.

---

*Board / Lead Architect — 2026-08-28*
