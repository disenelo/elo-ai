# WO-DREAM-ENGINE-001 — Dream Faculty build evidence

**Filed by:** Builder 2 · 2026-09-26
**Slice:** S3 (START_HERE_B2.md)
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` — Python 3.13.13, pytest 9.1.1

---

## STATE (TESTING_STANDARD state machine)

```
MISSING → IMPLEMENTED → WIRED → TESTED → LIVE VERIFIED → BOARD VERIFIED → RELEASED
                ^^^^^^^^^^^^           ^^^^^^
                reached                unit only
```

- **IMPLEMENTED** — 5 files built.
- **TESTED** — unit level only, 72 tests. The modules are exercised directly.
- **WIRED (partial)** — the S3 wiring defect is fixed: `server.py` now writes
  `intent = "dream"` on the dream path. The 5 new faculty modules
  (sleep_cycle / dream_input / dream_work / prompt_builder) are still NOT
  called by anything — `dream_faculty.py` runs its original single-cycle path.
  Tier 3 (REAL RUNTIME PATH) is satisfied for the intent fix ONLY.
- **NOT LIVE VERIFIED** — the running server (PID 28626) is executing pre-fix
  code. Needs a restart and a real dream trigger.

**Do not read this file as PASS.** It records what was built and what was
observed. Board crosschecks.

---

## THE WIRING FIX — APPLIED (was NOT IN at first filing)

*Updated after the first filing. The section below originally recorded this as
NOT APPLIED; it is now in. The original finding is preserved verbatim.*

`QUEUE/S3-DREAM-WIRING-DEFECT.md` asks for one line at `server.py:~974`:
write `intent = "dream"` alongside `state.mode = "dreaming"`.

**Original finding (NOT APPLIED):** `server.py` was Builder 1's file for
COG-004 RR20 and the Builder 2 brief sequences server.py last. Confirmed
absent against the running system at first filing:

```
$ grep -c 'intent.*=.*"dream"' server.py
0
```

**Now APPLIED — commit `55c7bd7`.** RR20 landed (`3e8dd0c`), then RR21
(`081f663` / `51c2b6b`); `server.py` was clean in the working tree and the
builder seat lock read RELEASED, so the file was taken.

| Line | Change |
|---|---|
| `server.py:981` | enter dream — adds `"intent": "dream"` alongside the existing `state.mode` / `motion.animation` / `lifecycle_state` writes. Nothing replaced. |
| `server.py:1002` | exit dream — adds `"intent": "idle"`, `dream_phase: None`, `dream_cycle: 0`, `dream_intensity: 0.0` (PHASE 9). |

The defect card asks for one field on the enter path. Shipping only that half
would strand eLo in dream intent after waking and Unity would never stand him
up, so the exit half is part of the same fix, not scope creep.

Guarded by `tests/test_s3_dream_wiring.py` — 6 passed, including a check that
the emitted value is one Unity actually accepts
(`EloOSAvatarReceiver.cs:482-485`: `dream` / `dreaming` / `daydream`).

**STILL NOT PROVEN:** Unity receiving it. Source-level guards only.

---

## FILES BUILT

| File | WO phase | Commit |
|---|---|---|
| `faculties/dream/sleep_cycle.py` | PHASE 1 | `a2331e2` |
| `faculties/dream/dream_input.py` | PHASE 2 | `44340fb` |
| `faculties/dream/dream_work.py` | PHASE 3 | `6e76b89` |
| `faculties/dream/prompt_builder.py` | PHASE 4 | `74f8f71` |
| `faculties/dream/__init__.py` | package surface | `dd10953` |
| `faculties/dream/dream_work.py` (concept-extraction fix) | PHASE 3 | `5ad7016` |

Files in the WO but **NOT** built this slice (not in the Builder 2 brief):
`tools/dream_fx.py`, `faculties/dream/layer_compositor.py`,
`faculties/dream/dream_review.py`, `faculties/dream/symbol_history.py`,
`tools/image_gen_agent.py` extension, journal schema extension.

---

## DEFECT FOUND AND FIXED DURING THIS SLICE

Found by reading generated prompts, not by a test. PHASE 3 concept
extraction was putting verbs and participles into noun slots:

```
BEFORE:  "A enormous david standing in a stayed, its watch built from soft metal"
BEFORE:  "a worked the size of a building, unfinished"
BEFORE:  "a felt folded inward until it holds a room"
BEFORE:  "A towering unresolved standing in a stops"

