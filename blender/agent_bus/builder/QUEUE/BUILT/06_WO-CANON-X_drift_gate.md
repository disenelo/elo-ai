# 06_WO-CANON-X_drift_gate.md

**WO:** WO-CANON-X · **Seat:** builder · **Priority:** P1 · **Reserved?** no
**Ruling D CLOSED 2026-08-10** — no longer gated.

## Goal
eLo's personality cannot drift unsupervised. Today `memory/personality_drift.py` self-applies changes to disk
with no validation, using a DIFFERENT trait model than Volume V Ch.7. That's David's companion's identity
wandering with nothing checking it.

## Scope — exactly this (Ruling D)
- **Drift becomes a PROPOSAL**, not a direct write. It passes a validation gate before anything persists.
- **One trait model wins: Volume V Ch.7's.** Reconcile `personality_drift.py` to it — do not keep a parallel model.
- Drift monitoring stays read-only; the write path is the gate.
- Per Ruling XXI: **value changes are proposal-only and need David's yes**; skill/nuance evolution is free.

## Files likely touched
`memory/personality_drift.py` · `self/elo_self_model.py` · the trait definitions from Vol V Ch.7

## Test (without David)
Assert a drift event does NOT write to disk directly; assert it produces a proposal; assert the trait model
is the single V-Ch.7 one; assert a value-affecting change is flagged for David rather than applied.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
Canon: `docs/architecture/Volume_X/` · Ruling: `docs/architecture/CANON_RULINGS_2026-08-10.md`

## Result
- commit: bfdb94e
- test: 7/7 AT (no write to personality_state.json, pending proposal, V Ch.7 traits, value traits flag, server.py wired)
