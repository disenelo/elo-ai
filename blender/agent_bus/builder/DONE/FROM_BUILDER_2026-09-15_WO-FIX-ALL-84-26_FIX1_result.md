# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-1: REGISTER_ABSENT
**Date:** 2026-09-15
**WO:** FROM_ARCHITECT_2026-09-11_WO-FIX-ALL-84-26.md §FIX-1
**Authority:** Board / Lead Architect — 2026-09-11

---

## Diagnosis

**Directive present in assembled prompt?** YES — unconditionally (WO-VOICE-REGISTER-RANGE-001, 2026-09-14).

`runtime/prompt_builder.py` line 683:
```python
directive_lines.append(
    "Linguistic range: eLo moves naturally between normal conversational English, "
    "South/West London idiom, Jamaican patois, contemporary slang, and elements of Cockney. "
    ...
    "Recognition, not performance."
)
```
No condition gate. Present on every TIER2+ turn.

**Why REGISTER_ABSENT was still firing after WO-VOICE-REGISTER-RANGE-001:**
Two causes:
1. **8b model (Ollama) ignoring the directive** — model capacity issue. llama3.1:8b does not reliably use South London register markers even when instructed via the system prompt.
2. **Groq emotional path missing register guidance** — the minimal emotional system prompt used by compound-beta (added by WO-MODEL-ROUTING-EMOTIONAL-001) did not include the register directive. Poetic English responses ("Stillness holds us...") pass eLo voice checks but fail REGISTER_ABSENT.

---

## Changes Applied

**`runtime/backend_router.py`** — minimal emotional system prompt (route_streaming emotional override):

Added register guidance to the compound-beta emotional prompt:
```python
"Linguistic register: eLo moves naturally between normal English, South/West London idiom "
"(yeah, innit, man, blud, real talk, right.), and contemporary slang. "
"Register choice follows the moment — not performance. "
"Personal/emotional turns → warmer, may draw from London register when it fits.\n\n"
```

---

## Evidence — live server

**Input:** "man I feel so low today, everything feels heavy"
**Action:** ground (TIER2+ — not intercepted by social_reflex on this framing)
**Backend:** groq(emotional)

```
[EMO_CHECK] action=ground sig=0.000 is_emo=True groq_avail=True
[EMO_WIN] returning groq(emotional) for action=ground
[eLo] backend=groq(emotional)+calendar action=ground
```

**Expressed output:**
> "Heavy days hit hard, but you're still here, bruv. Keep breathing, one step at a time, innit."

**Audit gap check:**
- `gaps: []` — REGISTER_ABSENT not fired ✓
- Register markers present: "bruv" + "innit" ✓
- No FORBIDDEN opener ✓
- No therapist pattern ✓

---

## Directive → expressed output chain confirmed

| Step | Status |
|---|---|
| Directive in assembled prompt (prompt_builder.py line 683) | ✓ Confirmed — unconditional |
| Directive included in Groq emotional path (route_streaming minimal prompt) | ✓ Added 2026-09-15 |
| Expressed output contains register markers | ✓ "bruv" + "innit" |
| REGISTER_ABSENT gap in audit | ✓ Cleared (`gaps: []`) |

---

## Remaining gap (8b model capacity — not this WO's scope)

Non-emotional TIER2+ turns still route to Ollama llama3.1:8b. The 8b model ignores the register directive. REGISTER_ABSENT will still appear on formal/neutral 8b responses (WO-FIX-ALL-84-26 §FIX-1 predicted this: "model capacity, partially fixed by routing WO").

This affects: build, answer, challenge, plan, explore actions on TIER2+ non-emotional turns. Each additional emotional action class moved to compound-beta reduces the footprint. For non-emotional TIER2+ turns, a separate routing decision (David L3) is needed to route those through a larger model.

---

## DoD

- [x] Directive confirmed in assembled prompt (unconditional) ✓
- [x] One real server turn: directive in prompt AND expressed output reflects it ✓
- [x] Expressed output: "Heavy days hit hard, but you're still here, bruv. Keep breathing, one step at a time, innit." ✓
- [x] Register markers present: "bruv", "innit" ✓
- [x] `gaps: []` — REGISTER_ABSENT cleared on this turn ✓

**VERDICT: SERVING**
(Note: 8b non-emotional turns will still show REGISTER_ABSENT — model capacity gap, not this WO. Routing WO partially addresses this class as predicted.)

---

*Builder · 2026-09-15*
