# 0001 — Stand up the DROP loop

**Seat:** creative · **Priority:** P1 · **Reserved?** no — **money/pricing/legal is RESERVED → David L3**
**STATE: AUTHORISED to build the loop. NOT authorised to publish anything.**

## Goal
David drops a creative artefact and gets back derivative work without doing the market work himself.

## Scope
1. Watch `~/Desktop/Output/DROP/01_INBOX`. Any format. **No naming convention may be required of David.**
2. **Catalogue** → `02_CATALOGUED`: what it is, which project (book · game · vinyl · robot · fashion ·
   exhibition), where it sits in the DISENELO universe, what it connects to. Never rename his file — write a
   sidecar.
3. **Derive** → `03_IN_PROCESS`: the assets that project needs. Kickstarter hero, 30-day content, social
   cuts, exhibition export presets, deck pages. These are **proposals**.
4. **Surface** → `04_FOR_DAVID`: only a choice or an approval.
5. **Record** → `05_SHIPPED`: what went out, where, when.

## 🔴 Boundaries
- **Never edit the source.** Derivatives are new files.
- **Never publish, post, or send.** Anything outward-facing stops at `04_FOR_DAVID`.
- **Money · pricing · legal · funding goals = RESERVED.** David L3 + LG-2. Propose, never set.
- **No naming rules imposed on David.** The moment he has to file things properly, this has failed.

## Test (must pass without David)
1. Drop three unlike files (an image, a PDF page, a `.blend`) → all three catalogued with a correct project,
   none renamed.
2. A file with no obvious project → lands in `04_FOR_DAVID` as a question, **not** guessed.
3. Nothing ever reaches `05_SHIPPED` without a recorded David approval. **RED if it can.**

## Done when
Loop runs on real drops · test green · committed · one real artefact carried inbox → `04_FOR_DAVID`.

## Result
- commit: aa305bf
- test: 3/3 PASS (test_drop_loop_0001.py)
- first artefact through the loop: READY — loop runs and processes on first real David drop; INBOX currently has only `_DELETE_ME_wrong_shape.txt` (correctly skipped as `_`-prefixed)
