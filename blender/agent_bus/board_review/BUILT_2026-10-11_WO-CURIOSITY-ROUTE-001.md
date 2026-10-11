# Board Review — WO-CURIOSITY-ROUTE-001: Curiosity Faculty Injection
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

`curiosity_faculty.top_question()` now reaches the system prompt when topic-relevant.

- `faculties/curiosity/curiosity_faculty.py:224` — `mark_surfaced()` implemented
- `server.py:6091-6111` — injection with relevance gate (topic token overlap OR open-invite phrases)
- Existing `server.py:5058` learning-faculty block preserved (different source, different system)
- Empty block → nothing injected (graceful degradation)

---

## Commit

Pre-existing implementation (WO-CURIOSITY-ROUTE-001 marker in server.py:6091).

---

## Tests — `tests/test_wo_curiosity_route_001.py`

```
pytest tests/test_wo_curiosity_route_001.py -v
→ 4 passed
```

| AT | Result |
|----|--------|
| top_question returns unsurfaced question | ✅ |
| mark_surfaced sets surfaced=True | ✅ |
| top_question returns None when all surfaced | ✅ |
| curiosity_prompt_block empty when no questions | ✅ |

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