AFTER:   "An enormous david standing in a room, its move built from soft metal"
AFTER:   "A tiny room stands at the edge of an enormous cliff"
AFTER:   "A towering angle standing in a workshop, its theme built from soft metal"
```

Fixed in `5ad7016`. **RESIDUAL, NOT FIXED:** a verb with no -ed/-ing/-ly
form and no determiner in front of it can still reach a secondary slot
("its move built from..."). No POS tagger — the module stays stdlib-only,
so the heuristics are syntactic. Leading positions are now reliably nouns.

---

## KNOWN GAPS — flagged, not invented

1. **Non-REM phase durations are [ESTIMATE].** The WO fixes REM length
   (~10 min cycle 1 → ~40 min cycle 5) but says nothing about NREM/DEEP/
   LIGHT. Marked `[ESTIMATE]` in `sleep_cycle.py`. David/Board to confirm.
2. **No ANGER row in the WO's Emotional Visual Translation table.** The
   emotion vector carries anger; the table has six rows and none of them is
   anger. Routed to `anxiety_fear` as the nearest visual fit and flagged
   in-file. Confirm or add a row.
3. **"12-field template" names 11 fields.** The WO lists SUBJECT through
   ABSTRACTION LEVEL (11) and then mandates a fixed closing sentence on
   every prompt. That sentence is carried as the 12th field `felt_quality`
   so the WO count and the code count agree.
4. **Late-cycle emotion vectors can come back flat** when the late-band
   source material carries no emotion keywords. `dominant_emotion()` then
   returns the first dimension (`joy`) by its documented tie-break, so late
   cycles get joy lighting regardless of content. Observed in the session
   run below, cycles 4 and 5. Not a crash; a quality limit of keyword-based
   emotion parsing on sparse input.

---

## ACCEPTANCE CRITERIA — what this slice covers

| # | Criterion | Status |
|---|---|---|
| 1 | Multi-cycle sleep, REM growing each cycle | COVERED — see SCHEDULE |
| 2 | Intensity affects prompt abstraction | COVERED — see PROMPTS |
| 3 | 7-dim emotional vector per dream | COVERED |
| 4 | Seeds with condensation/displacement/symbolic | COVERED |
| 5 | Dream World rules applied across scenes | COVERED |
| 6 | One image per REM peak, min 2 per session | PROMPTS built, 14 scenes. **No image generated** — PHASE 5 not in this slice |
| 7 | Scene images composited | NOT BUILT — PHASE 6 not in this slice |
| 8 | CompositionDesigner FX | NOT BUILT — PHASE 5 not in this slice |
| 9 | Journal full schema | NOT BUILT — PHASE 7 not in this slice |
| 10 | All outputs tagged DREAM/HYPOTHESIS/CREATIVE | PARTIAL — `OUTPUT_TYPES` defined, not yet applied by a writer |
| 11 | Two output channels | NOT BUILT — PHASE 8 not in this slice |
| 12 | Executive routes dream output | NOT BUILT |
| 13 | Unity receives dream_phase/dream_intensity | `publish()` written, **NOT CALLED** — needs server.py |
| 14 | Recurring symbol tracking persists | NOT BUILT — PHASE 10 not in this slice |
| 15 | Commit hashes filed | DONE — table above |

---

## COMMAND OUTPUT — verbatim

### Wiring fix still absent

```
$ grep -n "dreaming" server.py | head -10
961:        # Writes mode="dreaming" for Unity sleep animation before pipeline runs.
974:                        "state":           {"mode": "dreaming", "emotion": "calm"},
977:                        "lifecycle_state": "dreaming",

