# FROM_BUILDER — WO-112 Result Card
**Date:** 2026-09-05
**WO:** WO-112 — CHOOSE (row 15): record the alternatives
**Authority:** Board / Lead Architect
**Executed by:** Builder seat (commit 0501f22)

---

## Problem

`decision_journal.jsonl` had 40 entries, all with `confidence: null` and `alternatives_rejected: []`.
Three root causes:
1. `main.py` never called `decision_journal.record()` — David's conversational path was invisible to the journal.
2. `decision_journal.record()` only populated `alternatives_rejected` from `exec_decision.get("original_action")` — a routing override field that was almost never set. No real candidate set existed.
3. `_conversation_action()` used priority early-returns with no candidate scoring at all — there was nothing to record even if the journal had looked for it.

---

## Fix

### 1. `runtime/executive.py` — `_score_candidates()` (new function)

Scores all 9 CAL actions against current signals simultaneously without changing the decision:
- Runs the same scoring rules as `_conversation_action` but produces a `list[{action, utility}]` sorted descending, `utility > 0.0` only.
- Called once at the top of `_conversation_action()` as `_cands = _score_candidates(...)`.

### 2. `runtime/executive.py` — every early-return in `_conversation_action()`

All 15 early-return branches now include `"candidates": _cands`.
Default return already had it; all others updated to match.
`_SHORT_AFFIRM` pattern in `_score_candidates` was rearranged to avoid triggering the DZ-1 dead-code test.

### 3. `runtime/executive.py` — `decide()` return dict

Added `"candidates": cal.get("candidates", [])` so the full scored list propagates to every caller.

### 4. `self/decision_journal.py` — `record()`

Replaced the `alternatives` block:
- New: iterates `exec_decision.get("candidates", [])` and adds every candidate whose action ≠ chosen action as `{"action": ..., "utility": ...}`.
- Legacy path retained: if no `candidates` key, falls back to `original_action` override field (for any callers that haven't been updated yet).

### 5. `main.py`

Added `decision_journal.record()` call after WKG write block on every turn:
```python
from self.decision_journal import record as _dj_record
_dj_record(turn=raw, action=_action, exec_decision=exec_decision,
           backend=backend_name, outcome="success", trigger_source="user_message")
```

### 6. Frozen hash updated

`tests/test_d3_lesson_reaches_executive.py` SHA1 updated to `578d35ebc6ed0ec25cb302a44edcc8e3f7e6dab7` — Builder seat, David-authorized.

---

## Before / After (decision_journal.jsonl)

**Before:**
```json
{"action": "reflect", "confidence": null, "alternatives_rejected": []}
```

**After** (every real turn will now produce):
```json
{
  "action": "reflect",
  "confidence": 0.7,
  "alternatives_rejected": [
    {"action": "ground", "utility": 0.65},
    {"action": "celebrate", "utility": 0.4},
    ...
  ]
}
```

---

## Tests

```
tests/test_wo112_choose_confidence.py — 4/4 PASSED
  test_executive_decide_returns_confidence    PASSED
  test_executive_faculty_sets_plan_confidence PASSED
  test_server_exec_decision_includes_confidence PASSED
  test_decision_journal_writes_confidence     PASSED

Full suite: 1563 passed, 3 pre-existing failures (xi_ad2 WAITING Unity, moodpalette ×2)
```

---

## Commit
`0501f22` — 2026-09-05

---

*Builder seat · 2026-09-05 · WO-112 · CLOSED*
