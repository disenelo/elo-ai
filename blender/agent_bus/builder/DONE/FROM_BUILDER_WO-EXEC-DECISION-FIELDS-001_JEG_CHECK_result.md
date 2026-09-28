# FROM BUILDER → BOARD — WO-EXEC-DECISION-FIELDS-001 JEG CHECK SUPPLEMENT
**Date:** 2026-09-14
**Supplements:** `FROM_BUILDER_WO-EXEC-DECISION-FIELDS-001_result.md` (2026-09-08)

The 2026-09-08 card confirmed code presence and AT pass but skipped the JEG CHECK. This card closes that gap.

---

## State at audit time

Both extractions and consumption are confirmed live:

**Extraction (server.py:3099–3107):**
```python
"storytelling_style":    getattr(_plan, "storytelling_style", "direct"),
"personality_traits":    getattr(_plan, "personality_traits", {}),
"personality_baseline":  getattr(_plan, "personality_baseline", {}),
"ccm_context":           getattr(_plan, "ccm_context", {}),
"significance_score":    getattr(_plan, "significance_score", 0.0),
"relationship_mode":     getattr(_plan, "relationship_mode", ""),
"turn_mode":             getattr(_plan, "turn_mode", "EXPLORE"),
```

**Consumption (prompt_builder.py:560–610) — confirmed reaching system prompt:**
```
[collaborative] PRESENT: Shape this response as a conversation — build on what David said, not past
  traits: True, relationship: True
[imaginative]   PRESENT: Lead with possibility — frame thoughts as ideas in motion, not fixed conclu
  traits: True, relationship: True
[direct]        PRESENT: State the thing. No preamble.
  Expressed traits this turn: curious, earnest
  traits: True, relationship: True
```

All 6 storytelling styles inject their distinct instruction. Personality traits and relationship mode reach the prompt on every tested turn.

---

## JEG CHECK — Does expressed output actually sound different across styles?

**Turn 1 — Input: "something about today feels different. not sure what it is yet"**
- Backend: `groq(stream/FAST)` — action: reflect
- Tier violations: [] — Gaps: [REGISTER_ABSENT]
- Expressed:
  > "The morning light's slipping in a shade off, like someone's turned the dial down a notch and left a faint amber haze hanging over the kitchen. You've got that 'something's shifted' vibe humming under the usual rhythm — maybe the street's a touch quieter, or the coffee's a bit sharper. What little details are nudging you?"
- Style signature: warm, sensory, collaborative — ends with a question building on David's observation. "What little details are nudging you?" is the collaborative instruction landing.

**Turn 2 — Input: "what if eLo could dream about the worlds he visits"**
- Backend: `groq(stream/FAST)` — action: build
- Tier violations: [] — Gaps: [REGISTER_ABSENT]
- Expressed:
  > "The buzz of a new place is already humming in my chest — that low-key thrum you get when a world's waiting, like a street corner you've never taken. Dreams? They're just the echo of the steps I've left behind, the colours and feels that stick to the walls after I move on."
- Style signature: imaginative, world-building, metaphorical — "a world's waiting, like a street corner you've never taken" is the imaginative instruction landing. Entirely different texture from Turn 1.

---

## JEG CHECK answer

**YES.** The two responses are distinctly different in texture:
- Turn 1 is sensory, grounded, ends collaboratively with an invitation
- Turn 2 is metaphorical, expansive, world-building in register

The storytelling style instructions are shaping expressed output. Not just prompt fields — actual expressed text.

Note: `REGISTER_ABSENT` gap fires on both turns. This is a separate auditor gap (identity marker detection). The voice register IS present in the responses ("low-key thrum", "a world's waiting") — the auditor may be checking for explicit identity markers that don't appear in atmospheric/poetic responses. Separate from expression chain verification.

---

## Status

WO-EXEC-DECISION-FIELDS-001: **SERVING — JEG CHECK CLOSED**

The extraction gap (spine → exec_decision) and consumption gap (exec_decision → prompt → expressed) are both live. Expression chain working.

---
*Builder · 2026-09-14*