$ grep -c "intent.*=.*\"dream\"" server.py
0
0
```

### Full sleep session — all 5 cycles, all 4 phases

Generated against the code as committed at `5ad7016` (post concept fix).

```
SCHEDULE — 5 cycles x 3 phases
  cycle 1  nrem   intensity 0.08  band early   900s
  cycle 1  deep   intensity 0.04  band early   1200s
  cycle 1  rem    intensity 0.20  band early   600s
  cycle 2  nrem   intensity 0.16  band early   900s
  cycle 2  deep   intensity 0.08  band early   1200s
  cycle 2  rem    intensity 0.40  band early   1050s
  cycle 3  nrem   intensity 0.24  band middle  900s
  cycle 3  deep   intensity 0.12  band middle  1200s
  cycle 3  rem    intensity 0.60  band middle  1500s
  cycle 4  nrem   intensity 0.32  band late    900s
  cycle 4  light  intensity 0.44  band late    600s
  cycle 4  rem    intensity 0.80  band late    1950s
  cycle 5  nrem   intensity 0.40  band late    900s
  cycle 5  light  intensity 0.55  band late    600s
  cycle 5  rem    intensity 1.00  band late    2400s  [LONG REM]
  REM durations: [600, 1050, 1500, 1950, 2400]  (10min -> 40min)
  total session: 16800s

---- CYCLE 1 REM  intensity 0.20 (fragmented memory)  rem 600s ----
  sources=[1, 2, 3, 4] band=early dominant=wonder vector={'wonder': 0.333}
  seeds=4 transformations=['symbolic_transformation']
  world: An abandoned becomes station | Objects keep the warmth of whoever last held them | Every door opens onto another scale | symbol=a machine breathing | wonder/anticipation
  SCENE 1 [grounded] intensity=0.08 abstraction=literal mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    An abandoned becomes station. An abandoned becomes station, where objects keep the warmth of whoever last held them; a machine breathing recur throughout. wonder dominant, anticipation beneath it; something is being remembered wrongly. a becomes the size of a building, unfinished. Objects keep the warmth of whoever last held them. Every door opens onto another scale. centred, eye-level, stable horizon. volumetric golden hour light, highly saturated pastels. real surfaces — worn paint, dust, fabric, cold metal. 35mm, natural perspective, shallow movement. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.08 — literal, grounded, minimal transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 2 [transformation] intensity=0.20 abstraction=literal mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    a field of becomes seen from far above. An abandoned becomes station, where objects keep the warmth of whoever last held them; a machine breathing recur throughout. wonder dominant, anticipation beneath it; something is being remembered wrongly. a dream the size of a building, unfinished. Objects keep the warmth of whoever last held them. Every door opens onto another scale. centred, eye-level, stable horizon. volumetric golden hour light, highly saturated pastels. real surfaces — worn paint, dust, fabric, cold metal. 35mm, natural perspective, shallow movement. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.20 — literal, grounded, minimal transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.

---- CYCLE 2 REM  intensity 0.40 (associative dream)  rem 1050s ----
  sources=[1, 2, 3, 4] band=early dominant=wonder vector={'wonder': 0.333}
  seeds=5 transformations=['symbolic_transformation']
  world: An abandoned dream yard | Distance folds — far things are close | Nothing can be completed | symbol=small doors set too high | wonder/nostalgia
  SCENE 1 [grounded] intensity=0.16 abstraction=literal mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    An abandoned dream yard. An abandoned dream yard, where distance folds — far things are close; small doors set too high recur throughout. wonder dominant, nostalgia beneath it; something is being built by no one. the shadow of a dream moving without the thing that casts it. Distance folds — far things are close. Nothing can be completed. centred, eye-level, stable horizon. volumetric golden hour light, highly saturated pastels. real surfaces — worn paint, dust, fabric, cold metal. 35mm, natural perspective, shallow movement. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.16 — literal, grounded, minimal transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 2 [transformation] intensity=0.40 abstraction=associative mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    a corridor made entirely of dream. An abandoned dream yard, where distance folds — far things are close; small doors set too high recur throughout. wonder dominant, nostalgia beneath it; something is being built by no one. a field of servo seen from far above. Distance folds — far things are close. Nothing can be completed. off-centre, one element larger than it should be. volumetric golden hour light, highly saturated pastels. familiar materials behaving slightly wrongly. slightly wide, low angle, gentle distortion at the edges. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.40 — associative, partial transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.

