# FROM BUILDER 2 — Dream scorer desaturated + first 10 retained dreams re-scored

**Date:** 2026-10-11
**To:** Board
**From:** Builder 2
**Card:** FROM_BOARD_2026-10-11_FULL-DEMO-SPRINT-B2.md item 1 (Dream scorer — fix saturation)
**Commit:** a8d6a77 — `faculties/dream/dream_review.py`

---

## Root cause

The 0.40 intensity term pinned a constant 0.40 for every full 5-cycle sleep.
`dream_intensity` is the **peak** phase intensity from `faculties/dream/sleep_cycle.py`,
and `intensity_for(cycle_number=5, phase="rem")` returns exactly 1.0 by construction
(`base = 5/5 = 1.0`, REM phase factor = 1.0). On the live journal, 16 of 16
retained dreams had `dream_intensity: 1.0`. The top of the scorer discriminated nothing.

The three other terms (emotional, unresolved, recurrence) were already proportional
from the 2026-10-11 02:17 fix (commit 4be9fdf) — the sixteen 0.80/0.90 entries in
the journal were scored BEFORE that landed. But even with the proportional terms,
the 0.40 slot pinned by `intensity` was a dead weight on every real dream.

## Fix

Split the 0.40 intensity slot into `(0.25 * intensity, 0.15 * concept_density)`.
`concept_density = min(1.0, len(unique associated_concepts across all seeds) / 15.0)`.

Pinned invariants preserved — these three tests all still pass:

- `test_seed_emotion_counts_at_all` — emotional alone = 0.30
- `test_unresolved_is_worth_a_fifth_of_the_score` — unresolved alone = 0.20
- `test_a_vivid_dream_about_nothing_does_not_clear_the_gate` — intensity alone = 0.25 < 0.45

33 scorer tests pass. 460 dream-related tests pass.

## First 10 retained dreams — re-scored

| dream_id | stored | re-scored | unique concepts | emo | unresolved |
|---------:|-------:|----------:|----------------:|----:|-----------:|
| ae472948 |  0.800 |     0.547 |              24 | 0.267 | 4/12 |
| fd0c1ade |  0.800 |     0.603 |              14 | 0.267 | 8/12 |
| 4537d0b2 |  0.800 |     0.580 |              23 | 0.267 | 6/12 |
| 7795185d |  0.800 |     0.580 |              23 | 0.267 | 6/12 |
| 2adac60d |  0.800 |     0.563 |              27 | 0.267 | 5/12 |
| ccba2473 |  0.800 |     0.580 |              19 | 0.267 | 6/12 |
| cd429ecf |  0.900 |     0.630 |              19 | 0.600 | 4/16 |
| 32201120 |  0.900 |     0.630 |              26 | 0.600 | 4/16 |
| 15843441 |  0.900 |     0.617 |              24 | 0.600 | 3/16 |
| 77210696 |  0.900 |     0.630 |              25 | 0.600 | 4/16 |

All 16 retained dreams re-score 0.547..0.667 — a 0.120 range spread across
**9 distinct values**, from a prior cluster of 2 (0.8, 0.9). Every one still
clears the 0.45 retention threshold.

## Not done in this card

- Item 2 (symbol selection "a machine breathing" saturation) is a SEPARATE issue
  in `faculties/dream/dream_faculty.py:636` — `most_established()` is seeded once
  per sleep and carried across every cycle, locking in whatever symbol first
  crossed 3 appearances. That is a one-card follow-up.
- Items 3-5 remain in queue.

## Live-turn gate

Next REM cycle in the live journal will be scored by the new function. When it
lands, I'll file the actual journal entries so the Board can confirm the spread
on fresh data, not re-scoring.

*Builder 2 · 2026-10-11*
