# FROM_BUILDER — CCM FULL DIMS: all non-null dims reach prompt
**Status:** DONE  
**Date:** 2026-09-11  
**Board:** START_HERE.md P0 — CCM FULL DIMS  
**Commit:** 2434d90 (removed `[:4]` slice)

---

## What was wrong

`runtime/prompt_builder.py` had:
```python
# BEFORE (broken):
_ccm_items = [f"{k}: {v}" for k, v in list(_ccm.items())[:4] if v]
```
Only first 4 CCM dims injected. `creative_philosophy` (dim 12), `creator_matrix` (dim 27), `street_language`, etc. never reached the prompt.

## Fix (commit 2434d90)

```python
# AFTER (fixed):
_ccm_items = [f"{k}: {v}" for k, v in _ccm.items() if v not in (None, 0.0, [], {}, "") and v is not False]
```
All non-null dims inject. Null-guarding also improved (was just `if v`, now excludes 0.0/empty).

---

## Expressed proof (real server, 2026-09-11)

**Input:** "i keep starting creative projects and never finishing them"

**CCM dims detected (non-null):**
```
intent: conversation
relationship: creator
creative_philosophy: present
conversation_rhythm: short
vocabulary_preferences: ['street']
response_pacing: normal
social_expectations: greeting
creator_matrix: present
Total: 8 dims → all 8 inject into prompt
```

**Before fix:** only `intent`, `relationship`, `creative_philosophy`, `conversation_rhythm` would have reached the prompt (first 4 in dict order).  
**After fix:** all 8 inject.

`creative_philosophy: present` → "Shared philosophy resonant: The creative process doesn't finish..." directive fires ✅  
`creator_matrix: present` → "Creator principles active: Keep creating..." directive fires ✅

---

## Caller / trigger / observable / disconnection check

- **Caller:** `runtime/prompt_builder.py:608` — `_ccm = exec_decision.get("ccm_context") or {}`
- **Trigger:** Any turn where CCM enricher returns non-null dims
- **Observable:** "Context enrichment: ..." directive line in prompt; creative_philosophy/creator_matrix extra directives visible in expressed turns
- **Disconnection check:** Re-add `[:4]` slice → `creative_philosophy` and dims 5+ disappear from directive line

— Builder · 2026-09-11
