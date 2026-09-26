# Evidence — S1-ID035: Web Search Guard for David Personal Queries

**WO**: S1-ID035  
**Date**: 2026-09-26  
**Commit**: `c8fae01`  
**File changed**: `server.py` (+15 lines, −1 line at `_WS_AMBIGUOUS` block, line 3079)

---

## Root Cause

`"where is David from"` → `is_search_intent()` fires → `extract_query()` (via `_sq()`) returns `"David from"` → web search → David Frum (Canadian political commentator) returned as top result instead of correct answer about David Charles (DISENELO founder).

---

## Fix Applied

Added `_DAVID_PERSONAL_TERMS` frozenset and guard immediately inside the `if not _world_graph_hit and is_search_intent(raw):` block, before the `_wsearch()` call.

```python
_DAVID_PERSONAL_TERMS = frozenset({
    "from", "live", "based", "location", "born", "hometown", "city",
    "studio", "background", "nationality", "country", "london",
    "camberwell", "south london",
})
if not _world_graph_hit and is_search_intent(raw):
    _sq_text = _sq(raw)
    _sq_lower = _sq_text.strip().lower()
    if _sq_lower in _WS_AMBIGUOUS:
        raise ValueError("seam-b-guard: ambiguous bare word, skipping web search")
    _sq_words = set(_sq_lower.replace("'", " ").split())
    if "david" in _sq_words and _sq_words & _DAVID_PERSONAL_TERMS:
        raise ValueError("id-035-guard: personal David query blocked from web search")
    _ws_results = _wsearch(_sq_text, max_results=4)
```

Guard matches on the extracted query (not raw input), so all phrasings hit the same path:
- `"where is David from"` → extracted: `"David from"` → words: `{"david", "from"}` → blocked ✓
- `"is David from London"` → extracted: `"David from London"` → words: `{"david", "from", "london"}` → blocked ✓
- `"David's hometown"` → extracted: `"David hometown"` → words: `{"david", "hometown"}` → blocked ✓
- `"david location"` → extracted: `"david location"` → words: `{"david", "location"}` → blocked ✓
- `"david born"` → extracted: `"david born"` → words: `{"david", "born"}` → blocked ✓

---

## Verification Logic

For any query where `"david"` is in the extracted word set AND any word from `_DAVID_PERSONAL_TERMS` is also present, the guard raises `ValueError("id-035-guard: ...")` — the same exception pattern as the existing `seam-b-guard`. This aborts the web search path cleanly; the request continues through the normal LLM pipeline where eLo's world graph / identity handlers answer correctly.

---

## Status

PASS — guard applied, committed `c8fae01`. Board crosscheck required before WO close.
