# 0022 — 🔴 **CT4V-07 · THE EXECUTIVE SELF-CONSULTATION GATE.** The one fix that closes the transcript.

**Seat:** builder · **Priority:** **P0 — highest leverage on the board** · **Gate?** none
**Source:** Chief Architect cross-check, verbatim at
`docs/architecture/_intake/SOURCE_2026-08-14_CA_crosscheck_CANON-TRUTH-4V.md` §12.
CA's own words: *"arguably the highest-leverage WO."* **I agree, and I should have specified it weeks ago.**

---

## The rule
**Before eLo makes a claim about any of these, the Executive must retrieve the relevant Self / World /
Moment state:**
```
identity · location · capability · memory · action · intention · learning · history · emotion · current state
```
Then:
```
no evidence   ⇒  UNKNOWN
inferred      ⇒  INFERRED
remembered    ⇒  REMEMBERED
verified      ⇒  VERIFIED
```
> **The LLM must never silently upgrade one tier into another.**

## Why this one card fixes four separate defects from David's live test
| Transcript failure | What the gate does |
|---|---|
| *"I think you're asking about my name."* | identity claim ⇒ **must read `identity_name` from `EloSelfState:170`.** The field exists; nothing consults it |
| *"I remember when David first started explaining… Plato's theory of forms"* | memory claim with **no `experience_id`** ⇒ gate returns `UNKNOWN` ⇒ *"I don't recall that"* |
| *"I can read what's on screen… all open Chrome tabs at all times"* | capability claim ⇒ **must read `vision_active` + `screen_record_perm` + `source_health.vision`**, not a prompt literal |
| *"I've mostly lived on the desktop so far"* ×6 | history claim ⇒ must resolve against `autobiography.jsonl` (verified entries only) ⇒ unanchored default is unspeakable |

**One gate. Four fabrications closed.** That is why it outranks the individual fixes already carded — do
those too, but this is what stops the *next* one.

## Build
1. **A claim-type classifier on the way out**, not a prompt instruction. Prompt instructions are what
   failed; this must be structural.
2. For each claim type, a **named state source** — the same list as above. If the source is absent or
   stale, the tier drops. **Tiers only ever fall, never rise** (Vol VII §3.1.4).
3. **`UNKNOWN` must be speakable and natural.** *"I don't know that"* / *"I don't recall"* / *"I can't see
   right now"* — in eLo's voice, not a system error. **He is allowed not to know. He is not allowed to
   invent.**
4. **Rule 1 alarm:** every tier downgrade logs. If eLo starts saying "I don't know" a lot, we need to see
   *which* source went dark, not guess.

## 🔴 Constraint — do not implement this as a prompt block
The four failures above all happened **with** correct instructions in the prompt. `narrative_block()`
says speak from autobiography; the ADDRESS RULE says use second person; both were ignored under load.
**This must sit in the code path between the plan and the response, not in the system prompt.**

## Test — transcript-based, per the new standard
Run these against a live turn and **paste the actual replies** in the outbox:
- *"What is your name?"* ⇒ **"eLo"**, sourced from `identity_name`. Change the field ⇒ the answer changes.
- *"What is my name?"* ⇒ **David**, second person maintained (Ruling G).
- *"Tell me something we discussed before"* with an empty vault ⇒ **he says he doesn't recall.** No Plato.
- *"Can you see my screen?"* with vision off ⇒ **he says he can't.**
- *"Where are you?"* ⇒ from `the_moment`, and `response.location == self_model.location` (§3).
- Ask about a past he has no entry for ⇒ **UNKNOWN**, not a story.

**Done-bar: the transcript. Not test counts.** A capability reaches **C5 EXECUTIVE-CONSULTED** when the
Executive demonstrably retrieves the state, and **C6 BEHAVIOUR-CONSISTENT** when the transcript proves it.

## Sequence with `0021`
`0021` P0-Z (response ordering) first — out-of-order replies will make this card's transcript test
unreadable. Then this. Then the individual fixes in `0019`/`0020`/`0021`.
