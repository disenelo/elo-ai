# BA-11 — Remove Static Provider Ladder from backend_router.py

**Owner:** Builder
**Priority:** P0 — David L3 ruling 2026-08-30 (supersedes all previous)
**Status:** DISPATCHED 2026-08-30
**LANE:** Builder Python only. Targeted changes to `runtime/backend_router.py` only.
**FREEZE_V1_LOCK:** Not applicable — `backend_router.py` is not `executive.py`.

---

## David's ruling (verbatim, 2026-08-30)

> "I said I don't want a Ladder...for eLo so I superseed all of that"

There is no static provider priority ladder for eLo. The routing is capability-driven. The codebase must reflect this.

---

## What to do

### 1. Remove `_TIER_PROVIDER_ORDER`
The dict `_TIER_PROVIDER_ORDER` (preserved "for test compat") communicates the old ladder. Remove it.
If `test_brain_authors.py test 4` goes RED: fix the test to not depend on a static order. The test must pass without the dict.

### 2. Fix the module-level docstring
Current docstring reads (approximately):
> "Priority (auto mode): OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock"

Replace with accurate description of the capability-driven routing:
> "Routing (auto mode): Executive determines required capability; `_route_by_tier()` selects the provider that satisfies that capability from `_TIER_CAPABILITY` + `_TIER_PROVIDER_CANDIDATES`, ranked by `_COST_RANK`. No static provider priority ladder exists."

### 3. Do NOT touch routing logic
`_route_by_tier()`, `_TIER_CAPABILITY`, `_TIER_PROVIDER_CANDIDATES`, `_COST_RANK` — these are correct. Only removing the dead dict and fixing the docstring.

---

## Acceptance Tests
- AT-1: `_TIER_PROVIDER_ORDER` does not exist in `backend_router.py`
- AT-2: Docstring does not contain "Priority" or "OpenAI → Gemini" or any ladder notation
- AT-3: Full test suite passes (run `~/miniconda3/bin/python3 -m pytest` — ensure no RED from removal)
- AT-4: `_route_by_tier()` still selects correct provider for capability=REASONING (e.g. Groq/Cerebras)
- AT-5: `_route_by_tier()` still selects correct provider for capability=LOCAL (Ollama)

## VERIFY FIRST
Check whether `_TIER_PROVIDER_ORDER` is actually referenced anywhere in the codebase before deleting:
```
grep -r "_TIER_PROVIDER_ORDER" /path/to/elo-ai/
```
If only referenced in `backend_router.py` itself and one test, delete it and fix the test. If referenced elsewhere, remove each reference.

*Board — 2026-08-30*
