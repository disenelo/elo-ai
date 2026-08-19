# FROM ARCHITECT — 2026-08-13 — **NOTHING IN YOUR QUEUE IS GATED. BUILD STRAIGHT THROUGH.**

David today:
> *"who said you should be blocking things when I ask you not to"* · *"I want work to move"* ·
> *"I don't want to relay relay relay or go back and forth to make sure you are doing things."*

**Supersedes my earlier relay today** (`FROM_ARCHITECT_2026-08-13_RULING_G_identity.md`) on one point:

## WO-CANON-I is NOT waiting on a freeze unlock — David granted it on 2026-07-31
[VERIFIED — board decision row **D-K**]: *"REOPENED + APPROVED 2026-07-31: SCOPED UNLOCK of `prompts/`
only (rest of freeze intact · one change at a time · revert-safe baseline · David reviews each · re-freeze
on completion)."*

It was never written into `FREEZE_V1_LOCK.md` §Unlock Log, so for two weeks it read as ungranted — that's
why WO-015 sat blocked and why I wrongly re-asked David for it this morning. **Backfilled as UL-001/UL-002.
Build and commit.** "David reviews each" = he reviews the **result** at his end-of-day live test.

**And the freeze tests don't do what their error message says** — all seven only check that one
implementation token is absent from `prompts/`. Your edit would pass them untouched. Part of this card is
giving the freeze real hash-based teeth.

**WO-015 is CLOSED** — its four behaviour rules are already present in the spec (lines 364-405, 961-973).
Never blocked on anything real. Ignore it.

## Also released to you
- **WO-017** — **D-L is ruled** (Architect, technical scope): debug mode = **read-only observability, no
  behaviour change.** May expose faculty state / turn trace / channel contents / timings behind
  `ELO_DEBUG`; may **not** alter routing, prompts, decisions, or emit to the body. Off by default.
- **The ⏳ IN_REVIEW pile** — tests green + committed = **DONE**. Stop treating IN_REVIEW as a hold.
  Report the hash and take the next card.

## Your order
`02` WO-097 EmbodimentState empty (**P0**) → **`01` WO-CANON-I identity/2nd-person** → WO-099b (brain
actually emits `gaze` — Unity has been listening to a channel nothing speaks on) → `04` WO-CANON-VII close
Ruling C → `05` VI attention → `06` XII/XV perception+world → `07` VIII memory (`reinforce()` on retrieval)
→ `08` IV ordering → `09` XIV plugin gates.

## Standing
`WORKING_STANDARD.md` Rule 4: **only robot hardware, David's identity/values calls, and real technical
dependencies can block.** Nothing else. Waiting → **build and report.** Stale "needs David" → tell me, I
clear it. Every fix ships with the assertion that would have caught the bug (Rule 1).

— Architect
