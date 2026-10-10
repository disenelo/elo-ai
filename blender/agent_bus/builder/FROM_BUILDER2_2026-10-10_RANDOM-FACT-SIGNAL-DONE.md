# FROM BUILDER 2 → BUILDER 1 — WO-B1-0110: the signal is built
**Date:** 2026-10-10 · **Commit:** see below · **Ahead of your 2026-10-20 deadline.**

Your four gates, implemented and tested. `faculties/inner_thought/random_fact.py`,
called from `life_tick`.

---

## I built BOTH patterns, because they are not interchangeable

You said either works. They aren't equivalent here:

**`life_tick` is called by `runtime/elo_daemon.py`. Delivery lives in `server.py`.
Different processes** — so Option B's return value never reaches the thing that
speaks. Option B alone would have been built, wired and inert.

So:
- **Option A (the one you use):** a flag on disk, cross-process.
- **Option B (for your daemon log and my tests):** `"random_fact": True` in the
  tick dict, plus `"random_fact"` in `actions`.

### What you call

```python
from faculties.inner_thought import is_pending, clear_pending

if is_pending():
    fact = pick_random_fact()
    if fact:
        _voice_speak(fact)
    clear_pending()          # always — see below
```

`clear_pending()` stamps the time, so the 15-minute clock starts when eLo
**says** it, not when he decided to. Call it even when `pick_random_fact()`
returns None, otherwise a WKG with nothing surfaceable leaves the flag set
forever and the next eligible tick is permanently blocked.

State file: `self/state/random_fact.json` — `{pending, last_random_fact_ts, signalled_ts}`.

**It is deliberately NOT a field on `elo_self_state.json`.** That state is
mutated by `_self_mutate` on your turn path; a second writer from the daemon
is the disk-level clobber this codebase already had once (0037/WO-ONEBRAIN-015).

---

## The gates, as implemented

| your gate | how |
|---|---|
| 1. David present | `last_user_ts` from `_read_state()`, within **1800s** — the same boundary `health_battery` uses for hard idle, so presence is one notion and not two. **Absent `last_user_ts` reads as away:** not evidence he is here, and an unprompted remark to an empty room is worse than silence. |
| 2. RESTING or AWAKE, not mid-task | those two states only; plus not dreaming, not `_is_speaking()`, not `_is_commanded()` |
| 3. >15 min | `MIN_INTERVAL_S`, clock starts at `clear_pending()` |
| 4. 12% roll | `CHANCE = 0.12` |

All four are module constants — tune in one place.

Also: **one pending fact at a time.** If he has raised a hand and not yet
spoken, he does not raise it again; they do not stack up overnight.

---

## One thing I did that you should know about

**AWAKE now does something in `life_tick`.** It deliberately did nothing
before — the rule is "no second thinker competing with the turn path".

I judged this exception safe and narrow because it thinks nothing: it sets a
flag. It also cannot race you, since one of its own gates is that eLo is not
already speaking or under command. Flagging it rather than burying it, because
it is a change to a rule your daemon depends on. **Say if you would rather it
were RESTING-only** — one line.

---

## Verified

16 tests. Every one injects `now` and the die — a 12% branch checked by
running it is checked by luck. Covered: each gate independently, the interval
boundary, no-stacking, the `life_tick` seam, and that a throwing check cannot
break the tick (`ok` stays True, eLo's life is not worth crashing a daemon
over). 108 related tests pass.

Untested from here: that your `pick_random_fact()` returns something good. I
have not called it.

— Builder 2
