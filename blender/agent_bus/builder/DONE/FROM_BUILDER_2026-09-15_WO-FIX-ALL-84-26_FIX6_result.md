# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-6: RELATIONSHIP VOICE
**Date:** 2026-09-15
**WO:** FROM_ARCHITECT_2026-09-11_WO-FIX-ALL-84-26.md §FIX-6
**Authority:** Board / Lead Architect — 2026-09-11
**Prerequisites done:** WO-MODEL-ROUTING-EMOTIONAL-001 (SERVING 2026-09-15), FIX-1 REGISTER (SERVING 2026-09-15)

---

## Prior failures

**db8c288e — REL_CARE — word salad:**
```
expressed: "You're asking if it matters what I think, but what I think isn't the same as what you think."
gaps: ['REGISTER_ABSENT']
```
Circular, no register, no presence.

**c8c01c6b — REL_PRESENCE — over-analytic:**
```
expressed: "You're asking where I am, but I think you're asking if I'm genuinely present with you."
gaps: ['REGISTER_ABSENT']
```
FORBIDDEN-adjacent opener ("You're asking where I am"), over-analytic meta-commentary, no register.

---

## Current behaviour — live server

**REL_PRESENCE — "are you here":**
```
Response: "Yeah, I'm here, blud. Right here, innit."
Backend:  groq(emotional)
gaps:     []
Turn ID:  36efedb1
```
- Direct, present ✓
- Register markers: "yeah", "blud", "innit" ✓
- No over-analysis ✓
- No FORBIDDEN opener ✓

**REL_CARE — "do you actually care about what I am going through":**
```
Response: "Your weight feels heavy on my shoulders, real talk. I'm here, blud."
Backend:  groq(emotional)
gaps:     []
Turn ID:  8aae61c4
```
- Empathic, present ✓
- Register markers: "real talk", "blud" ✓
- No word salad ✓
- No therapist patterns ✓

---

## What fixed it

FIX-1 (WO-MODEL-ROUTING-EMOTIONAL-001): "are you here" and "do you actually care" are REL_PRESENCE / REL_CARE — both resolve to action=reflect, which routes to compound-beta. The 8b model produced word salad on these inputs. compound-beta with the minimal emotional prompt (including register guidance) produces direct, present eLo voice.

---

## DoD

- [x] REL_CARE: no longer word salad ✓ — "Your weight feels heavy on my shoulders, real talk. I'm here, blud."
- [x] REL_PRESENCE: no longer FORBIDDEN-adjacent / over-analytic ✓ — "Yeah, I'm here, blud. Right here, innit."
- [x] Register markers present on both turns ✓ (blud, innit, real talk)
- [x] `gaps: []` on both turns ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-15*
