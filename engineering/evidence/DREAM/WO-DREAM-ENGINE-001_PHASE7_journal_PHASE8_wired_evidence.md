# WO-DREAM-ENGINE-001 PHASE 7 (close) + PHASE 8 (wired)

**Filed by:** Builder 2 · 2026-09-27
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13

---

## STATE BEFORE

**PHASE 7** — the journal carried 14 keys. Everything PHASES 1–4 produced was
nested inside `cycles`, so a journal reader had to walk the cycle list to
find seeds, prompts, the dream world or the emotion vector. Of the 24 fields
the §7 schema names, 10 were missing.

**PHASE 8** — `dream_review.py` was built and tested (`193e68b`, ladder
`9f3b756`) but **nothing called it.** The wake transfer gate existed and
never ran.

## WHAT CHANGED

`_complete_journal_entry()` runs last in `run_dream()` and does two jobs:

1. **Flatten** — `seeds`, `prompts`, `emotion_vector`, `dream_world`,
   `dream_rule`, `transformations`, `wkg_relationships`, `memories_used`
   lifted to the top level.
2. **Review** — PHASE 8 now runs on the real dream path, and its cognitive
   channel is folded in: `significance`, `retained`, `candidate_insights`,
   `new_associations`, `spg_patterns`, `unresolved_questions`.

**24/24 §7 fields present.**

## STRICTLY ADDITIVE

The §7 schema calls it `sleep_phase`; the existing journal calls it `phase`.
Renaming would break every reader of the 108 entries already on disk, so
`sleep_phase` is **added alongside** `phase`, not instead of it. Same for
every other original key. A test asserts all 14 survive, and a separate test
asserts `phase` is not renamed.

`scene_images` and `final_artwork` are always present — empty when no artwork
ran — so a reader never has to test for key existence to learn a dream
produced no images.

---

## WIRE-CUT PROOF

Cut: stop folding the review in, and rename `phase` instead of aliasing it.

```
WIRE CUT: review fold removed + phase renamed instead of aliased
FAILED test_every_wo_schema_field_is_present[unresolved_questions]
FAILED test_schema_is_complete_even_on_a_short_dream
FAILED test_original_keys_survive[phase]
FAILED test_phase_is_not_renamed_to_sleep_phase
FAILED test_review_outputs_are_in_the_journal
FAILED test_candidate_insights_carry_the_promotion_stage
FAILED test_unresolved_questions_come_from_the_review
FAILED test_completion_is_idempotent
8 failed, 47 passed
```

Restored:

```
55 passed in 0.23s
```

Both halves are load-bearing: the schema guards and the additive guards fail
independently.

---

## REAL RUN

```
WO §7 SCHEMA — 24 fields
  dream_id                     ok   '3908230d'
  date                         ok   '2026-09-27'
  duration_s                   ok   0.0
  cycle_number                 ok   5
  sleep_phase                  ok   'NREM+REM'
  dream_intensity              ok   1.0
  seeds                        ok   list[13]
  memories_used                ok   list[6]
  wkg_relationships            ok   list[3]
  spg_patterns                 ok   list[2]
  emotion_vector               ok   dict[7]
  dream_world                  ok   dict[7]
  dream_rule                   ok   'Nothing casts a shadow'
  transformations              ok   list[3]
  prompts                      ok   list[14]
  scene_images                 ok   list[0]
  final_artwork                ok   None
  unresolved_questions         ok   list[1]
  new_associations             ok   list[3]
  recurring_symbols            ok   list[1]
  personality_delta_proposed   ok   None
  insight                      ok   'the arm stalls at the same angle'
  memory_refs                  ok   list[0]
  output_type                  ok   'DREAM'
  -> 24/24 present

PHASE 8 REVIEW FOLDED IN
  significance        : 0.6
  retained            : False
  surfaces_directly   : False
  candidate insight   : stage=IDEA class=HYPOTHESIS origin=dream_simulation
  new_associations    : 3
  spg_patterns        : 2
  unresolved_questions: ['still unresolved — what does eLo become when embodied?']

ADDITIVE CHECK — original keys still present
  ['phase', 'timestamp', 'theme', 'symbols', 'narrative', 'image_ref', 'mood', 'curiosity', 'session_read', 'focal_thread']
  phase == sleep_phase: NREM+REM == NREM+REM

VERIFIED anywhere in the entry: False
journal line written: 1 entry
```

Reading it:
- All 24 §7 fields present on a real dream.
- The PHASE 8 gate ran: significance 0.6, below the 0.72 retention
  threshold, so the insight stays at stage `IDEA` as `HYPOTHESIS` with origin
  `dream_simulation`. It has not been promoted.
- `surfaces_directly: false` is recorded in the journal itself — the faculty
  does not address David, and the entry says so.
- Every original key survives; `phase` and `sleep_phase` agree.
- The string `VERIFIED` appears nowhere in the entry.

## NOT PROVEN

- **Not live.** No dream has fired on the running server (PID 9577, up 5h+,
  pre-`ff98065`). This ran out of process.
- **The Executive does not consume the review yet.** PHASE 8's output is in
  the journal; routing it to waking cognition is PHASE 8's remaining half and
  belongs in `server.py`.
- `duration_s` reads 0.0 because the whole dream completes in well under a
  second without a real LLM or image calls. It measures real elapsed time.

## STATUS

PHASE 7: `IMPLEMENTED → WIRED → TESTED`.
PHASE 8: `WIRED` into the journal; **not routed to the Executive**.
Neither LIVE VERIFIED. Not declaring PASS.
