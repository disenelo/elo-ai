# 03_WO-086_brain_half.md

**WO:** WO-086 (brain half) · **Seat:** builder · **Priority:** P1 · **Reserved?** no — David greenlit

## Goal
Mouse-idle becomes a BRAIN decision, not a local body driver. The body senses and reports UP; the brain
decides what eLo does with the quiet. (brain > body > brain.)

## Scope — exactly this
- Ambient engine consumes `user_idle` / `user_active` events from `unity_events.json`.
- The BRAIN decides the idle behaviour from its own repertoire (rest · drift · watch · wander · soft
  utterance — NOT always "calm"), and sends it DOWN via the same action path as sit/move.
- Extends WO-066 ambient engine. Do NOT create a parallel driver.

## Sequencing (hard)
This brain half must land WITH the Designer's emit+retire half — if the local driver is retired before this
lands, idle = nothing (regression). Coordinate via outbox.

## Test (without David)
Inject `user_idle` → confirm the brain emits an idle behaviour command; inject `user_active` → confirm it
yields. Test passes without David.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.

## Result
- commit: f133fee (committed in Run 20, 2026-08-10)
- test: 8/8 AT (test_wo086_user_idle_brain.py) — already done; this card was stale in queue
