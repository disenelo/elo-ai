# 03c_WO-101 — the reward signal still learns from LANGUAGE, and there are four Significance shapes

**WO:** WO-101 · **Seat:** builder · **Priority:** P1 — pairs with WO-096B (do them together)
**Gate?** none. **Canon:** ADR-Exec-005 (Learning Through Verified Consequences) · Ruling F.
All facts [VERIFIED] 2026-08-13.

## A. `outcome=` exists but nothing passes it
[VERIFIED] `memory/significance_engine.py:167-174` — the signature is now
`evaluate(raw, response, action, plan=None, state=None, outcome=None)`, with real outcome dimensions at
`:217-231`, ACK-only scorers at `:237-290`, and the correct hard rule at `:225-226`
(`verified == False → outcome_terms = 0`). **That work is done and it is good.**

**But no production caller passes `outcome`.** `memory/journal_router.py:121` and
`faculties/significance/significance_faculty.py:144` both omit it. So live behaviour is **still keyword
tables over user text and reply text** — exactly what ADR-Exec-005 forbids as a reward signal.

This is the same failure shape as WO-095: the capability was built, the wiring wasn't, and the tests
called the capability directly so nothing noticed.

**Fix:** both call sites pass the real outcome (ACK / verified consequence). Where no outcome exists yet
for a turn, pass `None` **explicitly and knowingly** — do not let "absent" and "not wired" look the same.

**Rule 1 alarm (mandatory):** a test that fails if a production caller of `evaluate()` omits `outcome`.
Without it this silently regresses the moment someone adds a third call site.

## B. Four incompatible Significance shapes
[VERIFIED]
| Source | Dimensions |
|---|---|
| Live code `significance_engine.py:30-40` (`_WEIGHTS`) | **9** |
| Live code **when `outcome` is supplied** (`:227-230`) | **12** |
| `adr/ADR-Exec-005…md:82-83` | **7** |
| `Volume_V/05_Significance_Engine.md:51` | **5** |

The audit said three vectors; supplying `outcome` created a fourth. Drift item **O-5.2** is still open at
`ADR-Exec-005…md:147-149`.

### ⚖ ARCHITECT RULING — the live 12-dim vector is CANONICAL
The engine that actually scores is the truth; the documents follow it, not the reverse. **Builder: do not
change the code to match the docs.** Instead:
1. Emit the **same key set every call** — the 3 outcome dims are present always, zeroed when there is no
   verified outcome. A vector whose shape depends on the call site cannot be compared across turns, which
   silently breaks any learning built on it. **This is the actual bug in B, not the doc mismatch.**
2. Report the final canonical key list to the outbox; **I update ADR-Exec-005 §82 and Vol V Ch.5 §51 and
   close FC-2 and O-5.2.** That half is mine — don't wait for it.

## Test (without David)
- Every production call to `evaluate()` supplies `outcome` (or an explicit, logged `None`).
- The returned vector has an **identical key set** with and without an outcome.
- `verified=False` ⇒ all three outcome terms are exactly 0 (guard `:225-226` still holds).
- Regression: a turn with a real ACK scores differently from the identical turn without one. **If those
  two score the same, the reward is still reading language.**

## Done when
Green, committed, hash + canonical key list to outbox.
