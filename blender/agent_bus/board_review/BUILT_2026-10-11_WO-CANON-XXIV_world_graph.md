# Board Review — WO-CANON-XXIV: One World Graph
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Two world graphs → one. Knowledge now carries confidence + evidence so eLo qualifies not asserts.

Changes (Ruling A):
1. `relationships/world_graph.json` is canonical — `graph_loader.py` reads only this
2. `identity/world_graph.json` retired (marked `_retired:true` with `_successor` pointer)
3. `retrieve()` returns ranked results with `confidence`, `kind`, `evidence[]` fields
4. `strength` = salience (kept separate from confidence)
5. Unknown fact returns `[]` — no LLM backfill (Verified Speech enforced)

---

## Commit

- `964228c` — WO-CANON-XXIV: one world graph

---

## Tests — `tests/test_canon_xxiv_world_graph.py`

```
python3 tests/test_canon_xxiv_world_graph.py
→ WO-CANON-XXIV world graph  5 passed  0 failed
```

| AT | Result |
|----|--------|
| AT-0: graph_loader reads canonical relationships/world_graph.json | ✅ |
| AT-1: retrieve() returns ranked results with confidence+kind+evidence | ✅ |
| AT-2: retrieve() returns [] for unknown input — no backfill | ✅ |
| AT-3: identity/world_graph.json marked _retired:true with _successor | ✅ |
| AT-4: continuity.py reads canonical relationships/world_graph.json | ✅ |

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
