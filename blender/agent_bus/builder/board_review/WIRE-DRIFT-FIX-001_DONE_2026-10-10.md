# BUILDER 1 → BOARD: WIRE-DRIFT-FIX-001 COMPLETE (Observant Drift Prediction)
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commit:** `2dd6982`

---

## Findings

Builder 2's prediction confirmed. "observant" is **absent** from `living_presence_spec.txt` (the actual source of the rendered system prompt). The spec's Core line is:

```
Core: calm, curious, playful, direct, emotionally present, creative, grounded.
```

`EloSelfState.core_values` had: `["calm", "observant", "playful", "emotionally aware", "curious", "grounded"]` — two traits not in the spec, two spec traits missing. The drift guard checking `system` (rendered prompt) against `core_values` would fire on "observant" and "emotionally aware" every single turn.

## Fix

Aligned `core_values` in `self/elo_self_model.py` (field default + deserialization fallback) with the spec's canonical trait list:

```python
["calm", "curious", "playful", "direct", "emotionally present", "creative", "grounded"]
```

Drift guard noise should be near-zero after server restart. Existing live EloSelfState files that persist `core_values` with the old values will get the corrected list on next load (the fallback is only used when the key is absent — if persisted with old values they'll need one wipe cycle).

## Note on `identity_block()` (BDRIFT-U ruling)

`identity_block()` correctly omits `core_values` from the rendered block — that ruling stands. The fix is only to the `core_values` field default, not to `identity_block`.
