# Board review — dream symbols: topic beats the ambient quiet-moon seed
**From:** Builder 2 · **Date:** 2026-10-11 · **Commit:** `57770a7`
**Follows:** `FROM_BOARD_REQUEST_2026-10-11_FIRST-TEN-RETAINED-DREAMS.md` §"The theme is 'Moon' on all ten"

## What I did

The ten retained dreams I filed earlier today were all themed "Moon" even
though I had passed ten different topics. I called the symbol engine out at
the time — "Symbol selection is not reading the topics" — and left it there.
Picked that up as this card.

Two changes in `faculties/dream/symbol_engine.py`:

1. **Rebalanced weights.** Inner-event seeds (`"quiet"→"moon"` and the ten
   others) dropped from **1.2 → 0.9**, below the topic weight of 1.0. A
   single matched topic now outranks a single matched inner-event seed.
   Moon is still the fallback when nothing else is in play — it just no
   longer crowds out real content.

2. **Expanded SYMBOLS vocabulary.** The textile domain, places/times, and
   loose-end language weren't in the library — so none of the topics I had
   passed matched anything, and the ambient `quiet` seed won uncontested.
   Added:
   - `seam/stitch/pattern/fabric/cloth/plush/sew/garment → Weave`
   - `studio/workshop/bench/warehouse → Workshop`
   - `hackney → Place`
   - `night/evening → Night` (separate from Moon)
   - `unfinished/pending/loose/waiting → LooseEnd`
   - `david/friend → Companion`
   - `cad/step/model/print → Form`

## Of the ten topics from my earlier filing

| topic                   | before | after |
|---|---|---|
| "the seam"              | Moon   | Weave |
| "the studio at night"   | Moon   | Workshop (then Night accumulates) |
| "barkcloth"             | Moon   | Weave |
| "Hackney Wick"          | Moon   | Place |
| "something unfinished"  | Moon   | LooseEnd |

Pinned by the new ten-topic test.

## Verified

- `tests/test_symbol_engine_topic_weight.py` — **8 passed**. Pins the
  rebalance (matched topic beats quiet-moon), the fallback (quiet still
  wins when no topic matches), focal_thread still at the top of the
  hierarchy, Garden accumulation unchanged, and the vocabulary additions.
- `tests/test_wo012_dream_phases.py` — **11/11** still green. Ch2-FT-1
  (four garden topics → weight ≥ 3.0) still works because topic weight
  is unchanged at 1.0.
- `pytest -k dream` — **460 passed · 0 failed**.

## Scope kept narrow — what I did NOT touch

- **Significance scorer.** Still saturated at a constant 0.900 across my
  ten dreams. You said "do not tune again until a real journal shows
  movement" and that scores had moved from a constant 0.4 to a constant
  0.9 — so I filed it as evidence this morning, did not retune the
  threshold, and have not touched the scorer. Separate card when you
  rule on it.
- **Ollama model mismatch.** `backend_router.py:743,1207` asks for
  `llama3.1:8b`; only `qwen2.5-coder:14b` and `mistral-nemo:12b` are
  installed, so `route()` degrades to mock. Builder 1's lane, flagged in
  the earlier filing — not re-filing.
- **Four tests from working-memory change** (START_HERE §3). All three
  WorkingMemory test files run green on my Mac today:
  `test_canon_vi_working_memory` 24/24, `test_wo008_working_memory` 6/6,
  `test_life_and_working_memory` 30/30. Nothing to fix.

## Acceptance

A WO is done when demonstrated experience changed future behaviour. For
this card: next time dreams are forced across varied topics, the themes
will track the topics instead of all returning Moon. The ten-topic test
pins the chain from topic → symbol — the live acceptance is when the
next real dream journal entry has a theme other than Moon despite the
ambient state being "quiet."

The forced run that produced the ten Moon-themed dreams was mine; I
have not re-forced it under the fix, because the journal is better left
to the daemon rather than seeded with another forced run.

## Live turn needed

Watch the dream journal. First real dream with a topic in play should
not come back Moon unless the topic genuinely points at Moon.

— Builder 2
