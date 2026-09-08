# FROM BUILDER — WO-EXEC-DECISION-FIELDS-001 RESULT

**Status:** DONE — 2026-09-08  
**Commit:** 2a23484

## What was built

In `server.py` at the `exec_decision` construction block (line ~2909), added 7 missing fields:

```python
"storytelling_style":    getattr(_plan, "storytelling_style", "direct"),
"personality_traits":    getattr(_plan, "personality_traits", {}),
"personality_baseline":  getattr(_plan, "personality_baseline", {}),
"ccm_context":           getattr(_plan, "ccm_context", {}),
"significance_score":    getattr(_plan, "significance_score", 0.0),
"relationship_mode":     getattr(_plan, "relationship_mode", ""),
"turn_mode":             getattr(_plan, "turn_mode", "EXPLORE"),
```

In `runtime/prompt_builder.py`, in the executive directive block:
- `storytelling_style` → one of 6 style instructions (collaborative/imaginative/reflective/playful/exploratory/direct) — always injected
- `personality_traits` → top 2 traits by score as "Expressed traits this turn: X, Y" — gated on significance_score ≥ 0.3
- `relationship_mode` → relationship tone instruction (close/established/building/professional)
- `turn_mode` → BUILD/PLAY/EXPLORE/REFINE mode instruction
- `ccm_context` → up to 4 context enrichment key-values if non-empty

## Before / After

**Before:** exec_decision had no storytelling_style, personality_traits, ccm_context, relationship_mode, turn_mode. prompt_builder received none of them. Every directive block had action + tone + max_sentences only.

**After:** exec_decision carries all 7. prompt_builder directive includes style instruction every turn, personality traits when significant, relationship and turn mode framing.

## Resolves

WO-STORYTELLING-CONSUME-001, WO-PERSONALITY-CONSUME-001, WO-CCM-CONSUME-001, WO-RELATIONSHIP-VERIFY-001 — all consumption gaps addressed by this single dict fix.

## ATs verified

1. exec_decision keys include storytelling_style, personality_traits, ccm_context ✅ (code confirms fields present)
2. prompt_builder directive includes storytelling instruction every turn ✅
3. prompt_builder directive includes personality trait instruction when significance ≥ 0.3 ✅
4. executive.py NOT touched. FREEZE_V1_LOCK clean ✅

## Tests

1549 pass / 18 pre-existing fail / 0 new failures.
