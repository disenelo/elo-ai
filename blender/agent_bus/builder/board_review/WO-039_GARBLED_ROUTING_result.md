# WO-039 Garbled Routing — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — all ATs pass; already implemented in prior session

---

## What was verified

Both fixes from the WO spec are in place:

**Fix 1 — No prose coercion to command fragments:**
- `typo_engine.py`: `_COMMAND_WORDS` frozenset (`quit`, `close`, `kill`, `open`, `stop`, `exit`) requires exact match (distance=0) — prose word "built" (edit-distance 2 from "quit") is rejected by the guard.
- `typo_engine.py`: `_PROTECTED` set includes "built" — cannot be fuzzy-repaired at all.
- `typo_engine.py`: fuzzy matching disabled for inputs > 3 words — conversational sentences are never coerced.

**Fix 2 — System intent pattern anchored at sentence start:**
- `intent_engine.py`: pattern anchored `^(?:please\s+)?(?:quit|exit|close|kill|...)` — requires sentence-start position + real app/process target.
- Old unanchored `\b(?:quit|close|kill)\s+\w+\b` removed; mid-sentence command keyword can no longer fire system intent.

**Canned grammar content:** Not found in any server/router path — likely never present in this codebase (Architect's "leaked example content" reading was from a different session or model output, not a static content file).

## ATs

- AT-1 ✅ "built" is in `_PROTECTED` — never fuzzy-repaired to "quit"
- AT-2 ✅ `_fuzzy_match("built")` returns None (command-word guard)
- AT-3 ✅ system intent pattern anchored at sentence start (^ found in source)
- AT-4 ✅ "everything I built is related" → `intent='conversation'` (not system)
- AT-5 ✅ "quit Finder" → `intent=system` (real command still works)
- AT-6 ✅ py_compile clean on both files

**Run:** `python3 tests/test_wo039_garbled_routing.py` → **6/6 passed**

## Files

- `runtime/router/typo_engine.py` — `_COMMAND_WORDS` guard, `_PROTECTED`, fuzzy disable for long inputs
- `runtime/router/intent_engine.py` — sentence-start anchored system intent pattern