---- CYCLE 3 REM  intensity 0.60 (associative dream)  rem 1500s ----
  sources=[5, 6, 7, 8] band=middle dominant=joy vector={}
  seeds=4 transformations=['symbolic_transformation', 'condensation']
  world: An abandoned angle workshop | Light moves slower than sound | Nothing can be lost | symbol=rooms inside rooms | joy/anticipation
  SCENE 1 [grounded] intensity=0.24 abstraction=literal mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    An abandoned angle workshop. An abandoned angle workshop, where light moves slower than sound; rooms inside rooms recur throughout. joy dominant, anticipation beneath it; something is almost finished and will not finish. a angle folded inward until it holds a room. Light moves slower than sound. Nothing can be lost. centred, eye-level, stable horizon. volumetric golden hour light, highly saturated pastels. real surfaces — worn paint, dust, fabric, cold metal. 35mm, natural perspective, shallow movement. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.24 — literal, grounded, minimal transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 2 [transformation] intensity=0.42 abstraction=associative mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    a corridor made entirely of angle. An abandoned angle workshop, where light moves slower than sound; rooms inside rooms recur throughout. joy dominant, anticipation beneath it; something is almost finished and will not finish. a corridor made entirely of theme. Light moves slower than sound. Nothing can be lost. off-centre, one element larger than it should be. volumetric golden hour light, highly saturated pastels. familiar materials behaving slightly wrongly. slightly wide, low angle, gentle distortion at the edges. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.42 — associative, partial transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 3 [condensation] intensity=0.60 abstraction=symbolic mix={'relevant': 0.5, 'distant': 0.35, 'abstract': 0.15}
    A towering angle standing in a room, its theme built from soft metal, things showing through. An abandoned angle workshop, where light moves slower than sound; rooms inside rooms recur throughout. joy dominant, anticipation beneath it; something is almost finished and will not finish. a robot folded inward until it holds a room. Light moves slower than sound. Nothing can be lost. layered depth, foreground and background disagreeing on scale. volumetric golden hour light, highly saturated pastels. materials merging — glass that holds warmth, metal that folds like cloth. wide angle, tilted, deep focus holding several scales at once. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.60 — symbolic, condensation active. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.

---- CYCLE 4 REM  intensity 0.80 (strong symbolic dream)  rem 1950s ----
  sources=[9, 10, 11, 12, 13, 3] band=late dominant=joy vector={}
  seeds=6 transformations=['symbolic_transformation', 'condensation']
  world: An abandoned time yard | Everything floats | Nothing can be lost | symbol=small doors set too high | joy/distance
  SCENE 1 [grounded] intensity=0.32 abstraction=associative mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    An abandoned time yard. An abandoned time yard, where everything floats; small doors set too high recur throughout. joy dominant, distance beneath it; something is almost finished and will not finish. a time that keeps rebuilding itself. Everything floats. Nothing can be lost. off-centre, one element larger than it should be. volumetric golden hour light, highly saturated pastels. familiar materials behaving slightly wrongly. slightly wide, low angle, gentle distortion at the edges. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.32 — associative, partial transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 2 [transformation] intensity=0.56 abstraction=symbolic mix={'relevant': 0.5, 'distant': 0.35, 'abstract': 0.15}
    a corridor made entirely of time. An abandoned time yard, where everything floats; small doors set too high recur throughout. joy dominant, distance beneath it; something is almost finished and will not finish. a small doors set too high the size of a building, unfinished. Everything floats. Nothing can be lost. layered depth, foreground and background disagreeing on scale. volumetric golden hour light, highly saturated pastels. materials merging — glass that holds warmth, metal that folds like cloth. wide angle, tilted, deep focus holding several scales at once. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.56 — symbolic, condensation active. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 3 [condensation] intensity=0.80 abstraction=surreal mix={'relevant': 0.3, 'distant': 0.4, 'abstract': 0.3}
    A tiny time standing in a workshop, its watch built from warm glass, move showing through. An abandoned time yard, where everything floats; small doors set too high recur throughout. joy dominant, distance beneath it; something is almost finished and will not finish. the shadow of a david moving without the thing that casts it. Everything floats. Nothing can be lost. no stable horizon, the frame folding back into itself. volumetric golden hour light, highly saturated pastels. matter without a fixed state, surfaces that remember other shapes. impossible lens, perspective bending across the frame. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.80 — fully surreal, displacement and abstraction dominant. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.

