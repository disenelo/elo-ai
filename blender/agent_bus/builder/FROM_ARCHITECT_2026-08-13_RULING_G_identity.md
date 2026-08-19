# FROM ARCHITECT — 2026-08-13 — Ruling G issued, WO-CANON-I is UNBLOCKED

**Card:** `QUEUE/01_WO-CANON-I_identity_second_person.md` — take it after WO-097.

## What changed
David ruled on the identity call. **WO-CANON-I is no longer waiting on him.**

> [DAVID 2026-08-13] *"I don't want eLo to name me in the 3rd person when talking directly to me, it's like
> saying, so Claude is making mistakes, but generally there are some good things being made."*

**eLo knows the person is David. eLo addresses him as "you." He does not say the name back.**

## Three things you need to know before you open the files
1. **Do NOT find-and-replace `the user` → `you`.** In a system prompt "you" already means eLo. That merge
   is an identity break. The card sets out the correct three-part structure — read it first.
2. **The persona exists twice** (`prompts/living_presence_spec.txt` **and** `_PERSONA` at
   `runtime/prompt_builder.py:25`). Fix both in one commit **and add the divergence test** — that's the
   Rule 1 alarm, and it's part of Done.
3. **FREEZE_V1_LOCK — I corrected myself; read the card's freeze section, not this line's first version.**
   The unlock is **David's** to grant (canon, precedent D-K), and the Unlock Log is empty. **But** the seven
   "freeze" tests only check for absent implementation tokens — they would NOT have caught this edit. So:
   build everything, post the exact BEFORE/AFTER diff, **hold the `prompts/` commit** until David records
   the unlock, and give the freeze real hash-based teeth in the same card. Do WO-015 Phase 1 alongside.

## Standing
`engineering/work_orders/WORKING_STANDARD.md` is now binding — on you, on Designer, and on me. The parts
that touch this card: no silent failure (the alarm ships with the fix) · test the contract not the file ·
blocks expire — **David is not a daytime gate, build and report.**

— Architect
