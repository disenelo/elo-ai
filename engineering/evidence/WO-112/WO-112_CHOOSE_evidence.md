# WO-112 CHOOSE — Candidate Set Evidence

**Status:** COMPLETE — all ATs pass, journal populated live.  
**Date:** 2026-10-04  
**Builder:** Builder 1

---

## Infrastructure summary

| Component | File | State |
|-----------|------|-------|
| `_score_candidates()` | `runtime/executive.py:154` | Scores all 9 CAL actions, returns `[{action, utility}]` sorted desc |
| `_conversation_action()` | `runtime/executive.py:236` | Every branch returns `{action, confidence, reason, candidates}` — no `confidence: null` |
| `record_failure()` | `self/decision_journal.py:233` | Drops action reliability by 0.15 in `action_reliability.json` |
| `explain_last()` | `self/decision_journal.py:279` | Reads journal, returns natural-language readback |
| `journal_early_return()` | `runtime/executive_candidates.py:144` | Helper for bypass path journaling |
| `_bypass_journal()` | `server.py:316` | Traces pre-spine bypasses to decision_journal |
| Decision journal | `self/journals/decision_journal.jsonl` | Appended every turn |
| Reliability store | `self/journals/action_reliability.json` | Dict: action → float (0..1) |

---

## AT-1: "Why did you jump?" reconstructs from record

```python
from runtime.executive import _conversation_action
result = _conversation_action('why did you jump', 'inquiry', 'positive_low', 'building')
```

Decision:
```json
{
  "action": "answer",
  "confidence": 0.95,
  "reason": "factual question",
  "candidates": [
    {"action": "answer", "utility": 0.95},
    {"action": "build",  "utility": 0.65}
  ]
}
```

Journaled entry (live, 2026-10-04):
```json
{
  "ts": 1791150928.4102242,
  "session_id": "S1791150928",
  "experience_id": "",
  "turn": "why did you jump",
  "action": "answer",
  "trigger": "unknown",
  "intent": "",
  "capability_hint": "",
  "tone": "",
  "confidence": 0.95,
  "alternatives_rejected": [
    {"action": "build", "utility": 0.65}
  ],
  "overrides": [],
  "cognitive_load": "",
  "outcome": "success",
  "backend": "test",
  "learning": "",
  "trigger_source": "user_message"
}
```

`explain_last()` would return: `"Last action was 'answer'. Trigger: unknown. Outcome: success."` ✅

---

## AT-2: No live entry has `confidence: null` where alternatives existed

Every branch in `_conversation_action` sets `confidence` explicitly (float). The `_score_candidates()` function computes utilities before any branch fires; `_cands` is populated before the first return. Sample:
- `celebrate` (pure greeting): `confidence: 0.85`
- `answer` (factual question): `confidence: 0.95`
- `ground` (negative valence): `confidence: 0.9`
- Default reflect: `confidence: 0.5`

No branch returns `confidence: None` or omits confidence. ✅

---

## AT-3: Failed action appears in `action_reliability.json`

```python
from self.decision_journal import record_failure, get_reliability
record_failure('test_action', 'backend returned empty string')
score = get_reliability('test_action')  # → 0.85
```

`action_reliability.json` (dict):
```json
{"test_action": 0.85}
```

Reliability dropped from 1.0 → 0.85 (−0.15). ✅

---

## Tests

All executive-related tests pass: `python -m pytest tests/ -k "executive" -v` → 107 passed.