---- CYCLE 5 REM  intensity 1.00 (maximum surreal / emotional synthesis)  rem 2400s ----
  sources=[9, 10, 11, 12, 13, 3] band=late dominant=joy vector={}
  seeds=6 transformations=['symbolic_transformation', 'condensation', 'displacement']
  world: An abandoned david workshop | Objects keep the warmth of whoever last held them | Nothing can be lost | symbol=a machine breathing | joy/nostalgia
  SCENE 1 [grounded] intensity=0.40 abstraction=associative mix={'relevant': 0.7, 'distant': 0.2, 'abstract': 0.1}
    An abandoned david workshop. An abandoned david workshop, where objects keep the warmth of whoever last held them; a machine breathing recur throughout. joy dominant, nostalgia beneath it; something is being remembered wrongly. a david the size of a building, unfinished. Objects keep the warmth of whoever last held them. Nothing can be lost. off-centre, one element larger than it should be. volumetric golden hour light, highly saturated pastels. familiar materials behaving slightly wrongly. slightly wide, low angle, gentle distortion at the edges. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.40 — associative, partial transformation. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 2 [transformation] intensity=0.60 abstraction=symbolic mix={'relevant': 0.5, 'distant': 0.35, 'abstract': 0.15}
    a david that keeps rebuilding itself. An abandoned david workshop, where objects keep the warmth of whoever last held them; a machine breathing recur throughout. joy dominant, nostalgia beneath it; something is being remembered wrongly. a field of workshop seen from far above. Objects keep the warmth of whoever last held them. Nothing can be lost. layered depth, foreground and background disagreeing on scale. volumetric golden hour light, highly saturated pastels. materials merging — glass that holds warmth, metal that folds like cloth. wide angle, tilted, deep focus holding several scales at once. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.60 — symbolic, condensation active. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 3 [condensation] intensity=0.80 abstraction=surreal mix={'relevant': 0.3, 'distant': 0.4, 'abstract': 0.3}
    An enormous david standing in a room, its move built from soft metal, workshop showing through. An abandoned david workshop, where objects keep the warmth of whoever last held them; a machine breathing recur throughout. joy dominant, nostalgia beneath it; something is being remembered wrongly. a servo the size of a building, unfinished. Objects keep the warmth of whoever last held them. Nothing can be lost. no stable horizon, the frame folding back into itself. volumetric golden hour light, highly saturated pastels. matter without a fixed state, surfaces that remember other shapes. impossible lens, perspective bending across the frame. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 0.80 — fully surreal, displacement and abstraction dominant. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.
  SCENE 4 [abstraction] intensity=1.00 abstraction=surreal mix={'relevant': 0.3, 'distant': 0.4, 'abstract': 0.3}
    A tiny room stands at the edge of an enormous cliff. An abandoned david workshop, where objects keep the warmth of whoever last held them; a machine breathing recur throughout. joy dominant, nostalgia beneath it; something is being remembered wrongly. a corridor made entirely of weight. Objects keep the warmth of whoever last held them. Nothing can be lost. no stable horizon, the frame folding back into itself. volumetric golden hour light, highly saturated pastels. matter without a fixed state, surfaces that remember other shapes. impossible lens, perspective bending across the frame. scale, openness, unusual colour, impossible structures; painterly, photographic depth, no text, no logos, no watermarks, no readable writing. abstraction 1.00 — fully surreal, displacement and abstraction dominant. The image should feel like a remembered experience being transformed, not a literal illustration of the source memory.

