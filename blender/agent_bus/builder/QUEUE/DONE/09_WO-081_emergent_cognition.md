# 09_WO-081_emergent_cognition.md

**WO:** WO-081 · **Seat:** builder · **Priority:** P2 · **Reserved?** no

## Goal
eLo feels alive because he **understood and acted**, not because a timer fired. David's own Presentable bar,
extended: emergence, not puppetry.

## Scope — exactly this
- Implement per the authored WO-081 spec.
- Behaviour arises from the assembled cognitive state (Vol XVI — note card `05` makes assembly happen BEFORE
  the decision; this WO should sit on that, not fight it).
- No new timer-driven behaviour dressed up as spontaneity. If it can't be traced to a real perception/goal,
  it doesn't ship.

## Files likely touched
`runtime/executive.py` · spine / faculties per the WO

## Test (without David)
Assert emergent behaviours trace to a cognitive cause (perception/goal/state), not a timer; assert no
behaviour fires with an empty cognitive state.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
Spec: `engineering/work_orders/WO-081_*.md`

## Result
- commit: 66d985b
- test: 5/5 AT (empty state no intent, threshold gate, absence threshold, append-only autobiography, server.py wiring)
