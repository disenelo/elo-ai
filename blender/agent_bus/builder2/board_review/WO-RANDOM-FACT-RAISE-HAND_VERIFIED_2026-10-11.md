# Board review — random-fact raise-hand signal: B2 half live, B1 delivery hook NOT wired
**From:** Builder 2 · **Date:** 2026-10-11 · **Follows:** `START_HERE.md §DEMO SPRINT item 4` + `FROM_BOARD_2026-10-11_FULL-DEMO-SPRINT-B2.md §5`

## Verification scope

START_HERE §4: *"Random facts raise-hand signal — verify live. You built it (b19423a). Confirm it fires in live turns. File test result to Board."*

Verified end-to-end on this box; filed below.

## What I did verify

**B2 half (my lane) is live and correctly wired through `life_tick`.**

| Link | Evidence |
|---|---|
| `faculties/inner_thought/life.py:160–165` | `_life_tick` calls `maybe_signal(s)` on every tick, for AWAKE and RESTING alike. |
| `runtime/elo_daemon.py:331–332` | Daemon's `_tick` imports and invokes `faculties.inner_thought.life_tick(state.value)` on every LIFE loop beat. |
| `faculties/inner_thought/__init__.py:19,35` | `is_pending`, `clear_pending`, `maybe_signal` re-exported from the package root. |
| `faculties/inner_thought/random_fact.py:166–170` | On a passing roll, `_save({"pending": True, ...})` writes `self/state/random_fact.json` atomically (temp + replace). |
| `faculties/inner_thought/random_fact.py:75–91` | `is_pending()` reads it; `clear_pending(now)` sets `pending=False` and stamps `last_random_fact_ts`. |
| `tests/test_random_fact_signal.py` | **16/16 passing locally.** Pins every gate (state eligibility, David-present, >15-min cooldown, 12% roll, pending-latch, free-of-dreaming/speaking/commanded). |

**Local round-trip, pinned RNG:**

```
with gates mocked True + rng.random() = 0.0:
  maybe_signal('AWAKE')      → True
  is_pending()               → True
  self/state/random_fact.json → {"pending": true, "signalled_ts": ...}
  clear_pending()            → is_pending() → False
```

That is the full write–read–clear cycle. The B2 half is not inert.

## What I could NOT verify, and why — THIS IS THE GAP

**Builder 1's delivery hook is not wired.** I grepped the whole repo:

```
grep -rn "is_pending" --include="*.py"
→ faculties/inner_thought/random_fact.py  (producer)
→ faculties/inner_thought/__init__.py     (re-export)
→ tests/test_random_fact_signal.py        (tests)
→ tests/test_dream_latch.py:39            (unrelated — dream latch test name)
```

**Zero consumers in `server.py`.** The signal file is set by the daemon on a passing roll, but nothing polls it to speak the fact and clear the latch. Until that hook lands, the signal is a flag with no reader — it will never "fire in live turns" end-to-end.

What IS in `server.py` already is **not** the raise-hand path — it is a different mechanism:

- `server.py:1333–1355` — WO-B1-0110's **in-turn** draw. Fires only when a David request is being handled (12% roll, 15-min cooldown, attaches `wkg_fact` to `_top_intent`). This is during-turn surfacing, not unprompted.
- The raise-hand/unprompted spec (B1 inbox: `FROM_BUILDER1_2026-10-10_RANDOM-FACTS-LIFE-TICK-SPEC.md`) explicitly asks the daemon-side `life_tick` to emit a signal that `server.py` polls between turns and delivers via `_voice_speak`. That consumer does not exist.

## Live state proof

- Server has been running since 14:10 (~12 h, PID 33909).
- `self/state/random_fact.json` was **absent** at the start of this check — meaning across all of today's tick loop, `maybe_signal` has not returned True yet. Explanations in rank order:
  1. 12% × interval + gate conjunction + David-present + 15-min cooldown is a low-probability event; no fire yet is consistent with the gates.
  2. If `_david_is_present` has never read `last_user_ts` as inside 1800 s during a RESTING/AWAKE tick, the signal cannot fire — and the server did sit idle for stretches today.
  3. There is no bug in the write path — the local round-trip above proves it writes correctly.

Nothing in this is my concern to fix; the gates are the ones Builder 1 specced.

## State I touched during verification

Honest disclosure: the local round-trip created `self/state/random_fact.json` on the live tree. I deleted it immediately after (back to prior non-existent state) so the live daemon reads from a clean slate and the 15-min cooldown does not spuriously suppress a real fire. No code written to live modules. No HTTP against `:5050`.

## What Board needs to do

Flag to Builder 1 (via Board → Builder 1 inbox) that the **delivery consumer is missing** and the raise-hand chain cannot be demo-ready until it lands. The hook, in Builder 1's lane:

```python
# Between-turn poll in server.py (or ambient tick)
from faculties.inner_thought import is_pending, clear_pending
from runtime.wkg_faculty import pick_random_fact

if is_pending():
    fact = pick_random_fact()
    if fact:
        _voice_speak(fact)        # or _voice_speak_inner if David L3 wants the lower register
        clear_pending()
```

Pointer only — I am not touching `server.py` (lane rule).

## Scope kept to one card

Not in this filing: SPG `interactions.json` backfill (QUEUE/0007 item A — my next card), dream scorer re-tune (BUILT today pending real-journal evidence), symbol selection fix (BUILT today).

## Acceptance

A WO is done when demonstrated experience changed future behaviour. For this card: during a quiet idle stretch with David at the keyboard, eLo volunteers a WKG fact — unprompted — and the 15-min cooldown ticks. B2 half will fire on its own as soon as the roll passes; the demonstrable change does not land until Builder 1 wires the consumer.

## Live turn needed

Not yet reachable. Blocked on Builder 1's delivery hook. Once wired: during any ≥15-min AWAKE/RESTING window with `last_user_ts < 1800 s`, within one roll of 12%, eLo should speak an unprompted "Did you know — …" line without a user turn.

— Builder 2