TOTAL SCENES: 14  (WO criterion 6 minimum: 2)
OUTPUT TAGS: ('DREAM', 'HYPOTHESIS', 'CREATIVE ASSOCIATION')   ('FACT' deliberately absent)
```

### pytest — verbatim, not truncated

```
tests/test_dream_sleep_cycle.py::test_cycles_1_to_3_go_deep_4_and_5_go_light PASSED [  2%]
tests/test_dream_sleep_cycle.py::test_rem_duration_grows_each_cycle_10min_to_40min PASSED [  4%]
tests/test_dream_sleep_cycle.py::test_rem_intensity_rises_monotonically_to_one PASSED [  5%]
tests/test_dream_sleep_cycle.py::test_deep_sleep_dreams_less_than_nrem_and_rem_in_same_cycle PASSED [  7%]
tests/test_dream_sleep_cycle.py::test_intensity_is_clamped_to_unit_range PASSED [  8%]
tests/test_dream_sleep_cycle.py::test_intensity_labels_match_canonical_scale PASSED [ 10%]
tests/test_dream_sleep_cycle.py::test_content_band_weighting PASSED      [ 11%]
tests/test_dream_sleep_cycle.py::test_state_machine_advances_through_every_phase_then_stops PASSED [ 13%]
tests/test_dream_sleep_cycle.py::test_state_fields_are_the_three_unity_reads PASSED [ 14%]
tests/test_dream_sleep_cycle.py::test_short_sleep_truncates_and_never_reaches_late_band PASSED [ 15%]
tests/test_dream_sleep_cycle.py::test_publish_is_best_effort_and_never_raises PASSED [ 17%]
tests/test_dream_input.py::test_thirteen_source_types_in_canonical_order PASSED [ 18%]
tests/test_dream_input.py::test_band_source_filtering_matches_wo PASSED  [ 20%]
tests/test_dream_input.py::test_emotion_vector_has_exactly_seven_dimensions PASSED [ 21%]
tests/test_dream_input.py::test_unemotional_text_produces_flat_vector PASSED [ 23%]
tests/test_dream_input.py::test_emotion_dimensions_detected_separately PASSED [ 24%]
tests/test_dream_input.py::test_emotional_intensity_normalised_to_unit_range PASSED [ 26%]
tests/test_dream_input.py::test_memory_gravity_has_seven_components_and_unit_range PASSED [ 27%]
tests/test_dream_input.py::test_explicit_metadata_overrides_derived_gravity PASSED [ 28%]
tests/test_dream_input.py::test_recurrence_observed_across_the_field_not_declared PASSED [ 30%]
tests/test_dream_input.py::test_day_residue_is_sources_1_and_2_only_and_untransformed PASSED [ 31%]
tests/test_dream_input.py::test_emotional_peaks_ranked_and_carry_seven_dimensions PASSED [ 33%]
tests/test_dream_input.py::test_collect_selects_sources_by_cycle_band PASSED [ 34%]
tests/test_dream_input.py::test_collect_degrades_to_empty_without_raising PASSED [ 36%]
tests/test_dream_input.py::test_by_gravity_ranks_heaviest_first PASSED   [ 37%]
tests/test_dream_input.py::test_unresolvedness_rises_with_unfinished_cues PASSED [ 39%]
tests/test_dream_work.py::test_seed_count_stays_in_the_three_to_seven_band PASSED [ 40%]
tests/test_dream_work.py::test_seed_count_rises_with_intensity PASSED    [ 42%]
tests/test_dream_work.py::test_seeds_carry_the_wo_schema PASSED          [ 43%]
tests/test_dream_work.py::test_gravity_raises_probability_but_does_not_guarantee PASSED [ 44%]
tests/test_dream_work.py::test_empty_field_yields_no_seeds_and_no_crash PASSED [ 46%]
tests/test_dream_work.py::test_condensation_merges_and_does_not_list_its_sources PASSED [ 47%]
tests/test_dream_work.py::test_condensation_merge_count_scales_with_intensity PASSED [ 49%]
tests/test_dream_work.py::test_displacement_shifts_onto_a_different_subject PASSED [ 50%]
tests/test_dream_work.py::test_symbolic_transformation_uses_canonical_wo_mappings PASSED [ 52%]
tests/test_dream_work.py::test_unknown_concept_is_still_transformed_never_passed_through PASSED [ 53%]
tests/test_dream_work.py::test_dream_world_carries_all_seven_rule_fields PASSED [ 55%]
tests/test_dream_work.py::test_dream_world_accepts_an_observed_recurring_symbol PASSED [ 56%]
tests/test_dream_work.py::test_scene_count_rises_with_intensity_capped_at_four_stages PASSED [ 57%]
tests/test_dream_work.py::test_scenes_progress_grounded_to_abstraction_with_rising_intensity PASSED [ 59%]
tests/test_dream_work.py::test_all_three_mechanisms_applied_across_a_full_intensity_cycle PASSED [ 60%]
tests/test_dream_work.py::test_same_seed_reproduces_the_same_dream PASSED [ 62%]
tests/test_dream_work.py::test_different_seeds_produce_different_dreams PASSED [ 63%]
tests/test_dream_work.py::test_concept_extraction_prefers_noun_heads_over_verbs PASSED [ 65%]
tests/test_dream_work.py::test_participles_and_adverbs_are_never_concepts PASSED [ 66%]
tests/test_dream_work.py::test_nouns_with_participle_suffixes_are_kept PASSED [ 68%]
tests/test_dream_work.py::test_ordinals_are_skipped_in_favour_of_the_head_noun PASSED [ 69%]
tests/test_dream_work.py::test_condensation_setting_slot_is_always_a_place PASSED [ 71%]
tests/test_dream_work.py::test_article_agreement_in_condensation_and_displacement PASSED [ 72%]
tests/test_dream_work.py::test_displacement_fallback_does_not_double_the_article PASSED [ 73%]
tests/test_dream_prompt_builder.py::test_template_has_twelve_fields PASSED [ 75%]
tests/test_dream_prompt_builder.py::test_every_field_is_populated PASSED [ 76%]
tests/test_dream_prompt_builder.py::test_prompt_always_ends_with_the_mandated_final_line PASSED [ 78%]
tests/test_dream_prompt_builder.py::test_emotional_visual_table_has_the_six_wo_rows PASSED [ 79%]
tests/test_dream_prompt_builder.py::test_every_emotion_dimension_maps_to_a_table_row PASSED [ 81%]
tests/test_dream_prompt_builder.py::test_emotion_selects_lighting_and_visual_language PASSED [ 82%]
tests/test_dream_prompt_builder.py::test_abstraction_bands_match_the_wo_thresholds PASSED [ 84%]
tests/test_dream_prompt_builder.py::test_bounded_randomness_proportions_match_the_wo PASSED [ 85%]
tests/test_dream_prompt_builder.py::test_intensity_demonstrably_changes_prompt_abstraction PASSED [ 86%]
tests/test_dream_prompt_builder.py::test_recurring_symbol_present_in_every_scene_of_the_cycle PASSED [ 88%]
tests/test_dream_prompt_builder.py::test_mix_concepts_returns_requested_count_and_falls_back_on_thin_pools PASSED [ 89%]
tests/test_dream_prompt_builder.py::test_same_seed_reproduces_the_same_prompt PASSED [ 91%]
tests/test_dream_prompt_builder.py::test_flat_emotion_vector_falls_back_to_the_dream_world_emotion PASSED [ 92%]
tests/test_dream_package.py::test_package_exports_all_four_phases PASSED [ 94%]
tests/test_dream_package.py::test_output_types_never_include_fact PASSED [ 95%]
tests/test_dream_package.py::test_existing_dream_modules_still_import PASSED [ 97%]
tests/test_dream_package.py::test_full_sleep_session_end_to_end PASSED   [ 98%]
tests/test_dream_package.py::test_late_cycles_are_more_abstract_than_early_cycles PASSED [100%]

============================== 69 passed in 1.00s ==============================
```

### Regression — pre-existing dream suites after the __init__.py change

```
$ ~/miniconda3/bin/python3 tests/test_wo_dream_state.py

============================================================
WO-DREAM-STATE   6 passed  0 failed

$ ~/miniconda3/bin/python3 tests/test_wo012_dream_phases.py
  ✅ Ch2-ST-3: patience proposal, validated=False → routes to Ch.7

Result: 11/11 passed, 0 failed

$ ~/miniconda3/bin/python3 tests/test_canon_xxvi_creative_intelligence.py

================================================================================
WO-CANON-XXVI creative intelligence   25 passed   9 known-gaps   0 failed

```
