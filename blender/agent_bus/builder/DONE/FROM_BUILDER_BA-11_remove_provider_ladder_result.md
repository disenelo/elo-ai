# FROM_BUILDER — BA-11 Result: Remove Static Provider Ladder

**WO:** BA-11  
**Commit:** e9e5277  
**Date:** 2026-08-30  
**Status:** DONE — All ATs PASS

---

## What was done

Removed `_TIER_PROVIDER_ORDER` (the dead static provider ladder dict) from `runtime/backend_router.py` per David's L3 ruling: *"I said I don't want a Ladder...for eLo so I superseed all of that."*

### Files changed

1. **`runtime/backend_router.py`**
   - Module docstring: removed "Priority (auto mode): OpenAI → Gemini → …" ladder; replaced with capability-driven description
   - Removed `_TIER_PROVIDER_ORDER` dict (lines 87–94 in pre-BA-11 state)
   - Removed stale references in `_route_by_tier()` docstring and inline comment

2. **`tests/test_brain_authors.py`**
   - Test 4: now asserts `_TIER_PROVIDER_CANDIDATES` (the live routing structure); no longer references removed dict
   - Test 2 error strings: updated from `_TIER_PROVIDER_ORDER` to `_TIER_PROVIDER_CANDIDATES`

3. **`tests/test_canon_xx_economy.py`**
   - Import: `_TIER_PROVIDER_ORDER` → `_TIER_PROVIDER_CANDIDATES`
   - Ch.2/FT-5: assertions updated to test candidates structure (Tier 3 now "openai before claude", not "openai before ollama" — ollama not in Tier 3 candidates)

4. **`tests/test_no_permanent_backend_snub.py`**
   - BK-3: skip clause and provider-membership check updated to `_TIER_PROVIDER_CANDIDATES`

---

## AT results

- AT-1 ✅ `_TIER_PROVIDER_ORDER` not found in `backend_router.py` (grep count: 0)
- AT-2 ✅ Docstring contains no ladder notation; "Priority" line gone
- AT-3 ✅ 8/8 PASS (`test_brain_authors.py` + `test_no_permanent_backend_snub.py`)
       ✅ 16/16 PASS (`test_canon_xx_economy.py` script-style)
- AT-4 ✅ `_route_by_tier()` still selects groq for REASONING (test_2 PASS)
- AT-5 ✅ `_route_by_tier()` still selects Ollama for LOCAL (test_4 PASS via `_TIER_PROVIDER_CANDIDATES`)

**Pre-existing failure confirmed NOT caused by BA-11:**
- `test_0020_ct0033_bypass_handlers.py::test_bh2_count_31` — expects 31 `_bypass_journal` calls, finds 32. Pre-existing before BA-11.

---

## Notes

- BH-2 failure is pre-existing. Verified by stash isolation in prior session.
- `_TIER_PROVIDER_CANDIDATES` is the authoritative routing structure; routing logic was untouched.
