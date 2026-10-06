# RESULT — ROOT-3: graph_loader word-boundary fix
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Status:** ALREADY DONE — no code change needed

---

## Finding

ROOT-3 "graph_loader word-boundary fix" is already shipped.

`knowledge/graph_loader.py:177-181` — `_kw_match()`:

```python
def _kw_match(keyword: str, text_lower: str) -> bool:
    """True if keyword appears as a whole word in text (not as a substring of another word).
    B3-BOARD-RULINGS Issue 3 2026-10-06: bare 'k in t' matched 'ai' inside 'brain'/'again'/'said'.
    """
    return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text_lower))
```

Entity keyword matching uses `re.search(r"\b" + ...)` — word-boundary regex. The old `k in t` substring match that fired on "ai" inside "brain/again/said" is gone.

The WKG claim retrieval function `retrieve_wkg()` at line 400 also uses `_wkg_word_scores()` with word-boundary matching at line 468-473.

## Evidence

B3-BOARD-RULINGS Issue 3 is cited in the commit that introduced this fix. Both `_find_entities()` and `retrieve_wkg()` now use word-boundary matching.

ROOT-3 is closed.
