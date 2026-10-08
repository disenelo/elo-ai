**WO:** METACOGNITION-INTEGRATION-CHECK · **Seat:** builder2 · **Priority:** P1
**Reserved?** no

## Goal
WO-METACOGNITION-001 (commit 85cc8bf) and WO-UNLEARN-001 were built. Confirm self-improvement faculties are actually wired into live turns — not just built as standalone modules.

## Scope
1. Read `faculties/metacognition/` — find the entry point
2. Find where it is called from `server.py` or `spine.py` (if it isn't, that's the gap)
3. Confirm `self_improvement/` is triggered after each turn (or on the scheduled window)
4. Check `correction_store.py` — is it accumulating corrections from real turns?
5. Run existing metacognition tests

If NOT wired into live turns: spec the wire to Builder 1 (B2 does not touch server.py). File `FROM_BUILDER2_METACOGNITION-WIRE-SPEC_<date>.md` for Builder 1's queue.

## Files to touch
`faculties/metacognition/` (read) · `self_improvement/` (read) — audit only

## Done when
Wiring confirmed (or gap specced to B1). Test pass result recorded.

## Result
- commit: ``c2a85de``
- test: `test_response_assessment` + `test_wo_metacognition_001` + `test_correction_capture` — 47 passed
- notes:

**1. Entry point** — `faculties/metacognition/` holds 5 modules. Four are
   wired; one is not.

   | module | reached from | status |
   |---|---|---|
   | `correction_capture` | `ambient_engine:391` | wired |
   | `deferred_threads` | `ambient_engine:402` | wired |
   | `open_question_capture` | `inner_thought_first:270` | wired |
   | `response_assessment` | via `correction_capture` | wired |
   | `metacognition.py` | **nothing** | **the gap** |

**2. Called from server.py / spine.py?** No — and that is fine. The live path
   runs through `ambient_engine`, which server.py starts at :2286 and which
   ticks every 0.5s. (`test_wo103` defined "live path" as server+spine only
   and reported these as dead code; widened in `a6b986b`.)

**3. self_improvement triggered?** Yes — `correction_store` is called from
   server.py at :5670, :6072, :6487, :8501.

**4. correction_store accumulating from real turns?** Yes. 26 MB,
   47k+ rows, last written 2026-10-08 00:31.

**5. THE GAP, and it is worse than "not wired".** WO-METACOGNITION-001
   (85cc8bf) built `assess_confidence`, `flag_uncertainty` and
   `detect_reasoning_error`. Zero production callers, tests only. Measured
   before wiring anything:

       conf 0.25  uncertain=True  "The eLo robot uses a Raspberry Pi 5 and TPU shell."
       conf 0.50  uncertain=True  "I think maybe it could possibly be around 1972..."
       conf 0.00  uncertain=True  "Yes."

   A well-grounded factual statement scores BELOW a hedged uncertain one, and
   `flag_uncertainty` (threshold 0.6) fires on all three. The score is really
   measuring WKG coverage, which is low across the board. **Wiring it as a
   real signal would have marked every response eLo gives as uncertain.**

   So it is now READ and RECORDED on every verdict, and never acted on —
   `CONFIDENCE_IS_CALIBRATED = False`. Reachable and measurable instead of
   invisible. Same shape as the observe-only Vol XI envelope check.

**Follow-up needed (not mine to rule):** the threshold and the WKG-coverage
   basis need calibrating before confidence can gate anything. Recommend a
   card once ROOT-1 lands — confidence scored on WKG coverage cannot be right
   while the WKG is not growing.

## Live turn needed
Not directly observable — this card is an audit plus an observe-only wire.

The one checkable consequence: ask eLo something he has no WKG backing for,
e.g. **"what's the capital of Burkina Faso?"**. He should answer normally and
NOT hedge — confidence is recorded but does not gate the reply. If he starts
prefacing ordinary answers with uncertainty, the observe-only wiring has been
promoted to a cause by mistake.
