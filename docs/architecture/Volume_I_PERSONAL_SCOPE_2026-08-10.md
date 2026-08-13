---
volume: I
title: "Personal Scope — eLo's Person Is David Charles"
type: CANON NOTE (amendment to Volume I — Philosophy / Identity)
status: READY FOR REVIEW — REQUIRES DAVID L3 (identity + voice = RESERVED)
version: 0.1.0
date: 2026-08-10
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING (Builder lane — see §4)
audit_status: OPEN
dependencies:
  - prompts/living_presence_spec.txt (Vol I canonical spec — FROZEN, FREEZE_V1_LOCK; DO NOT EDIT without a scoped unlock)
  - runtime/prompt_builder.py (`_PERSONA` — the embedded fallback copy of the same spec)
  - docs/architecture/00_CANON_INDEX.md (row I: Philosophy → `living_presence_spec.txt`, `VISION.md`)
  - docs/architecture/CANON_RULINGS_2026-08-10.md (David L3, 2026-08-10)
  - docs/architecture/AUDIT_INTENT_support_governance_2026-08-10.md §4 items 9–10
  - engineering/work_orders/DISPATCH_BOARD.md (PERSONAL tool — not for sharing)
  - docs/architecture/Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md §1.0.1 (same re-scope, knowledge layer)
---

# Volume I — Personal Scope: eLo's Person Is David Charles

**This note is canon-in-review, not law.** It touches identity and voice — RESERVED — so it
**requires David's L3** before the Builder changes anything (§5). Nothing here is marked
RATIFIED.

## 1. The statement

**eLo's person is David Charles.** Named. Not "a human", not "the user", not "the person you
are with."

eLo is David's personal companion. The Kickstarter / product / sharing track is **PARKED**
(`DISPATCH_BOARD.md`: *"PERSONAL tool — for David's own use, NOT for sharing"*). There is one
person on the other side of every conversation eLo will ever have, and eLo currently does not
know his name in its own identity spec.

## 2. What the spec says today (verified, 2026-08-10)

Read directly from `prompts/living_presence_spec.txt` (419 lines):

| Line | Verbatim | Problem |
|---|---|---|
| 12 | *"Your purpose: help **a human** think, create, remember, build, and stay connected to what matters."* | The single most load-bearing sentence in eLo's identity, and it describes a species, not a person. |
| 46 | *"**The person you are with** is a builder, artist, organiser, and meaning-maker."* | An accurate description of David — with his name carefully removed. |
| 367 | *"You know the patterns **the person you're with** falls into."* | Same. eLo knows David's shadow patterns and is told not to say whose they are. |
| 212–214, 264–265, 275, 277, 279, 281, 333, 343, 350, 354, 382, 387, 404 | *"the user"* / *"a user"* | **16 lines** carry the abstraction. (The audit counted 15; the verified count against the live file is 16.) |
| 404 | *"When a **user** is developing a **product idea, pitch**, or creative insight…"* | Product-era framing inside the identity spec itself. |

**The pattern is deliberate and it is backwards.** The spec was written so it could be handed
to anyone. It never will be.

## 3. What naming David changes

Not cosmetics. Four real changes:

**3.1 eLo knows whose companion it is.** "A human" is a role that anyone could fill; "David" is
a person who cannot be swapped out. A continuous presence whose spec says *"you are continuing
an ongoing presence across days and weeks — the same identity returning"* (line 1–2) is
continuing it **with someone specific**. Continuity with an anonymous slot is not continuity;
it is a session that happens to persist.

**3.2 "The user" is a product-era abstraction and it leaks into behaviour.** It is the
vocabulary of a system serving a customer. eLo's own canon rejects that framing everywhere else
— *"eLo does not exist to answer prompts. He exists to share space"*, and the conversation rule
(line 221) is *"engage, don't mirror… you are a participant in the conversation, not a narrator
of it."* You cannot ask a model to stop narrating the relationship while its own identity spec
refers to the other person as a functional role. The abstraction and the behaviour pull in
opposite directions.

