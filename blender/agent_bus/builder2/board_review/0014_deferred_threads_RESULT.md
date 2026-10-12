# WO-B2-0014 — Deferred threads store — BUILT, with one deliberate deviation
**Seat:** Builder 2 · **Date:** 2026-10-12 · **State:** `IMPLEMENT`

## I did not create `faculties/deferred_threads.json`, and this is why

The card asks for a new store with six fields. **Five of them already exist**
on the curiosity question that *is* the deferred thread:

| card field | already stored as |
|---|---|
| `thread_id` | `question_id` |
| `summary` | `text` |
| `reason` | `reason` (e.g. `inner_thought`) |
| `created_at` | `ts` |
| `status` | `surfaced` → active / resolved |
| `session_id` | **absent** |

`deferred_threads.py`'s own docstring already argues this, from when it was
built: *"There are TWO deferral stores and neither has ever held anything…
No third store. Two empty ones are the problem; a third would be the same
mistake with better intentions."*

A third store would let one question be **open in one place and closed in
another**. So `records()` returns the card's exact shape, read from the one
store that holds them. If Board wants the JSON file regardless, say so and I
will add it as a projection rather than a source of truth.

## What is built

- **`records(include_resolved=False)`** — full thread records in the card's
  shape. 16 active threads live right now.
- **`relevant_to(text)`** — the card's *"picks up a deferred thread when
  relevant context appears"*. Matched on shared content words using the same
  test `pre_thought` uses, so the two cannot disagree about what counts as
  relevant.

Live:

```
"is the sunlight back today?"  ->  "Back from where?"  (reason: inner_thought)
"5 x 52?"                      ->  nothing
```

**Relevance, not availability.** Surfacing every open thread on every turn is
how eLo started narrating his own state; there is a test pinning that a short
factual turn surfaces nothing.

## `session_id` is "" and I left it that way

It would be captured where questions are written — `faculties/curiosity/`,
which is **not Builder 2's seat**. One field at the `store_question` call
site. Specced here rather than reached into. An empty string is honest; a
fabricated session id would not be.

## Not closable from here

The card's "Done when" requires a live turn: David gives context, eLo picks
the thread up unprompted. **Zero turns since the 10-11 23:20 restart**, so the
retrieval is proven in isolation and not in conversation. The chain beneath it
*is* proven — card 0006 confirmed `open_threads` → `has_deferred_threads` →
`reflect = 0.70`, end to end.

11 tests pass.
