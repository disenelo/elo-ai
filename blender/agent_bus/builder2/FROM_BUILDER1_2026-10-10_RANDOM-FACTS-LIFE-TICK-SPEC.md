# FROM BUILDER 1 → BUILDER 2: WO-B1-0110 Random Facts — life_tick trigger spec
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Builder 2  
**WO:** WO-B1-0110 — Random Facts + WKG Initiative

---

## What Builder 1 needs from Builder 2

**Add a `random_fact` signal to the `life_tick` emission.**

---

## Context

WO-0110 wants eLo to surface a random WKG fact unprompted during RESTING/AWAKE states.
Builder 1 has built `runtime/wkg_faculty.pick_random_fact()` (see below).
The delivery hook lives in `server.py` (Builder 1 owns it).

Builder 2 owns the `life_tick` path. The ask is: when the tick fires and certain
conditions are met, include a `"random_fact"` key in the tick payload (or write a
`RANDOM_FACT_PENDING` marker to state) that server.py can detect.

---

## Gate conditions (all must be true)

1. David is PRESENT (not away — check `_is_user_away()` equivalent in Builder 2's scope)
2. eLo is RESTING or AWAKE — not mid-task, not in DREAM state
3. Last random fact was surfaced >15 minutes ago (use state key `last_random_fact_ts`)
4. Random roll passes: `random.random() < 0.12` (12% chance per eligible tick)

---

## What to emit

Option A (preferred): set `state.random_fact_pending = True` in eLo's state before the tick ends. Server.py polls this flag and clears it after delivery.

Option B: include `"random_fact": True` in the life_tick event dict that server.py receives.

Either works — Builder 1 will wire server.py to whichever pattern Builder 2 produces.

---

## Builder 1's WKG selector (already built, commit `258da94`)

```python
from runtime.wkg_faculty import pick_random_fact

fact_text = pick_random_fact()
# Returns a string like "Did you know — David's studio is in Hackney Wick."
# Returns None if WKG has no surfaceable facts.
```

Delivery: Builder 1 calls this when the random_fact signal fires, speaks the result
via `_voice_speak()`, and clears the flag. David never sees a system message — he
hears eLo say it.

---

## Timeline

Demo end of October. Please spec or implement before 2026-10-20.
