# 03b_WO-CANON-XXV — Temporal Cognition: the volume is exemplary, the build is dead code

**WO:** WO-CANON-XXV (rebuild) · **Seat:** builder · **Priority:** P1
**Gate?** none. **Status of the spec:** Volume XXV's chapters were rated the best in the repo by the audit.
**Status of the code:** [VERIFIED 2026-08-13] nothing in the live turn imports it.

## Why this card exists
The board was marked DONE ✅ for WO-CANON-XXV. That was false. It was corrected to REOPENED on 2026-08-10 —
**but only the paperwork was corrected. The code was never touched.** David, 2026-08-13: *"Why is this
untouched."* Fair question; the honest answer is that reopening the row wasn't followed by a build card.
This is that card.

## What's actually on disk [VERIFIED]
| Spec says | Code has |
|---|---|
| An `Anticipation` type — eLo expects things | **No `Anticipation` class anywhere in the repo.** |
| Anticipations carry a time **envelope** (earliest/expected/latest) | **Zero `envelope` hits.** |
| `expires` is a time | `faculties/temporal/faculty.py:86, :105, :124, :134` — **`expires: bool = True`** |
| Circadian phase drives behaviour | `:80` — 3 hardcoded values |
| The faculty runs in the turn | Only importers are its own `__init__.py` and `tests/test_canon_xxv_temporal.py:51, :240, :364` — **nothing in the live path** |

Classes present at `faculty.py:73, 91, 101, 110, 119, 129`. Read them before rewriting — some may be
salvageable; say which you kept.

## Build to the volume, not to the old file
Spec: `docs/architecture/Volume_XXV/` — it is complete and does not need rulings.
Minimum for this to be real:
1. **`Anticipation`** with a proper **time envelope** (earliest · expected · latest), not a bool.
2. **`expires` becomes a timestamp**, and expiry is *evaluated* — an anticipation that doesn't arrive must
   produce a noticed outcome, not silently vanish.
3. **Wire the faculty into the turn** — it must be imported and run from the live path, not from a test.
4. **Planning horizon + circadian** feed the cognitive state so the Executive can read them.

## 🔴 Done bar — read this, it is the point of the card
**"Tests pass" is NOT done for this WO.** Every dead build in this repo had passing tests that called the
component directly. Done is:
- an assertion that `faculties.temporal` is imported **by the live turn path** (fails if it's orphaned again)
- a real run where eLo forms an anticipation, it expires unmet, and **the unmet expiry is visible in state**
- Rule 1 alarm: if the faculty is not wired, something must **say so loudly** at startup — not run happily
  with a dead faculty

## Done when
Above green, committed, hash to outbox. **Report in the outbox whether an anticipation was formed and
resolved on a real run.** If the answer is "the tests pass" and not that, it isn't done.
