# Board Review — 0094: Graph Loader Word Boundary Fix
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Fix graph_loader retrieval substring pollution: `k in t` matched "ai" inside "brain"/"again"/"said",
injecting false-positive context (e.g. searching "art" matched "Camberwell College of Arts").

---

## Fix status

Already landed in commit B3-BOARD-RULINGS (2026-10-06). `knowledge/graph_loader.py:177-181`:

```python
def _kw_match(keyword: str, text_lower: str) -> bool:
    """True if keyword appears as a whole word in text (not as a substring of another word).
    B3-BOARD-RULINGS Issue 3 2026-10-06: bare 'k in t' matched 'ai' inside 'brain'/'again'/'said'.
    """
    return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text_lower))
```

Both `_kw_match()` (entity retrieval) and `_wkg_word_scores()` (WKG retrieval) use word-boundary regex.
No raw `k in t` substring match remains in the retrieval path.

---

## Tests

```
python3 -m pytest tests/ -k "graph_loader or retrieval" -v
→ 31 passed in 1.01s
```

---

## Board decisions required

None. Implementation correct, 31/31 tests green. No new commit needed.

*Builder 1 · 2026-10-11*