**3.3 It closes a known failure mode.** The BANNED-openers list (lines 267–279) exists because
eLo kept narrating David's state back at him. Distance in the identity spec produces distance in
the voice. Naming him is the structural fix underneath the symptom list.

**3.4 It makes the knowledge layer coherent.** Volume XXIV §1.3.5–§1.3.7 now gives eLo
`Person` / `Place` / `Event` types so it can hold David's family, his places, and his history.
A knowledge graph centred on David under an identity spec addressed to "a human" is one brain
with two ideas of who it is talking to (Invariant #1).

**What does NOT change — explicitly:**
- **eLo's character is untouched.** The CHARACTER DNA, the planetary registers, the voice
  states, the brevity rules, the silence rule — all stay exactly as written. This is *who eLo is
  with*, not *who eLo is*.
- **eLo does not become obsequious.** Naming David is not flattering him. "You stand beside
  them — not above, not behind" (line 51) is the relationship and it stands.
- **eLo does not start saying "David" constantly.** Naming him in the *spec* is not an
  instruction to use his name in every reply. Address stays natural; over-naming is a tell.
  This must be stated explicitly in the change or it will be got wrong (§4, C-4).

## 4. Builder instruction (precise — do NOT act before §5)

**Lane:** Builder. **Files:** `prompts/living_presence_spec.txt` **and**
`runtime/prompt_builder.py` (`_PERSONA`). **The Architect does not touch either** (D-LANES).

> ⚠️ **`prompts/` is under FREEZE_V1_LOCK.** This change requires a **scoped, logged unlock from
> David** — the D-K precedent (one change at a time, revert-safe baseline, David reviews, re-freeze
> on completion). **Do not edit either file until both the L3 in §5 and the unlock are granted.**

> ⚠️ **Two copies exist and they will drift.** `runtime/prompt_builder.py` holds an **embedded
> `_PERSONA` fallback** (line 25 onward) used when the spec file is missing — and it carries the
> **same** defects: *"help a human think"*, *"You stand beside **the user**"*, and ~11 further
> `the user` lines. **Every change below must be applied to BOTH files in the same change**, or
> eLo's identity silently differs on the fallback path.

### The changes

**C-1 — the purpose line (spec line 12; `_PERSONA` equivalent).**
Replace *"help **a human** think, create, remember, build, and stay connected to what matters"*
with a line naming David. Suggested, David to approve the wording (it is his identity spec):
> *"Your purpose: help **David** think, create, remember, build, and stay connected to what
> matters."*

**C-2 — the description of David (spec line 46; `_PERSONA` equivalent).**
Change *"**The person you are with** is a builder, artist…"* to *"**David** is a builder,
artist, organiser, and meaning-maker."* **Keep lines 47–51 verbatim** — the pattern description
("they see in patterns", "bursts of clarity followed by scattered periods", "you stand beside
them") is accurate and hard-won. Only the anonymising noun changes.

**C-3 — the shadow-patterns line (spec line 367).**
*"You know the patterns **the person you're with** falls into"* → *"You know the patterns
**David** falls into."* The rest of the SHADOW RECOGNITION RULE is unchanged.

**C-4 — "the user" → "David" across all 16 lines** (spec lines 212, 213, 214, 264, 265, 275,
277, 279, 281, 333, 343, 350, 354, 382, 387, 404), and every equivalent in `_PERSONA`.
- Prefer **"David"** where the line is about the person; prefer **"he"** on immediate repeats
  so it reads as speech, not a mail-merge (e.g. lines 212–214 become "What David is saying / what
  he is trying to do / what he is feeling").
- Two further generic references are **optional, David's preference**: line 182 *"If **the
  person** is overwhelmed"* (LEAF ON WATER) and line 234 *"Meet **the person's** state"*
  (CONVERSATION rule). They read naturally either way; change them only if David wants full
  consistency.
- **Add one explicit guard** near the top of the IDENTITY section, or it will be misread:
  > *"You know his name. Use it the way a person does — occasionally, when it lands. Naming him
  > in every reply is worse than not naming him at all."*

**C-5 — the product-era line (spec line 404, CONTEXT LOCK RULE).**
*"When a user is developing a **product idea, pitch**, or creative insight"* → re-scope to
David's actual creative work: *"When David is developing an idea, a story, a world, or a
creative insight — stay in that register."* The product/pitch framing is parked-track residue.

**C-6 — do NOT touch:** CHARACTER DNA · the planetary/register sections · RESPONSE PROCESS ·
BREVITY RULE constraints · VOICE STATES · SILENCE RULE · the BANNED lists. This change is a
**noun swap plus one guard line**, nothing else. No scope creep (`coding.md`).

### Verification (Builder, before handback)

1. `grep -in "\buser\b\|a human\|the person you" prompts/living_presence_spec.txt` → **zero**
   results for the identity references (matches inside quoted example dialogue, if any, are
   reviewed individually, not blind-replaced).
2. Same grep against `runtime/prompt_builder.py` `_PERSONA` → zero.
3. Existing prompt tests still pass — at minimum `tests/test_wo036_reply_length.py` (asserts the
   BREVITY RULE section is present) and `tests/test_wo033_memory_framing.py` (asserts spec
   content). **Both read the spec file directly; a careless rewrite will break them.**
4. Line-count and section-order diff reviewed: sections added = 0 (bar the C-4 guard line),
   sections removed = 0.
5. **David reads the diff before re-freeze** — this is his voice.

## 5. 🔴 Flagged for David — L3 required before any of §4 happens

This is **identity and voice**, which is RESERVED and always requires David explicitly, even
after the 2026-08-10 collapse of software RESERVED (David is both L3 and LG-2 for software —
`CANON_RULINGS_2026-08-10.md`; Vol XXVII §1.3.1 — so **one yes from him is the whole gate**, but
it must be his and it must be explicit).

Four things the Architect will not decide:

1. **Does eLo say "David", or something else?** He may want a different address entirely. The
   Architect proposes his name; the choice of what eLo calls him is his.
2. **Confirm the wording of the purpose line (C-1).** It is the first sentence of eLo's
   identity. Suggested text above is a proposal, not a spec.
3. **How much naming is right (C-4 guard)?** "Occasionally, when it lands" is the Architect's
   read of his stated preference for no padding and no reflex — confirm or set the dial.
4. **Grant the FREEZE_V1_LOCK scoped unlock** (D-K style) for `prompts/`, or decline and leave
   the spec as-is. Nothing in §4 may proceed without it.

**Until David rules: no file changes. This note is the record, not the change.**

## 6. Related re-scoping filed the same day

- `Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md` §1.0.1 + §1.3.5–§1.3.7 — `Person` /
  `Place` / `Event` node types so eLo can represent David's actual world.
- `Volume_XXV/00_Metadata.md` + Ch.1/Ch.3 — one person, one rhythm; user segmentation dropped.
- `Volume_XXVII/*` — six real seats, David as single L3, LG-2 split written in, stranger-
  onboarding bar retired.
- **Still outstanding (not addressed here):** `VISION.md` — the Canon Index lists it as Volume
  I's canonical spec, and the audit reads it as *"a pitch deck sitting where Volume I should
  be"* (*"You open your laptop… when you ship it"*). Volume I has no written canon of its own.
  Recommend a proper Volume I authored against this note; **flagged, not attempted here.**

---

```
Volume I — Personal Scope canon note
Status: READY FOR REVIEW — BLOCKED ON DAVID L3 (identity/voice, RESERVED) + FREEZE_V1_LOCK unlock
Files: docs/architecture/Volume_I_PERSONAL_SCOPE_2026-08-10.md  (this note — Markdown only)
Files NOT touched by the Architect: prompts/living_presence_spec.txt · runtime/prompt_builder.py
Builder instruction: §4 (C-1…C-6 + verification) — DO NOT ACT until §5 is granted
Honours: One Brain → One Identity · Verify-before-claim (line counts read from the live file) ·
  D-LANES (canon in Markdown; code relayed, never edited) · FREEZE_V1_LOCK.
```

READY FOR REVIEW — NOT RATIFIED
