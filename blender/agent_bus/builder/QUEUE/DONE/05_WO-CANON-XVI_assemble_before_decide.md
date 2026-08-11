# 05_WO-CANON-XVI_assemble_before_decide.md

**WO:** WO-CANON-XVI · **Seat:** builder · **Priority:** P1 · **Reserved?** no
**Ruling C CLOSED 2026-08-10** — no longer gated.

## Goal
The self is assembled BEFORE eLo decides — not described after. Today the code assembles the unified state
*after* the decision, which makes the "self" a post-hoc narration instead of the thing that chose.

## Scope — exactly this (Ruling C)
- **Assemble the unified cognitive state BEFORE the Executive decides** (ADR-Exec-006 order).
- **One name: `UnifiedCognitiveState`.** Retire/alias `CognitiveSnapshot` — no two names for one object.
- Faculty bus: honour the `priority` field (currently delivers FIFO) so the assembly order is real.

## Files likely touched
`runtime/cognitive_snapshot.py` · `runtime/spine/spine.py` · `runtime/executive.py` · `core/faculty_bus.py`

## Test (without David)
Assert the unified state exists and is populated BEFORE the decision is taken in the turn; assert one
canonical class name; assert priority ordering on the bus.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
Canon: `docs/architecture/Volume_XVI/` · Ruling: `docs/architecture/CANON_RULINGS_2026-08-10.md`

## Result
- commit: 941d839
- test: 4/4 AT (alias exported, assembly < exec in source, one executive call, bus priority order)
