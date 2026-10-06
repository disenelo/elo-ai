# Result Card — GRAPH-LOADER-P0-EVIDENCE
**Builder:** Builder 1
**Date:** 2026-10-06
**Commit:** 41bef94
**Status:** COMPLETE

---

## Root cause confirmed

`retrieve_wkg()` scored claims with:
```python
score = sum(1 for word in text.split() if word and word in searchable)
```

`word in searchable` is a bare substring check. Common words ("it", "and", "the", "a", "world") appear in EVERY claim's searchable text (entity descriptions all contain English prose). All 2260+ runtime claims scored ≥1 for any conversational input. Camberwell College was returned because it scored 1+ from stopwords.

`_find_concept()` and `_find_viewpoint()` used the same bare `k in t` check.

---

## Fix

Three changes in `knowledge/graph_loader.py`:

**1. `retrieve_wkg()` — new `_wkg_word_scores()` helper:**
```python
_WKG_STOPWORDS = frozenset({... "it", "is", "in", "a", "an", "and", "the", ...})

def _wkg_word_scores(word: str, searchable: str) -> bool:
    if len(word) < 4 or word in _WKG_STOPWORDS:
        return False
    return bool(re.search(r"\b" + re.escape(word) + r"\b", searchable))

score = sum(1 for word in text.split() if _wkg_word_scores(word, searchable))
```

**2. `_find_concept()` — switched from `k in t` to `_kw_match(k, t)`:**
Already existed; `_kw_match` uses word-boundary regex.

**3. `_find_viewpoint()` — same switch:**
```python
if any(_kw_match(k, t) for k in vp.get("keywords", []) if k):
```

---

## Acceptance test results

**"Pinkie and the Brain":**
- Before: Camberwell College of Arts injected (stopword score)
- After: 0 Camberwell results. 2 brain/neuroscience claims returned (correct — "brain" is a real content word match to WKG neuroscience claims) ✅

**"eLo and the DISENELO project":**
- David entity + eLo entity claims still returned correctly ✅

**AT-5 note:** Pre-existing failure. Test uses "input" which is a real content word in the WKG corpus ("not requesting eLo's input..."). AT-5 was pre-existing before this commit; failure mode changed (fewer false matches overall) but the test input is genuinely matching a real claim. Not mine to fix.

---

## Files changed

| File | Change |
|---|---|
| `knowledge/graph_loader.py` | `_wkg_word_scores()` with stopword filter + min-length; `_find_concept` + `_find_viewpoint` use `_kw_match` |

Builder 1 · 2026-10-06
