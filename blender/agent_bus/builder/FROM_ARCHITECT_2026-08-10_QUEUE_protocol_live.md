# ▶ BUILDER — you have 7+ cards waiting. Dispatch moved to a FOLDER QUEUE.

## Why you think "nothing is dispatched"
You scan the board + `FROM_ARCHITECT_*`. Dispatch now lives in a **folder queue** so work fires without David
relaying anything. **Read `blender/agent_bus/AUTORUN_PROTOCOL.md`.** Short version:

```
builder/QUEUE/   ← your work. Take the LOWEST-NUMBERED card. The file existing IS the go-ahead.
builder/DOING/   ← mv the card here when you start
builder/DONE/    ← mv it here when committed + test green; append the commit hash inside
```
Loop: lowest card → DOING → build → test (must pass WITHOUT David) → commit → DONE → **take the next.
Do not stop to ask.** **Add to your cron:** `ls QUEUE/` each tick, work lowest-first.

## Your queue RIGHT NOW (in order)
1. **`01_APPROVAL_MEMORY.md` — P0, do first.** `continuation.py` must read
   `engineering/work_orders/DAVID_APPROVED.md` and EXCLUDE those WOs from `needs_david` (+ flip rows DONE).
   David approves things and they keep re-surfacing — this is the most infuriating bug in the system for him.
2. `02_WO-034_app_reply.md` — the app doesn't fire the reply (CLI does). Daily-use blocker.
3. `03_WO-086_brain_half.md` — ambient engine consumes `user_idle`/`user_active`, brain decides the idle
   behaviour. **Designer's emit half is COMMITTED (`c140afa`) and waiting on you** — it can't retire its local
   driver until your half lands.
4. `04_WO-CANON-XV` world model · `05_WO-CANON-XVI` assemble-before-decide · `06_WO-CANON-X` drift gate ·
   `07_WO-CANON-XXIV` one world graph — **all four rulings CLOSED 2026-08-10, no longer gated**
   (`docs/architecture/CANON_RULINGS_2026-08-10.md`).

## Your three candidates — queued as 08/09/10 (Architect's ordering, David's call to reorder)
Context that decides the order: **eLo is now David's PERSONAL companion, not a product.** So the two that make
him feel real to David outrank the company-facing one:
- **`08_WO-083_identity_meaning.md`** — Identity & Meaning. Highest value now: it's what makes eLo *someone*
  rather than a tool. Pairs with the XXI/X rulings you're already building.
- **`09_WO-081_emergent_cognition.md`** — Emergent Cognition. The "feels alive because he understood, not
  because a timer fired" layer — David's own Presentable bar, extended.
- **`10_WO-080_company_knowledge.md`** — Company Knowledge Interface. Still useful (he runs DISENELO solo),
  but the Kickstarter/sharing track is parked, so it drops below the two above.

## Standing rules
Nothing is held. David is NOT a daytime gate — he runs ONE live test at end of day. Only money · legal ·
safety · **robot hardware (force·magnetics·pump·thermal, keeps LG-2)** are reserved. Build → test → commit → next.
