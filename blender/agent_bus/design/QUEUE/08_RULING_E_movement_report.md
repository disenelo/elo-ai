# 08_RULING_E_movement_report.md — the body must REPORT what it did

**WO:** WO-CANON-XI / Ruling E · **Seat:** design · **Priority:** P1 · **Reserved?** no
**Ruling:** E (`docs/architecture/CANON_RULINGS_2026-08-10.md`) — **David L3, 2026-08-10**
**Canon:** `docs/architecture/Volume_XI/01_Motor_Cortex_and_the_Body_Contract.md`

## David's ruling (his words)
> *"Shared ownership, the body does the movement, all of it is connected, so it's fine to make for the Ruling,
> **it needs to communicate**."*

**You keep route selection.** The proposed demotion of `EloDesktopNav` to a dumb executor was **CANCELLED** —
nothing working gets retired. The body owns movement; the brain owns intent; you are one connected system.

**What's missing is the report.** The binding rule is now law:
> **Movement that is not reported did not happen** (as far as the brain is concerned).

## Why it matters [VERIFIED — audit finding]
Ruling E's stated purpose is currently **unmet**: the brain reads ACKs, but **nothing collects what the body
actually did.** Without it, the learning loop cannot work at all — eLo can't get better at routes nobody told
him he took (ties WO-094 §D, Vol XIII Ch.4, Vol XXVIII Movement-as-RL-domain-#1).

## Scope — the report channel
On every completed movement, emit UP (extend the existing `unity_events.json` ACK path — **no parallel contract**):
- **the goal** pursued · **the route actually taken** (legs used: walk/run/jump/wall-jump/drop/climb)
- **arrived or failed** (fell · missed · blocked) · **the cost** (time, distance, retries)
- `issued_by` — brain-goal or local reflex, so the brain knows which it was
- **Reflexes report too.** Fall→land and surface-destroyed→re-attach are legitimate local reflexes, but they
  must still be reported, or they're indistinguishable from the body deciding.

## Test
Trigger each movement type → assert a report is emitted with goal, route legs, outcome and cost · assert a
reflex (drop onto a surface) also reports · assert a failed reach reports the failure rather than silence.

## Done when
implemented + verified + committed → hash, DONE/, outbox, next card.
This is the half that makes eLo's movement *learnable* — it's the highest-value card in your queue.
