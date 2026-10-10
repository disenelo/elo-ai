# TO BOARD — the drift fix lands, but the guard will likely still fire every turn
**From:** Builder 2
**Date:** 2026-10-10
**State:** `PROPOSE` — a prediction with its uncertainty named, filed before turns resume
**Re:** `3794f64` WO-IDENTITY-DRIFT — Builder 1 applied my one-line fix

---

## The fix is correct

`server.py:8701` now reads `_check_drift(_elo_self, system or "")`. That is
exactly what I proposed and it restores WO-107's intent.

**It has not been exercised.** 0 drift rows since it landed — but also **0
turns** since it landed (newest turn 00:53, fix 05:33). The zero proves
nothing yet. Saying so rather than reporting it as verified.

---

## Why it will probably still fire — on every turn

`check_identity_drift` tests whether each of the six `core_values` appears
literally in the text. The text is now the system prompt. Measured:

| trait | in `identity_block`? | in `canonical_identity.md`? | anywhere in `elo_personality_engine/`? |
|---|---|---|---|
| calm | no | **yes** (3) | yes |
| playful | no | **yes** (1) | yes |
| curious | no | **yes** (1) | yes |
| emotionally aware | no | no | `personality_core.md`, `sources/identity.md` |
| grounded | no | no | only JSON configs (`motion_mapping`, `mode_profiles`) |
| **observant** | no | **no** | **nowhere at all** |

Two things compound:

1. `identity_block()` **deliberately omits `core_values`** — David L3's ruling
   2026-08-22, documented in the docstring: *"core_values is experiential
   self-state, not canonical identity."* So the block the guard most obviously
   targets will never satisfy it. Confirmed by running it: all six report
   missing against the identity block alone.
2. **`observant` appears in no personality source in the repo.**

So unless some other part of the assembled prompt supplies them, the guard
fires every turn for at least `observant`, probably also `grounded` and
`emotionally aware` — **three rows per turn, forever**, which is worse than
the ~354 turns it fired on before.

---

## What I have NOT established

I did not assemble the live `system` string. Doing that means running the
server, and it is Builder 1's file. **UNKNOWN: whether the full personality
block injects text containing these three words.** Resolved by one live turn
— or by Builder 1 printing the assembled prompt once.

I am filing it as a prediction rather than a finding because that distinction
is the whole point, and because it is cheap to check before David next talks
to eLo and generates a fresh flood.

---

## The deeper point, unchanged

A substring test over six adjectives still measures vocabulary, not
character. Pointing it at the prompt makes it a **prompt-integrity** check,
which is a real and useful thing — but only if the prompt is actually
supposed to contain those six words. Per the August ruling, it is not: the
canonical traits live in `canonical_identity.md` and `core_values` is a
separate experiential field.

So the guard is now comparing the experiential list against a prompt built
from the canonical list, and those two lists do not match. **The honest fix
is probably to check the canonical traits, or to retire the guard** — not to
keep pointing it at new text.

Not acting. `server.py` and `self/elo_self_model.py` are not mine, and the
August ruling is David's.

— Builder 2
