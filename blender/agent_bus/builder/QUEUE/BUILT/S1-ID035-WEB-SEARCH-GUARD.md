# QUEUE ITEM: S1 — ID-035 Web Search Guard (Personal Identity Queries)
**Stack:** S1 (Pipeline Repair)  
**Priority:** HIGH — live bug, David Frum returning as answer to "where is David from"  
**File:** `server.py`  
**Date authored:** 2026-09-25

---

## ROOT CAUSE (confirmed by Board — do not re-diagnose)

`_SEARCH_TRIGGERS` in `tools/web_search.py` includes `"where is "`. So "where is David from" passes `is_search_intent()`. Then `extract_query()` strips "where is " and returns `"David from"` as the search query. Web search runs → hits David Frum (Canadian political commentator) → injects "David Frum is from Canada." into raw. LLM says "David Frum is from Canada."

The `_LOC_Q_TRIGGERS` guard at line ~2184 exists but is in a code path that may not always intercept before web search. Evidence: `memory/interactions.json` lines 23562-23563 show web search firing on "David from".

The fix adds a second guard directly at the web search call site so it is impossible for web search to fire on personal-identity queries about David.

---

## FIX — `server.py` (exact code, apply verbatim)

**Find this block** (around line 2991 — search for `_WS_AMBIGUOUS = frozenset`):

```python
            _WS_AMBIGUOUS = frozenset({
                "done", "ok", "okay", "yes", "no", "wait", "ready", "waiting",
                "pending", "open", "closed", "next", "back", "forward", "stop",
                "go", "hey", "right", "sure", "cool", "good", "great", "fine", "nice",
            })
            if not _world_graph_hit and is_search_intent(raw):
                _sq_text = _sq(raw)
                if _sq_text.strip().lower() in _WS_AMBIGUOUS:
                    raise ValueError("seam-b-guard: ambiguous bare word, skipping web search")
                _ws_results = _wsearch(_sq_text, max_results=4)
```

**Replace with:**

```python
            _WS_AMBIGUOUS = frozenset({
                "done", "ok", "okay", "yes", "no", "wait", "ready", "waiting",
                "pending", "open", "closed", "next", "back", "forward", "stop",
                "go", "hey", "right", "sure", "cool", "good", "great", "fine", "nice",
            })
            # ID-035 guard: personal identity queries about David must NEVER
            # go to web search. "where is David from" → "David from" → David Frum.
            # Match on the extracted query, not raw, so all phrasings are caught.
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
                # Block personal-identity queries about David from hitting web search.
                # "David from", "david location", "david born", etc. all blocked here.
                _sq_words = set(_sq_lower.replace("'", " ").split())
                if "david" in _sq_words and _sq_words & _DAVID_PERSONAL_TERMS:
                    raise ValueError("id-035-guard: personal David query blocked from web search")
                _ws_results = _wsearch(_sq_text, max_results=4)
```

---

## VERIFY AFTER APPLYING

Run this test (do NOT modify the test file — read-only verification):

```bash
cd /path/to/elo-ai
python3 -c "
from tools.web_search import is_search_intent, extract_query
queries = [
    'where is David from',
    'where is he from',  
    \"where's David from\",
    'where does David live',
    'where is David based',
    'David from',
]
for q in queries:
    sq = extract_query(q)
    words = set(sq.lower().replace(\"'\", ' ').split())
    david_personal_terms = {'from', 'live', 'based', 'location', 'born', 'hometown', 'city', 'studio', 'background', 'nationality', 'country', 'london', 'camberwell', 'south london'}
    blocked = 'david' in words and bool(words & david_personal_terms)
    print(f'  {q!r} → query={sq!r} → blocked={blocked}')
"
```

Expected: All "David from/live/based/location/born" queries print `blocked=True`. "where is he from" prints `blocked=False` (no "david" in extracted query, acceptable — the `_LOC_Q_TRIGGERS` guard at line ~2184 handles first-person queries).

---

## AFTER COMMIT

File evidence note to: `engineering/evidence/ID/S1-ID035-WEB-SEARCH-GUARD_evidence.md`

Include:
- Commit hash
- Output of the verify script above
- One live test: ask the running system "where is David from" and confirm the response is Camberwell/South London, NOT David Frum/Canada

---

## BUILDER RESULT

**Status:** DONE  
**Commit:** `c8fae01` (ID-035: personal David query guard at web search call site)  
**Date:** 2026-09-26  
**Evidence:** `engineering/evidence/ID/S1-ID035-WEB-SEARCH-GUARD_evidence.md`

Guard `_DAVID_PERSONAL_TERMS` added in `server.py:3157–3174`. All "where is David from/live/based/born/location" queries blocked from web search. Evidence filed.

**Board action:** Verify + close WO.
