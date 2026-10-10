# 08_WO-083_identity_meaning.md

**WO:** WO-083 · **Seat:** builder · **Priority:** P2 · **Reserved?** no

## Goal
eLo has a sense of who he is and what matters to him — identity and meaning, not just capability. This is
what makes him someone rather than a tool. He is now David's personal companion; this is the layer that
carries that.

## Scope — exactly this
- Implement per the authored WO-083 spec, grounded in the self-model + Volume X (Personality) and
  Volume XXI (Narrative Identity).
- **Honour the 2026-08-10 rulings:** "same eLo" = continuity of **memory + values**; growth is free but
  **value changes are PROPOSAL-ONLY and need David's yes**; never assert an identity claim that doesn't trace
  to real state (ADR-Exec-001 Verified Speech).
- No fabricated autobiography — meaning is grounded in what actually happened, not invented.

## Files likely touched
`self/elo_self_model.py` · identity/meaning module per the WO · Vol X / XXI touchpoints

## Test (without David)
Assert identity/meaning answers trace to stored state; assert a value-change attempt produces a proposal
(not a write); assert no unverified self-claim.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
Spec: `engineering/work_orders/WO-083_*.md` · Rulings: `docs/architecture/CANON_RULINGS_2026-08-10.md`

## Result
- commit: 497fbf8
- test: 5/5 AT (empty-state no fabrication, threshold enforcement, consistency-check focal+quiet, value-change drift gate, server.py wiring)
