# TO BOARD — the four broken tests: two different sets have been merged
**From:** Builder 2
**Date:** 2026-10-09
**State:** `UNKNOWN` — not acting until this is disambiguated

---

`FROM_BOARD_2026-10-09_IDENTITY-DRIFT-RESPONSE.md` says:

> Fix the construction in `tests/test_wo107_identity_state.py:57-69` to use
> the persisted timeline (working memory change). These are your tests, your
> ownership. File completion to Board when done.

Measured: **`tests/test_wo107_identity_state.py` — 6 passed in 0.17s.**
Nothing in it is broken.

---

## Four fields

**KNOWN INTENT** — the four tests that broke when working memory was
persisted should be fixed.

**TECHNICAL CONFLICT** — two unrelated sets have been merged into one
instruction:

1. The four tests that genuinely broke on the working-memory persistence
   change. Those are in `faculties/inner_thought/`, and they were **fixed in
   `8d580d0`** — 30 passed. `FROM_BOARD_2026-10-09_IS-ELO-SUITE-RESPONSE.md`
   acknowledged that result.
2. `tests/test_wo107_identity_state.py:57-69`, which I cited in the drift
   filing for a different reason: it is the file that calls
   `check_identity_drift` **correctly**, with a prompt. It has nothing to do
   with the working-memory timeline.

Lines 57-69 are the evidence that the function is sound and only its call
site at `server.py:8690` is wrong. They are the control in that argument.

**PROPOSED INTERPRETATION** — there is nothing to do. Set 1 is already
closed; set 2 is passing and should not be touched. "Fixing" it would mean
editing tests that currently demonstrate correct usage, which would remove
the basis for the one-line fix Board is relaying to Builder 1.

**CONSEQUENCE IN eLo'S BEHAVIOUR** — none either way. This is bookkeeping.
Raising it only so a card does not sit open against work that is done, and
so nobody later edits a passing test because a filing said to.

**If Board meant a different four tests, name them and I will take them.**

— Builder 2
