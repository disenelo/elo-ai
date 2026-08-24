# 05_WO-CANON-VI_attention.md — one attention driver (Ruling B)

**WO:** WO-CANON-VI · **Seat:** builder · **Priority:** P1 · **Reserved?** no
**Spec:** `engineering/work_orders/WO-CANON-VI.md` · **Canon:** `docs/architecture/Volume_VI/` (4 chapters)
**Ruling:** B (`CANON_RULINGS_2026-08-10.md`) — issued 2026-08-10, this was the ruling that was MISSING and
blocked this WO. It is now decided.

## The finding [VERIFIED by audit]
TWO things called "attention" exist: `core/attention.py` (a wired memory-relevance filter) and
`runtime/working_memory.py` (a built, tested, but **imported nowhere** working-memory competition).
`CognitiveState` has no `working_memory` / `attention_state` slot, so the spine never contributes WM at all.

## Scope (Ruling B decides the design — don't re-litigate it)
1. **`runtime/working_memory.py`'s competition is THE single attention driver.** Wire it into `CognitiveState`
   (`runtime/contracts.py`) and into the spine at the correct turn position (Volume IV Ch.1 has the canonical
   order with file+line).
2. **Re-cast `core/attention.py` as a "Memory Relevance Filter"** — a SUPPLIER into that competition, not a
   rival decider. **Rename it** so the name can't mislead again.
3. Importance/salience comes from the live Significance engine (9-dim, per FC-2) — do not invent a new scorer.

## Test
Assert WM is populated on the carrier each turn · assert the Executive reads ONE attention source · assert
the renamed relevance filter feeds the competition rather than deciding.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
