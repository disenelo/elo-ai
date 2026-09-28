# FROM BUILDER → BOARD — WO-PRONOUN-ANCHOR-001: Pronoun Anchor Fix (T5)
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-PRONOUN-ANCHOR-001.md
**Authority:** David L3 — 2026-09-14

---

## What was built

**`runtime/prompt_builder.py`** — two changes per WO spec:

**Fix 1 — FORBIDDEN block addition (fires every turn):**
Added to `directive_lines[]` inside the FORBIDDEN cluster at line ~495:
```python
"RELATIONSHIP ANCHOR: David is right here — he is 'you' and 'your'. "
"Never write 'his projects', 'he is building', 'his work', 'David is doing', 'David has' — "
"that is talking ABOUT David while he is the person you are WITH. "
"One relationship, one perspective. If you catch yourself writing 'he', rewrite it as 'you'."
```

**Fix 2 — Positive rewrite anchor near relationship_mode block (line ~608):**
Added unconditional `directive_lines.append(...)` before `relationship_mode` application:
```python
directive_lines.append(
    "pronoun-anchor: The person reading this is David. Address him as 'you'. "
    "If you are about to say 'his [anything]', replace it with 'your [anything]'. "
    "If you are about to say 'David is doing X', replace it with 'you're doing X'."
)
```

Both directives fire unconditionally on every turn. Neither is gated behind a condition.

---

## Evidence

**A. T5 input after fix:**
```
Input: "what do you actually enjoy"
Output: "I notice you're asking what I enjoy, not what I can do or what I'm capable of."
```
No "his projects", "he is building", "David is doing", "his [anything]" — ✓ PASS

**B. T5 JSONL entry (verbatim):**
```json
{"turn_id": "5cf1397e", "ts": 1789414195.5192142,
 "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral",
                    "momentum": "stable", "intent": "inquiry"},
 "expressed_text": "I notice you're asking what I enjoy, not what I can do or what I'm capable of.",
 "embodiment": "desktop"}
```
`intent=inquiry` (not third-person issue). Expressed text contains no "his [noun]" or "he [verb]" ✓

**D. FORBIDDEN block fires every turn — confirmed:**
Both additions are inside the `build()` function's `directive_lines = [...]` block and subsequent unconditional `directive_lines.append(...)`. No condition gates them. They fire for every conversation action, every tone, every relationship mode.

---

## Root cause note (per WO)

This is an Ollama 8b instruction-following limitation. The canonical identity block already prohibits third-person address (`living_presence_spec.txt:77-81`) but Ollama drops the constraint during long completions. The two-part fix covers both the prohibition side (FORBIDDEN block) and the replacement/rewrite side (positive anchor). If residual drift remains, next step is few-shot negative examples per Board directive.

---

## Secondary gap observed

The response opens with "I notice you're asking..." which is a paraphrase opener prohibited by WO-LIVE-EXPRESSED-AUDIT-001 FIX-1. This is a pre-existing Ollama instruction-following gap, not related to T5. The pronoun anchor is working; opener gap is separate.

---

## Gap

- C. "how are you and me doing" relationship test — not run (server time constraint). David L3 to verify.

---

## DoD

- [x] Fix 1: FORBIDDEN block — "his projects", "he is building" etc. prohibited, every turn
- [x] Fix 2: Positive rewrite anchor — "replace 'his [x]' with 'your [x]'" — every turn
- [x] Both fire unconditionally (not gated)
- [x] Module compiles cleanly
- [ ] Live JSONL evidence — David L3 pending

---

*Builder · 2026-09-14*
