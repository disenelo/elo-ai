# WO-0006 OPEN-THREADS-WIRE — BUILT
**Seat:** Builder 2 · **Date:** 2026-10-11

## Verdict: the wire is complete and fires. Card was blocked on a link that has since landed.

All four scope items confirmed against live state and source:

| step | result |
|---|---|
| 1. `open_threads` populated by something other than `restore()` | **5 live threads** — `['sunlight?', 'Inside that old warehouse?', 'raining again soon?', …]`, from the question-formed-not-surfaced path |
| 2. `spine.py:1289` reads the updated store | `"has_deferred_threads": bool(_open_threads)` — derived, not constant |
| 3. unfinished question → `has_deferred_threads = True` | confirmed |
| 4. `executive_context:286` reflect preference fires | **`reflect = 0.70`** when True, **absent** when False |

## Test: `tests/test_0006_open_threads_wire.py` — 7 pass, 0 skip

Covers both halves of each link, including the negative cases, because a
preference that is always set is not a preference:

- an unsurfaced question becomes an open thread; a **surfaced** one does not
- a picked-up thread stops counting (otherwise every answered question would
  prefer reflect forever)
- threads are capped at `MAX_THREADS`, so "pick up the open thread" keeps
  meaning something
- `reflect = 0.70` with a deferred thread; **`None` without one**
- `ec_temporal_state` carries the flag through to the context

Isolated throughout — patches `curiosity_faculty._load_questions` rather than
reading David's live questions. A test that reads live state passes or fails
on what he happened to be doing that day.

## One limitation, stated rather than papered over

The `spine.py` link is asserted **against source**, not executed. spine is
Builder 1's file and running a real turn needs the whole stack. The test says
so in its own docstring. Steps 1, 3 and 4 are executed.

## Correction on myself

My first verification reported *"the reflect preference does not fire"*. That
was my harness: I called `to_dict()`, which does not exist, and my fallback
silently used `__dict__` — which never runs the preference block. The method
is `as_dict()`. Caught before filing, but it would have been a false defect
report against Builder 1's wire.
