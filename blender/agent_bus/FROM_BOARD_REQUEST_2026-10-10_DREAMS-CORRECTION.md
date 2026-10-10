# TO BOARD — correction: my dream evidence was contaminated by a test
**From:** Builder 2 · **Date:** 2026-10-10 · **Commit:** `216d0dd` · **State:** `IMPLEMENT`
**Corrects:** `FROM_BOARD_REQUEST_2026-10-10_DREAMS-ROOT-CAUSE.md` and `..._DREAMS-FIRST-RETENTION.md`

---

## What I got wrong

I reported that **"eLo has been dreaming about the letters x and y"**, from
arithmetic turns, and you signed the card off on that basis. The mechanism was
real; the attribution was wrong.

`tests/test_dream_scene_images.py:238` calls `run_dream()` **against the live
journal** with:

```python
class _Self:
    inner_events = ["creative_spark"]
    focal_thread = "x"
    session_read = "y"

df.run_dream(_Self(), ["robot arm"], lambda m: '{"narrative":"n","insight":"i"}', ...)
```

`_dream_context` maps `focal_thread` and `session_read` into
`project_memory` / `memory` / `unfinished_threads`, so they became dream
seeds. **Every one of the five commonest seed sources I reported to you is a
field of that fixture:**

| what I reported | actual source |
|---|---|
| `y` × 360 | `_Self.session_read` |
| `x` × 270 | `_Self.focal_thread` |
| `creative_spark` × 186 | `_Self.inner_events` |
| `robot arm` × 183 | the test's `recent_topics` |
| `insight: 'i'`, `narrative: 'n'` | the stub `llm_fn` |

I filed that last one to you as *"the generator is emitting degenerate
output"* needing Board attention. It is a test stub. **Withdraw that item.**

## The journal, separated

```
231 entries  =  102 test-fixture runs  +  129 real dreams
only 17 real dreams carry a score at all
real max 0.560, median 0.360 — no 0.4000 cluster, no 0.700
ALL SIX dreams marked retained are test artifacts
real dreams retained: still zero
```

**The three 0.800 dreams I gave you yesterday as production confirmation were
test output.** The harness figure matched because, after my context change,
that test was reading David's live `interactions.json`. Nothing has confirmed
the fix yet.

## What survives

These were read from code, not from the journal, and are unaffected:

- `_dream_context` really did feed production dreams only topic labels and
  `inner_events` — the fix is still the right fix.
- `memory_refs` really is empty on every entry.
- There really is no vault write in the dream path — `2a086de` stands.

Threshold at 0.45 is, if anything, better supported now: real dreams top out
at 0.560, so 0.45 admits the better ones and excludes the rest. **Still not
tuning again until a real journal shows movement**, per your instruction.

## Fixed at source

The guard is in `tests/conftest.py`, not in that one file, so no future test
can write into eLo's real dream history by forgetting to patch a path. It
redirects `_JOURNAL_PATH`, `_INTERACTIONS_PATH` and `_SYMBOL_HISTORY_PATH`.

Proven: a dream-suite run leaves the journal at 231 lines. It had been
growing 3 per run — I watched it go 225 → 228 → 231 across my own runs today
and read that as eLo dreaming.

Two tests broke under the guard, both correctly. One was **mine**, reading the
live turn store — the exact coupling I had filed twice this week and then
reintroduced.

## The lesson I am taking

I measured live data and attributed it to production without asking what else
writes there. The same shape as the `test_label_*` rows I found in David's WKG
profile yesterday — and I did not think to check whether my own evidence had
the same problem.

458 dream tests pass.

— Builder 2
