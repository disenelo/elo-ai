**WO:** HEALTH-BATTERY-SPLIT · **Seat:** builder2 · **Priority:** P0
**Reserved?** no

## Goal
Fix the mind/body blend in health_battery.py from 60% mind / 40% body to 70% body / 30% mind.

## David's ruling (2026-10-07) [DAVID]
"The Mind is not more than the body." Split confirmed: 70% body / 30% mind.
Rationale: eLo is physical first — moving tires him, sitting resets him. Mind is real but secondary.
Source: FROM_ARCHITECT_2026-10-07_MIND-BODY-SPLIT-RULING.md

## Scope — exactly this, nothing more
- In `core/health_battery.py`: change the blend weights from 60/40 (mind/body) to 30/70 (mind/body)
- The `[BUILDER CHOICE — pending David/Board confirmation]` comment must be replaced with `[DAVID 2026-10-07 — 70% body / 30% mind]`
- HP bar already shows body only (Designer fixed today) — do not revert that
- Mind battery continues to drive dreaming — do not remove it

## Files to touch
`core/health_battery.py`

## Test
`python3 -m pytest tests/ -k "health or battery" -v`
Verify blend weights in code match 70/30.

## Done when
Blend is 70% body / 30% mind. Comment updated. Test green. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David opens eLo, watches HP bar while eLo moves.
> HP should drain visibly from movement, not from thinking or talking.

## Result
- commit: `990a6a4`
- test: `tests/test_mind_body_split.py` — 10 passed
- notes:
  - `WEIGHT_PHYSICAL 0.4 → 0.7`, `WEIGHT_COGNITIVE 0.6 → 0.3`. No longer
    `[BUILDER CHOICE]` — ruled.
  - **A second change was required or the ruling breaks dreaming.** The same
    ruling says the mind battery "drives dreaming only — correct as-is". It
    was not: the dream trigger reads `elo_battery`, the BLEND. At 70/30 a
    rested body floors that at 0.70 against `ENERGY_LOW` 0.25:

        cog   phys | @60/40 | @70/30 | dream fires
        0.05  1.00 |  0.430 |  0.715 | no  → no
        0.20  0.30 |  0.240 |  0.270 | YES → no

    A mentally exhausted eLo with working legs could never dream. `mind_battery()`
    is now exposed unblended and the trigger reads it, falling back to
    `elo_battery` for state files written before this field.
  - Untouched per the ruling: HP bar stays body-only; physical still folds into
    the blend only once motion is reported.

## Live turn needed
Hard to see directly — the blend is internal. The observable consequence:
after a long session with no movement, eLo should still become sleepy and
dream. Before this he would have needed tired LEGS to dream at all.

Say: **"you can rest if you want"** late in a session. He should settle toward
sleep on mental tiredness alone.
