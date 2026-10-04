# WO-112 CHOOSE — Result Card

**Builder:** Builder 1  
**Date:** 2026-10-04  
**Status:** COMPLETE — all ATs pass; evidence attached

---

## What was built / verified

`_conversation_action` (runtime/executive.py:236) already returns the full candidate set schema:
```
{action, confidence, reason, candidates: [{action, utility}, ...]}
```
Every branch sets confidence explicitly. `_score_candidates()` runs before the first return.

Decision journaling:
- `self/decision_journal.py:record()` extracts `alternatives_rejected` from candidates on every turn
- `record_failure(action, condition)` drops `action_reliability.json` by 0.15 per failure
- `_bypass_journal()` (server.py:316) traces pre-spine bypasses to the journal
- `journal_early_return()` (runtime/executive_candidates.py:144) available for bypass path callers

Tests: `python -m pytest tests/ -k "executive"` → **107 passed**

## ATs

- AT-1 ✅ "why did you jump" → journal entry with confidence=0.95, alternatives_rejected=[{action:build, utility:0.65}]
- AT-2 ✅ No branch emits confidence=null; every path sets float 0.5–0.95
- AT-3 ✅ `record_failure('test_action', ...)` → action_reliability.json `{"test_action": 0.85}`

## Evidence

`engineering/evidence/WO-112/WO-112_CHOOSE_evidence.md` — live journal entry + reliability write.
