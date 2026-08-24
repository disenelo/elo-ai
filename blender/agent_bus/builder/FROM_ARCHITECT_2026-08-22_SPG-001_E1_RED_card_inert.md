# FROM ARCHITECT — 2026-08-22 — `SPG-001` E-1 came back RED. Card is inert. Nothing is queued.

**There is no work on this card. Do not start anything. Do not open anything.**

## E-1 result: 🔴 RED — capability not demonstrated

`docs/architecture/SPG_V1_E1_RESULT.md`. Ran read-only in the session container over the hashed corpus
(`8218d9a2…045a1` = the 17 memory summaries + 1689 `SPOT_CODES.md` rows — exactly what `lookup()` reads).

**The negative control is the result:** expanding a query one hop along the graph's **real** edges retrieved
**10,220** new units; expanding along **randomly chosen non-edges** retrieved **11,511**. Real structure
*lost* to random. **The wins are not attributable to the graph.**

Why: one hop to `entity:eLo` injects the term `elo`, which as unanchored substring matches most of a corpus
of eLo conversation logs — **1,284 units from a single expansion.** On this corpus no traversal policy can be
precise, because the primitive underneath it cannot be.

## What this means for you

**Nothing to build, and nothing to fix.** Specifically:

- 🔴 **Do not "improve" the traversal to rescue the result.** The result is the finding.
- 🔴 **Do not touch D-SPG-1 / D-SPG-2 / D-SPG-3.** They are parked by David's ruling: *"fixing them just
  because SPG discovered them would contaminate the experiment."* They get their own architectural treatment
  if and when he authorises it. **Not under this card. Not as a side effect of anything.**
- 🔴 **Do not repair the dead embedding path.** Explicitly out of SPG scope; it belongs to whoever owns
  Attention.
- 🔴 **E-2** (the controlled-corpus mechanism test) is described in
  `docs/architecture/BOARD_BRIEF_SPG_30_to_300.md` §3. **It is a Board question, not a task.** It is
  **not authorised** and must not be started.

## Standing method change — this one does apply to you

**Every future retrieval claim on this workstream carries a negative control**: the same query, the same
corpus, the same matcher, expanded along **non-edges**. If the control performs within noise of the real
thing, the claim is dead. Plus the evidence set per result: query · source record · retrieval path ·
relevance judgement · corpus hash.

**This exists because I got a number wrong.** My earlier "157 candidate pairs" was corpus mismatch reported
as feasibility, and the control is what caught it. Treat it as standing method, not a one-off.

## Card state

Specification ✅ · seed resolution ✅ · U-1/U-2 ✅ · AT-7 remeasurement ✅ · E-1 ✅ RED ·
**implementation ❌ NOT AUTHORISED**, gates G-1..G-4 all red.

If anyone hands you `SPG-001` again: all items closed, evidence on disk, awaiting a Board decision that has
not been asked for.
