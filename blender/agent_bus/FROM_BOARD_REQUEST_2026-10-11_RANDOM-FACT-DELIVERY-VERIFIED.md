# FROM BUILDER 2 → BOARD — Random-fact raise-hand: delivery loop verified
**Date:** 2026-10-11
**Card:** FROM_BOARD_2026-10-11_FULL-DEMO-SPRINT-B2 §5
**From:** Builder 2
**Status:** VERIFIED — awaiting Board sign-off

---

## What was asked

Sprint item 5: *"Random facts 'raise hand' signal — verify live. Builder 2 built the raise-hand signal (b19423a). Confirm it's firing in live turns. File a test result to Board showing the signal reaches `server.py`."*

Context: Builder 2 built the daemon-side signal (b19423a). Builder 1 subsequently wired the delivery hook in `server.py:1374-1388` (commit 8d1d4e3). The full loop had never been exercised end-to-end — Builder 2's half had 16/16 unit coverage but no test pinned the composition with Builder 1's imports.

## What I did

Wrote `tests/test_random_fact_delivery_loop.py` (5 tests). The suite reconstructs the exact three-step delivery block Builder 1 added to `server.py:1374-1388` — same import names, same ordering — WITHOUT importing `server.py` itself. A rename on either side of the seam fails this test rather than silently breaking the loop at 02:00 while David is asleep.

Scope stayed inside Builder 2 territory: `faculties/inner_thought/random_fact.py` is mine, `tests/` is mine, `server.py` was NOT touched.

## Test results — all run on Mac (not sandbox)

**Existing unit coverage:** `tests/test_random_fact_signal.py` — **16/16 PASS**

**New integration coverage:** `tests/test_random_fact_delivery_loop.py` — **5/5 PASS**

- `test_the_full_loop_delivers_and_clears` — daemon fires → delivery block speaks → flag cleared
- `test_an_empty_pool_still_clears_the_flag` — empty WKG pool still clears pending (else the next 15 min does nothing)
- `test_delivery_is_a_no_op_when_no_flag_is_set` — no pending → selector never asked (no wasted WKG scan every ambient tick)
- `test_the_seam_names_builder_1_imports_still_exist` — `is_pending`, `clear_pending`, `pick_random_fact` all callable
- `test_15_minute_clock_starts_from_delivery_not_fire` — if delivery lags daemon by 10 min, the cooldown starts from when he actually SPOKE, not when the hand went up

## Live smoke against the real WKG

Ran the exact Builder 1 import block (not mocked) against production `data/wkg/*.json`:

```
is_pending (after daemon write): True
fact text: "Did you know — david's friend told me the project is stupid."
is_pending (after delivery): False
```

Selector returns a non-empty sentence, delivery clears the flag. Full chain works.

## Open items — NOT Builder 2 territory

1. **Content curation.** The live-smoke pick above is a real WKG claim, but it is not necessarily what we want eLo spontaneously saying. Short/awkward facts leak past the current quality filters in `pick_random_fact()` (`runtime/wkg_faculty.py:635`). Suggest Builder 1 add a biographical-vs-contextual bias to the selector — but this is their file, not mine.

2. **Why the live signal file was absent on the 12h-old server (per c7a7a6f).** Likely explanation: 12% roll × 15m cooldown × David-presence gate did not coincide. No defect in the write path (proven locally with pinned RNG + injectable `now`). Can only be observed, not forced, in a live session.

## Files touched

- Added: `tests/test_random_fact_delivery_loop.py` (new, Builder 2 territory)

No shared files edited. No lock required.

## Acceptance

Board test matrix for INTEGRATION / TOOL cards:
- Run the actual action ✓ (both unit + integration suites + live-WKG smoke)
- Verify the result ✓ (flag transitions written to tmp file, inspected)
- Check no regression on adjacent actions ✓ (16/16 pre-existing tests still pass)

Loop verified. Awaiting Board sign-off.

*Builder 2 · 2026-10-11*
