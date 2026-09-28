# WO-CAP-EMB-052 — eLo should understand dreams, simulations and memories as different states

**Date:** 2026-09-28
**Seat:** Builder 2
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · pytest 9.1.1
**Commits:** `18d6a09` (vocabulary) · `479a5d3` (wired into the dream journal)
**Source:** `SOURCE_2026-09-19_eLo_EMBODIMENT_LEARNING_MEMORY.md` §52

**STATUS: TESTED.** Not LIVE VERIFIED — see LIVE EVIDENCE.

---

## THE GAP

All thirteen §52 terms already appeared somewhere in the tree. None of them
appeared as a *state*. They were spread across three unrelated vocabularies,
and most of the words meant something else entirely:

| §52 term | what was actually in the tree |
|---|---|
| Pattern | `re.compile` patterns in `social_reflex`, `backend_router`, `voice_rewrite` |
| Instinct/reflex | `runtime/social_reflex.py` — a greeting matcher |
| Inference | a word in prompt text |
| Simulation | `dream_simulation`, an origin — not "let's test this virtually" |

The three real vocabularies each carried a slice and none carried the set:

- `MemoryOrigin` — where a memory came from
- `runtime/wkg_faculty._EPISTEMIC_CLASSES` — how well a fact is attested
- `dream_review.PROMOTION_LADDER` — how far an insight has climbed

Nothing could answer *which state is this claim in*, which is what §52 asks
for. `runtime/cognitive_state.py` is that answer.

## WHAT THE DISTINCTION DOES

Naming thirteen states changes nothing on its own. The load-bearing part is
that only three of them may assert that something occurred, and that no state
may be spoken in another's voice.

```
§52 — the thirteen states, as built
STATE            MEANING                                may claim it happened
Memory           This happened                          True
Knowledge        This is known                          False
Inference        This follows from evidence             False
Pattern          This keeps recurring                   False
Hypothesis       This might be true                     False
Imagination      Let's explore this                     False
Dream            Unconstrained/background association   False
Simulation       Let's test this virtually              False
Prediction       I expect this                          False
Observation      This is happening                      True
Instinct/reflex  Respond quickly                        False
Decision         Executive selected this                False
Action           We actually did it                     True

no state may be spoken as another
  dream        as memory       -> False
  simulation   as action       -> False
  prediction   as observation  -> False
  hypothesis   as knowledge    -> False
  memory       as memory       -> True

the three existing vocabularies, classified
  MemoryOrigin.real_experience        -> memory
  MemoryOrigin.episodic_trace         -> memory
  MemoryOrigin.consolidated           -> memory
  MemoryOrigin.dream_simulation       -> dream
  MemoryOrigin.dream_insight          -> hypothesis
  MemoryOrigin.self_model             -> knowledge
  MemoryOrigin.semantic               -> knowledge
  MemoryOrigin.simulated_experience   -> memory
  MemoryOrigin.physical_experience    -> memory
  epistemic VERIFIED             -> knowledge
  epistemic HISTORICAL           -> memory
  epistemic SOURCE_ATTRIBUTED    -> knowledge
  epistemic SYMBOLIC             -> dream
  epistemic HYPOTHESIS           -> hypothesis
  epistemic SPECULATIVE          -> imagination
  epistemic DISPUTED             -> hypothesis
  epistemic UNKNOWN              -> hypothesis

§51's axis stays separate — both are MEMORY, only one may claim a body
  simulated_experience   state=memory    physical_experience=False
  physical_experience    state=memory    physical_experience=True

wired — the promotion ladder in the dream journal
  stage=DREAM       cognitive_state=dream       claims it happened=False
  stage=IDEA        cognitive_state=imagination claims it happened=False
  stage=EVALUATION  cognitive_state=hypothesis  claims it happened=False
  stage=TEST        cognitive_state=simulation  claims it happened=False
  stage=KNOWLEDGE   cognitive_state=knowledge   claims it happened=False

fail-safe — unlabelled records
  ''               -> hypothesis  claims it happened=False
  'made_up_origin' -> hypothesis  claims it happened=False
  None             -> hypothesis  claims it happened=False
```

## §51 IS A DIFFERENT AXIS AND STAYS ONE

`simulated_experience` and `physical_experience` both classify as **MEMORY** —
both happened. Which *body* did it is §51's distinction and stays in
`memory_origin.py`, where only the physical one answers True to
`can_claim_physical_experience()`.

Folding §51 into §52 would have read tidily and lost a distinction David
called non-negotiable. Pinned by `test_embodiment_axis_is_orthogonal_and_preserved`.

## WIRED

`CandidateInsight.cognitive_state` is derived from `stage`, never stored
beside it, so the EMB-031 ladder and the EMB-052 vocabulary cannot drift apart
the way the three existing vocabularies already had. It lands in `as_dict()`,
so every retained insight in the dream journal now carries its state.

The invariant that falls out: **no rung of the ladder reaches MEMORY,
OBSERVATION or ACTION.** A dream is never evidence that anything happened,
however far its insight climbs — not even at KNOWLEDGE, which is "This is
known", not "This happened".

## BOARD CROSS-CHECK, EXECUTABLE

The cross-check rule for this WO is mechanical: *"For each line of the source
spec ... Unmatched source lines = FAIL."*

`test_every_source_line_is_represented` opens the work order, parses the
VERBATIM SOURCE block, and compares every State/Meaning pair against the
build. It goes red if source and build ever drift. Board does not have to take
my word for the table; the suite re-derives it from the source on every run.

Rule 4b is pinned too: `test_instinct_reflex_is_not_slash_collapsed` fails if
"Instinct/reflex" is ever shortened.

## TEST RESULTS

```
tests/test_cap_emb_052_cognitive_state.py        24 passed
```

Regression, all green after both commits:

```
dream + battery + EMB + origin + wkg + image_gen + live_state   743 passed
```

## WIRE-CUT

| cut | result |
|---|---|
| `may_assert_as` returns True + every state may claim occurrence | 10 failed |
| drop PATTERN from the vocabulary | 3 failed |
| slash-collapse "Instinct/reflex" → "Instinct" | 3 failed |
| `cognitive_state` returns MEMORY for every stage | 3 failed |
| restored | 24 passed |

## LIVE EVIDENCE

**NONE.** Tier 5 is not satisfied, and the WO asks for a real-server JSONL
exchange.

The running server does not carry these commits, and it still does not carry
`b9f29fe` or `15af57b` either — so no dream has fired live, and the dream
journal that would show `cognitive_state` in a real record has no real record
to show. The evidence above is observed on the real code path, out of process.

A restart is the gate. That is the same gate as the DREAM and CAP-EMB cards.

## KNOWN, NOT DONE

- **The guard is available, not enforced at the response layer.** Nothing
  calls `can_claim_occurred()` before eLo speaks. `runtime/claim_gate.py` is
  where it would go, and that is the response path Builder 1 is active in.
  Identical half-closure to EMB-051, and for the same reason — stated rather
  than quietly omitted.
- Six states — INFERENCE, PATTERN, PREDICTION, INSTINCT_REFLEX, DECISION,
  ACTION — are named and distinguished but have no producer yet: nothing in
  the tree currently *emits* a record in those states. The vocabulary is
  complete; the coverage is not. They are reachable, not reached.

## BUILDER STATUS

**TESTED.** Not declaring PASS — Board crosschecks.
