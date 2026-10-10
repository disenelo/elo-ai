# TO BOARD — inner thought as pre-processor: built, spec filed
**From:** Builder 2 · **Date:** 2026-10-10 · **Commit:** `d5ab962` · **State:** `IMPLEMENT`

Spec filed to Builder 1 at `blender/agent_bus/builder/FROM_BUILDER2_2026-10-10_INNER-THOUGHT-PREPROCESS.md`,
direct, at your explicit instruction. Noting the routing because it overrides
the standing rule.

## The constraint I had to solve around

David's ruling reverses the goal but not the physics. `early_runner` states
the thought *"does not condition the reply's tokens"* because the LLM inner
voice takes **15–30s under three-seat contention** (4 tokens in 17.8s
measured) and blocking every turn was already ruled out.

So `pre_thought()` is a **second thing**, not a change to that one:

| | | latency |
|---|---|---|
| `pre_thought()` | state eLo already holds. **No model.** Injected before generation. | **0.01–0.27 ms** |
| `early_runner` | the LLM inner voice. Concurrent, expressed after. | 15–30 s, unchanged |

eLo does not need to generate language to know what he was just doing or what
he left unfinished. He already holds it.

## The four answers you asked for

1. **Payload** — `pre_thought(raw) -> {key, inject, complex, why, signals, elapsed_ms}`. Injects under `INNER_THOUGHT_PRE`. `inject` is `""` on most turns and that means *do nothing*.
2. **Complexity** — Builder 1 checks nothing; calling costs less than deciding whether to call. Internally: anaphoric / about-him / overlaps an open thread / ≥12 words, **disqualified at ≤6 words**.
3. **Fast path** — no model, no network, four JSON reads. Budget 1 ms, test fails above 50 ms.
4. **Injection** — three lines appending `pre["inject"]` to `system` before generation.

## What I deliberately held back

An inner thought on every turn is how eLo started narrating his own telemetry.

- `"5 x 52?"` → untouched. Short and correct is not drift.
- Working memory is app focus (`"13:54 Google Chrome"`). **My first version
  injected it into "how are you feeling about the robot shell?"** — the exact
  defect I filed last week. Now gated on turns that ask about recent activity,
  with a test pinning that it stays out.
- Threads and questions surface on word overlap: **relevance, not availability.**

11 tests, written to pin what must NOT be injected as much as what must.
`server.py` untouched.

## Open
One live turn's assembled prompt containing the block, so I can confirm it
lands rather than infer it. That is the only part I cannot see from here.
