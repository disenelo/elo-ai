# FROM BUILDER → BOARD — CCM fast path: venting intent gap
**Date:** 2026-09-14
**Authority:** WO-CCM-CORE-FAST-PATH-001 spec + CCM_SPEC_v1.2.md INTENT MATRIX
**Gap:** "venting" listed in WO TIER 1 triggers and CCM INTENT MATRIX, but not in initial implementation

---

## Gap found

WO-CCM-CORE-FAST-PATH-001 specifies TIER 1 triggers as:
> CCM intent_category = greeting / checking_in / farewell / **humour / venting** AND raw word count ≤ 12

CCM_SPEC_v1.2.md INTENT MATRIX includes "Venting" as a category.

Initial implementation of `runtime/social_reflex.py` included greeting/checking_in/farewell/humour but omitted venting.

---

## Fix applied

**`runtime/social_reflex.py`:**
- Added `_VENTING_PATTERNS` tuple: "ugh", "argh", "ffs", "this is so frustrating", "this sucks", "not working", "i give up", "i hate this", "stressed", "overwhelmed", "can't cope", "losing it", "done with this", "so tired", "burnt out", "can't deal"
- Added venting detection to `classify_social_intent()` (after humour patterns)
- Added "venting" to `_SOCIAL_INTENTS` frozenset
- Added venting-specific clause in `classify_tier()`: venting always → TIER 1, never TIER 0 (even single-word "ugh" deserves a warm micro-prompt response, not a voice pool reply)

**`faculties/ccm/ccm_enricher.py`:**
- Updated comment to include venting in the category list

---

## Verification

```
'ugh'          → tier=TIER1, intent=venting  ✓
'this sucks'   → tier=TIER1, intent=venting  ✓
'i give up'    → tier=TIER1, intent=venting  ✓
'Yo'           → tier=TIER0, intent=greeting  ✓  (unaffected)
'wagwan'       → tier=TIER0, intent=greeting  ✓  (unaffected)
'how you doing'→ tier=TIER1, intent=checking_in  ✓  (unaffected)
'remind me to call mum' → tier=TIER2+, intent=None  ✓  (capability escalation unaffected)
```

Venting → TIER 1 only (no TIER 0): "ugh" alone would be 1 word and could have hit TIER 0, but the venting guard ensures it goes to LOCAL Ollama for a warm response, not a canned voice pool reply.

---

*Builder · 2026-09-14*
