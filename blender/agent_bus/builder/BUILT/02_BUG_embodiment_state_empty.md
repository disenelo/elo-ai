# 02_BUG_embodiment_state_empty.md — LIVE BUG: EmbodimentState publishes EMPTY on every direct-response turn

**WO:** WO-097 · **Seat:** builder · **Priority:** P0 (live defect, silent) · **Reserved?** no
**Found:** Architect canon audit 2026-08-10 while transcribing the real turn order for Volume IV.

## The bug (ordering defect in the spine)
In `runtime/spine/spine.py` the turn runs:
```
:503  build_embodiment_state(...)      ← publishes response_text / display_text / tts_text
:509  _conversation_faculty(...)       ← this is what SETS direct_response
```
**`build_embodiment_state` runs BEFORE the conversation faculty produces the response.** So on every
direct-response turn, `response_text`, `display_text` and `tts_text` are published **EMPTY**. Silently.

## Why it matters
This is the state the body reads to know what eLo is saying/showing. Publishing it empty degrades every
direct turn and nothing reports the failure — same silent-failure class as WO-096 (the swallowed ImportError).
Two independent silent defects in the perception/embodiment path found in one audit says the pattern needs
attention, not just the instances.

## Scope — exactly this
1. **Reorder:** `build_embodiment_state` must run AFTER `_conversation_faculty` has set `direct_response`.
   Verify no other faculty depends on the current position before moving it (it's a small reorder — check,
   don't assume).
2. **Assert it can't silently regress:** add an assertion/log if `build_embodiment_state` is called with no
   response available on a direct-response turn, so this can never fail quietly again.
3. **Ordering test** — per Volume IV Ch.2, a test that FAILS if the spine sequence changes such that
   embodiment precedes conversation.

## Test (without David)
Run a direct-response turn → assert `response_text` / `display_text` / `tts_text` are POPULATED in the
published embodiment state (currently empty). Assert the ordering test fails if the two are swapped back.

## Done when
implemented + test green + committed → append hash, move to DONE/, outbox line, take next card.
Canon: `docs/architecture/Volume_IV/01_The_Turn_Loop.md` (the transcribed real order) + `02_Ordering_Guarantees_and_Invariants.md` (invariant I-6).
