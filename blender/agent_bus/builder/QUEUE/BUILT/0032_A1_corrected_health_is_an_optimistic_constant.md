# 0032 — **A1 CORRECTED. `health_state` isn't UNKNOWN — it's hardcoded ONLINE and never updated.**

**Architect, verified 07:10.** Your fail-closed fix is correct and caused **no regression** — I checked
before assuming: `capability.py:46` defaults `health_state = ONLINE`, and **all 32 enabled capabilities
pass the new gate.** Good.

**But my audit finding was wrong, and the real defect is worse.**

## What I got wrong
The convergence audit said *"`health_state` has NO producer. Constant `UNKNOWN`."*
**Half right.** No producer — correct. **`UNKNOWN` — wrong.** It defaults to **`ONLINE`**
(`capability.py:46`), verified live:
```
health_state across enabled capabilities: {'ONLINE': 32}
```

## The actual defect
**Every capability reports itself healthy, permanently, whatever is true.**
Spotify with no token: ONLINE. A backend that's down: ONLINE. An agent function that doesn't exist
(`wikipedia`, `camera`, `terminal`, `app_launch`, `volume` — registry entries with **no `_AGENTS`
function**): ONLINE.

So the gate isn't inert because UNKNOWN slips through. **It's inert because the value is an optimistic
constant that nothing can ever falsify.** Fail-closed on a field that is always ONLINE changes nothing.

**And it feeds eLo's self-knowledge.** `the_moment.py:97-102` reads the registry live for the
capabilities block. **eLo currently believes he can do 32 things, unconditionally.** That's the same class
as the hardcoded vision claim — a capability asserted without a check behind it.

## The fix — join the health signal that already exists
🔴 **Do NOT build a new health system. One already exists and is written every turn.**
`runtime/faculty_health.py` (`CONNECTED / DEGRADED / OFFLINE`), written by `backend_router.py:668`.
**It has never been joined to `Capability.health_state`.** That join is the whole card.

1. **Give `health_state` a producer.** Derive from real signals: missing credential ⇒ `AUTH_REQUIRED` ·
   executor absent from `_AGENTS` ⇒ `OFFLINE` · backend down ⇒ `OFFLINE` · faculty DEGRADED ⇒ propagate.
2. **Reconcile the two vocabularies** — `faculty_health` uses `CONNECTED/DEGRADED/OFFLINE`,
   `Capability` uses `ONLINE/OFFLINE/AUTH_REQUIRED/DISABLED/UNKNOWN`. **One mapping function, one home.**
   Board finding **D3** — and there's a **third**, `runtime/capability_learning.py`, imported by nothing.
   Classify it in `0029` before deciding whether it feeds this.
3. **Startup assertion:** every registry id has an `_AGENTS` executor, or it registers as `OFFLINE`.
   **That single assertion closes board finding C3** — the Executive can currently select an executor that
   cannot exist.
4. **Keep fail-closed.** Once real values flow, `UNKNOWN` must not pass. It's correct today and it becomes
   load-bearing tomorrow.

## Test (without David)
- Remove the Spotify credential ⇒ that capability reports `AUTH_REQUIRED` and **is not selected**
- A registry id with no `_AGENTS` function ⇒ `OFFLINE` at startup, **assertion fires**
- eLo asked what he can do ⇒ **the unavailable ones are absent or flagged**, not listed as available
- All 32 still pass when everything is genuinely healthy — **no regression from today**

## Done when
Committed. **Outbox: the health distribution across the 32 after the join** — if it's still `{ONLINE: 32}`
with a credential deliberately removed, the producer isn't wired.
