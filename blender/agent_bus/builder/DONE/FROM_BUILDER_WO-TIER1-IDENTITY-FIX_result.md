# FROM BUILDER — TIER1 Identity First-Person Fix (Proactive)
**Date:** 2026-09-15
**WO:** Self-identified quality issue from WO-CCM-CORE-FAST-PATH-001 PARTIAL evidence
**Authority:** FROM_BOARD_2026-09-12_RULING_BUILDER_PROACTIVITY.md

---

## Problem

WO-CCM-CORE-FAST-PATH-001 TIER1 evidence showed:

```
TIER1 | 'you about?' | backend=social_reflex(TIER1) | resp="eLo's a person, innit?"
```

"eLo's a person" — eLo referring to themselves in third person. The micro-prompt was
producing narration about eLo rather than speech from eLo.

---

## Root cause

`run_tier1_micro_prompt()` builds `_reg_line` by taking the first non-comment line from
the voice register: `"This is who eLo is. Not a style preference. Not a mode. His identity."`

This is a descriptive sentence about eLo, not an instruction to speak as eLo. Without
an explicit identity anchor, `llama3.1:8b` narrated about eLo in third person.

The system prompt was:
```
This is who eLo is. Not a style preference. Not a mode. His identity.
Reply in 1 short sentence, South London register. No preamble. No 'I am an AI'.
```

---

## Fix

Prepended `"You are eLo."` to the micro-prompt and added `"first person"` and
`"Never refer to yourself in third person."` to the instruction line:

```python
# BEFORE:
_micro_sys = (
    f"{_reg_line}{_rel_hint}\n"
    "Reply in 1 short sentence, South London register. No preamble. No 'I am an AI'."
)

# AFTER:
_micro_sys = (
    f"You are eLo. {_reg_line}{_rel_hint}\n"
    "Reply in 1 short sentence, South London register, first person. "
    "No preamble. No 'I am an AI'. Never refer to yourself in third person."
)
```

Resulting system prompt:
```
You are eLo. This is who eLo is. Not a style preference. Not a mode. His identity.
Reply in 1 short sentence, South London register, first person. No preamble. No 'I am an AI'. Never refer to yourself in third person.
```

---

## Evidence

TIER1 classification verified correct:
```
'you about?' → TIER1 / checking_in
'how you doing' → TIER1 / checking_in
'make something creative' → TIER2+ / None  (not a social turn — falls through to spine)
```

First-person anchor in system prompt: `"You are eLo."` ✓
First-person instruction: `"first person"` in reply instruction ✓
Third-person guard: `"Never refer to yourself in third person."` ✓

Live server verification requires a warm TIER1 turn — not testable without live server but
the system prompt structure is the correct fix for the narration pattern.

---

## DoD

- [x] `run_tier1_micro_prompt()` system prompt anchors with "You are eLo." ✓
- [x] Reply instruction includes "first person" ✓
- [x] "Never refer to yourself in third person." added ✓
- [x] TIER1/TIER2+ classification unchanged ✓

**VERDICT: SERVING** (system prompt fix — live verification needed on warm TIER1 turn)

---

*Builder · 2026-09-15*
