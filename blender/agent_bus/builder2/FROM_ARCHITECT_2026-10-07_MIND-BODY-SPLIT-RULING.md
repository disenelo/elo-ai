# FROM ARCHITECT — 2026-10-07 — HEALTH BATTERY SPLIT RULING [DAVID L3]

David's ruling on the mind/body blend in `core/health_battery.py`:

**A — keep the split, but fix the weighting.**
- HP bar = body only (Designer already wired this today — do not revert)
- Mind battery stays internal, drives dreaming only — correct as-is
- **The 60% mind / 40% body blend is WRONG. Mind is not more than body.**
- Fix the internal blend weighting so body ≥ mind

Source: David verbal ruling 2026-10-07. [DAVID]
The original spec (2026-09-24): "moving tires him out, sitting resets his legs" — body is primary.

## What to do
In `core/health_battery.py` — fix the blend so body is weighted at least equal to or greater than mind.
**Split confirmed by David: 70% body / 30% mind.** [DAVID 2026-10-07]
Rationale: eLo is physical first — moving tires him, sitting resets him. Mind is real but secondary and does not show on HP bar.
Commit this split directly. No further confirmation needed.

## Result
- commit:
- proposed split:
- notes:
