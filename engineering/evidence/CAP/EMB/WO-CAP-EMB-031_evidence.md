# WO-CAP-EMB-031 — Dream output treated differently from memory

**Filed by:** Builder 2 · 2026-09-27
**Source:** `SOURCE_2026-09-19_eLo_EMBODIMENT_LEARNING_MEMORY.md §31`
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · pytest 9.1.1
**Commits:** `193e68b` (PHASE 8 gate) · this commit (§31 ladder)

---

## VERBATIM SOURCE §31 — line by line

| Source line | Where it is true in the built system |
|---|---|
| `This is critical.` | — |
| `Dream:` | `faculties/dream/dream_review.py` |
| `should initially be:` | `CandidateInsight.stage` defaults to `IDEA` |
| `HYPOTHESIS` | `epistemic_class = HYPOTHESIS` on every reviewed insight |
| `not:` | — |
| `FACT` | `VERIFIED` is in `FORBIDDEN_EPISTEMIC` and unreachable from a dream |
| `So:` | — |
| `DREAM` | `STAGE_DREAM` — `PROMOTION_LADDER[0]` |
| `IDEA` | `STAGE_IDEA` — every insight starts here |
| `EVALUATION` | `STAGE_EVALUATION` — reached only by clearing significance 0.72 |
| `TEST` | `STAGE_TEST` / `test_insight()` — requires a NAMED source outside the dream |
| `KNOWLEDGE` | `STAGE_KNOWLEDGE` — reachable only through TEST |
| `Not:` | — |
| `DREAM` | — |
| `TRUTH` | No path exists. Proven by wire-cut below. |

---

## STATE BEFORE

PHASE 8 (`193e68b`) gated dreams at EVALUATION only: significance ≥ 0.72
promoted `DREAM_SIMULATION → DREAM_INSIGHT` and stopped there. That satisfies
"HYPOTHESIS not FACT", but **§31 specifies five stages and the build had
three**. There was no TEST stage, so "evaluated" was the end of the ladder.

## WHAT CHANGED

`PROMOTION_LADDER = (DREAM, IDEA, EVALUATION, TEST, KNOWLEDGE)`.

- Significance clears **EVALUATION only**. It no longer implies knowledge.
- `test_insight(insight, corroborating_source)` is the **TEST** gate. It
  refuses when no source is named, and refuses when EVALUATION was skipped.
  A dream cannot test itself — corroboration comes from outside it.
- At KNOWLEDGE the class becomes `SOURCE_ATTRIBUTED`, never `VERIFIED`.
  `wkg_faculty` enforces `SOURCE_ATTRIBUTED != VERIFIED` at its own boundary.

---

## WIRE-CUT PROOF

The tests go RED when the behaviour is removed. Cut: delete the EVALUATION
guard in `test_insight()` and promote the class to `VERIFIED`.

```
WIRE CUT: EVALUATION gate removed, class promoted to VERIFIED
FAILED tests/test_dream_review.py::test_evaluation_cannot_be_skipped
FAILED tests/test_dream_review.py::test_dream_to_truth_is_unreachable_by_any_path
2 failed, 25 passed
```

Wire restored:

```
27 passed in 0.10s
```

The two tests that guard §31 are the two that fail. They are load-bearing,
not decorative.

---

## REAL RUN — JSONL

Produced by driving the real `run_dream()` → `review()` → `test_insight()`
path. Journal and lexicon redirected to tmp; the live stores are untouched.

```jsonl
{"wo": "WO-CAP-EMB-031", "checkpoint": "DREAM -> IDEA (reviewed, significance applied)", "stage": "EVALUATION", "epistemic_class": "HYPOTHESIS", "memory_origin": "dream_insight", "retained": true, "corroboration": [], "is_knowledge": false, "content": "the arm stalls at the same angle"}
{"wo": "WO-CAP-EMB-031", "checkpoint": "TEST attempted with no corroborating source", "stage": "EVALUATION", "epistemic_class": "HYPOTHESIS", "memory_origin": "dream_insight", "retained": true, "corroboration": [], "is_knowledge": false, "content": "the arm stalls at the same angle"}
{"wo": "WO-CAP-EMB-031", "checkpoint": "TEST with corroboration -> KNOWLEDGE", "stage": "KNOWLEDGE", "epistemic_class": "SOURCE_ATTRIBUTED", "memory_origin": "dream_insight", "retained": true, "corroboration": ["bench observation 2026-09-27: arm stalls at 41 degrees"], "is_knowledge": true, "content": "the arm stalls at the same angle"}
{"wo": "WO-CAP-EMB-031", "checkpoint": "EVALUATION skipped -> refused", "stage": "IDEA", "epistemic_class": "HYPOTHESIS", "memory_origin": "dream_simulation", "retained": false, "corroboration": [], "is_knowledge": false, "content": "the arm stalls at the same angle"}
{"wo": "WO-CAP-EMB-031", "checkpoint": "ladder", "PROMOTION_LADDER": ["DREAM", "IDEA", "EVALUATION", "TEST", "KNOWLEDGE"], "VERIFIED_reachable_from_dream": false, "FORBIDDEN_EPISTEMIC": ["CANONICAL", "HISTORICAL", "VERIFIED"]}
```

Reading the rows:
1. Reviewed and significant → **EVALUATION**, still HYPOTHESIS. Not knowledge.
2. TEST with no named source → **refused**, stays at EVALUATION.
3. TEST with corroboration → **KNOWLEDGE**, SOURCE_ATTRIBUTED, source recorded.
4. EVALUATION skipped → **refused**, stays at IDEA as DREAM_SIMULATION.
5. `VERIFIED_reachable_from_dream: false`.

---

## NOT PROVEN

- **Not a live-server exchange.** §31's evidence line asks for a real-server
  turn. This gate is a library boundary, not a conversational capability —
  there is no prompt that exercises it. The rows above are the real code
  path, not a mock. When the Executive routes dream output through a turn,
  that will be the server-level evidence.
- **No dream has fired on the live server.** PID 9577 has been up 5h+ with
  no dream in the journal.
- Tier 7 (OWNER ACCEPTANCE) is David's.

## STATUS

`IMPLEMENTED → WIRED → TESTED`. Not LIVE VERIFIED. Not declaring PASS.
