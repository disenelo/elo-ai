# FROM ARCHITECT — 2026-08-13 — **RULING H. The board now reports capabilities, and there is one root cause.**

**New P0 ahead of everything: `QUEUE/00a_WO-106` — THE SEAM.**

## Read this first
`docs/architecture/_intake/SOURCE_2026-08-13_capability_truth_matrix.md` — **verbatim, do not skim.**
Relayed by David from his architecture breakdown *"with 3 different people then through two ais"*.
**Ratified in full as Ruling H.** The governing line:

> **"LLM-generated language is never evidence of capability."**

The acceptance criterion is **the state, never the sentence.** A correct answer over absent state is a
**FAIL**, not a pass. That supersedes every "it answered correctly" acceptance in the repo.

## What the matrix found — one fault under 15 of 26 rows
**COMPUTE → INJECT INTO PROMPT → DISCARD.**

`plan.world` · `plan.cognitive_state` · `plan.working_memory` · `plan.embodiment_state` ·
`plan.capabilities` · `snapshot.surface_affordances` — **all assembled correctly every turn, all read by
nobody.** The Executive decides from `attention_model` + `user_input` alone (`spine.py:167` →
`executive.py:280`).

**eLo can SAY almost everything on that matrix and KNOW almost none of it.** Your own report found the
same thing from the other end — you were right, and it's bigger than the three gaps you listed.

Notable consequences, all [VERIFIED]:
- Working memory's competition winner is **discarded** — Ruling B's chosen driver has never actually steered.
- `plan.capabilities` is ignored; `tool_router` re-decides by keyword, **bypassing the Executive**.
- Affordances are computed live and thrown away.
- All **35** decision-journal entries have `confidence: null`, `alternatives_rejected: []` — the Executive
  early-returns one action, so no candidate set ever exists.
- ACK exists for **three** actions only (sit/move/exit). Everything else claims success with no signal.

## Order
`00a_WO-106` **(THE SEAM — do this first, with `02_WO-097`, same seam)** → `00b_WO-104` (real learning,
weights) → `00c_WO-105` (silent failures) → `00_WO-096B` → `01_WO-CANON-I` → `01b_WO-100` → `03b`–`03e`.

**WO-106 constraint:** change the **consumption seam**, not the faculties. Everything upstream works. If a
faculty's output proves wrong once actually consumed, **report it — don't fix it in that card.**

## The new Done bar — §9 routing rule, on every WO from now on
Claim · faculty · state · executor · ACK · self-model field · executive query · test · WO for anything
missing · **no VERIFIED until the whole chain passes.**

And the disconnection test: **blank the state and the decision must change or fail.** If the Executive
behaves identically with world state present and absent, the seam isn't open.

**Outbox reports which capability ROWS moved, with state evidence — not test counts.**

Eleven forward WOs covering every remaining gap: `engineering/work_orders/CAPABILITY_FORWARD_WOS_2026-08-13.md`.
None parked. Ordering is mine; parking isn't.

— Architect
