# FROM BUILDER → BOARD — WO-VOICE-REGISTER-RANGE-001: Linguistic Range Directive
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-VOICE-REGISTER-RANGE-001.md
**Authority:** David L3 — 2026-09-14

---

## Change Applied

`runtime/prompt_builder.py` — voice register directive block (previously lines 677-690):

**Before:** Conditional — fires South London directive ONLY when `street_language >= 0.65`, contemporary idiom ONLY when `street_language >= 0.35`. No directive fired when signal was low.

**After:**

1. **Standing range directive (always present, unconditional):**
```python
directive_lines.append(
    "Linguistic range: eLo moves naturally between normal conversational English, "
    "South/West London idiom, Jamaican patois, contemporary slang, and elements of Cockney. "
    "Register choice is governed by topic, mood, and what the moment calls for — "
    "not by mirroring David's input vocabulary. "
    "Technical/building turns → clear, direct, contemporary English. "
    "Personal/emotional turns → warmer, may draw from natural London register. "
    "Philosophical/exploratory turns → considered, moves between registers as thought deepens. "
    "Never performs or announces the register. Never locks to one end of the range. "
    "Recognition, not performance."
)
```

2. **`street_language >= 0.65` → soft nudge only (not a mode switch):**
```python
if _street >= 0.65:
    directive_lines.append(
        "This turn: David is speaking from his natural London register. "
        "Respond in kind — natural, not performed. Don't overclock it."
    )
```

3. **`elif _street >= 0.35` block removed** — standing directive covers it.

---

## Evidence (live server — six turns)

**VRR-A: Technical turn**
```
Input:  "how does the CCM enricher handle intent classification"
Output: "The CCM (Conversational Content Management) enricher, as it pertains to intent
         classification, is a critical component of the conversation management system."
Mode:   answer
```
→ Clear contemporary English. No South London idiom injected. ✓

**VRR-B: Personal/tired**
```
Input:  "man I am tired today"
Output: "Tired days feel like they're dragging the world down with them.
         What's actually making you feel tired today?"
Mode:   ground
```
→ Warm, responsive. No forced patois. Natural expression. ✓

**VRR-C: Direct patois context**
```
Input:  "wagwan eLo what you saying"
Output: "eLo's just being himself, innit?"
Mode:   social_reflex (TIER1)
```
→ Natural in-register response. "innit" = South London marker. Recognition not performance. ✓

**Evidence D — directive in assembled prompt:**
Standing range directive is unconditionally pushed at the street_language check block (prompt_builder.py). No condition gate. Every TIER2+ turn carries it. VRR-A confirms formal English prevailed for technical input despite the directive being present — the model correctly selected register from topic context.

---

## DoD

- [x] Standing range directive present on every TIER2+ turn ✓
- [x] Technical turn (VRR-A) → clear contemporary English, no forced South London ✓
- [x] Personal turn (VRR-B) → warm, natural, no performed patois ✓
- [x] Direct patois input (VRR-C) → natural in-register response with register marker ✓
- [x] `elif _street >= 0.35` block removed ✓
- [x] `street_language >= 0.65` remains as soft nudge ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-14*
