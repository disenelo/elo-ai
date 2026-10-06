# RESULT — ROOT-1: WKG Specific-Fact Extractor (WO-WKG-AUTO-POPULATE-001)
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Commit:** 6d5f5e4
**Status:** DONE

---

## Root cause identified

The existing WKG write paths were NOT broken — they were writing the wrong thing.

2232 live claims were already in `memory/wkg/claims.json`, all following the pattern:
```
David Charles → ASSOCIATED_WITH → world
David Charles → ASSOCIATED_WITH → projects
David Charles → ASSOCIATED_WITH → creative
```

These are **category labels**, not facts. The category-match path at `server.py:6659` takes
the first matched category name ("projects", "creative", "memory") and creates an entity with
that as its label — discarding the actual utterance entirely.

When `retrieve_wkg_context_items()` scores claims against a query, it word-matches against
`subject + object + predicate + notes + interpretation`. An object entity labelled "projects"
scores on every turn with that word. An object entity labelled "David is working on TPU shell"
scores only when the query mentions TPU, shell, or robot.

The gap: no path preserved the **specific text** of what David said.

## What was built

**`runtime/wkg_fact_extractor.py`** — pattern-based extraction on `_original_raw`:

| Pattern | Relationship | Significance |
|---------|-------------|-------------|
| "my [X] is [Y]" | HAS_PROPERTY | 0.72 |
| "I'm building/working on [X]" | ASSOCIATED_WITH | 0.65 |
| "I finished/completed [X]" | ASSOCIATED_WITH | 0.67 |
| "the [deadline/version/goal] is [Y]" | HAS_PROPERTY | 0.70 |
| "eLo [has/is/does] [X]" | HAS_PROPERTY | 0.68 |

Each matched entity gets:
- **label**: the full extracted statement (e.g. "David's studio is in Hackney")
- **description**: `Stated: "<first 200 chars of utterance>"` — the actual words

This makes retrieval work: the entity description text carries David's words so
`graph_loader._wkg_word_scores()` can match on them.

Guards:
- Questions (`?` suffix or question-word prefix) → skip
- Utterances > 500 chars → skip (likely code/paste)
- Max 2 facts per turn

## Server.py wiring

`server.py:6577` — called immediately after `populate_wkg_from_turn()`.
Uses same `_wkg_proj` and `_wkg_xid` computed for the entity stub writer.

## Verification

- `python3 -m py_compile runtime/wkg_fact_extractor.py` → ok
- `python3 -m py_compile server.py` → ok
- `tests/test_root1_wkg_fact_extractor.py` — 5/5 pass:
  - FE-1: possessive fact extracted with Hackney in entity label
  - FE-2: questions not extracted
  - FE-3: "I'm building X" pattern matches
  - FE-4: entity description contains utterance text
  - FE-5: silent on broken wkg_faculty

## What ROOT-1 now means

Before: `"I'm shipping DISENELO Seams next week"` → WKG gets `David ASSOCIATED_WITH projects`

After: `"I'm shipping DISENELO Seams next week"` → WKG gets
`David ASSOCIATED_WITH [entity: "David is working on DISENELO Seams next week"] (SOURCE_ATTRIBUTED, 0.65)`
with description containing `Stated: "I'm shipping DISENELO Seams next week"`.

Next session, `retrieve_wkg_context_items("Seams")` word-matches "Seams" against
that entity's label and description → returns the claim → injected into prompt.

## Still open

The category-match path at `server.py:6659` continues writing generic claims — it should
not be removed yet (it captures turns the fact extractor patterns miss). Long-term these
should be deduplicated or the category path should enrich the entity description.

WO-WKG-CONTAMINATION-CLEANUP-001 still BLOCKED (Board authorization required).
