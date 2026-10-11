# Board Review — WO-112: CHOOSE — Decision Record Has a Decision
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Every live journal entry had `confidence: null` and `alternatives_rejected: []`.
Root cause: `decision_journal.py:record()` read only from `exec_decision.get("candidates", [])`,
discarding the pre-populated `alternatives_rejected` set by the kernel hook.

FREEZE_V1_LOCK honoured — wrapper approach, `executive.py` untouched.

Fix: `self/decision_journal.py` — added `elif exec_decision.get("alternatives_rejected"):` branch.

---

## Commit

- `fcf2934` — `self/decision_journal.py` (+4 lines, 1 site)

---

## Evidence — real journal entry post-fix

```json
{
  "turn": "It is a full moon tonight",
  "action": "reflect",
  "confidence": 0.5,
  "alternatives_rejected": [
    {"rejected": "conversation", "reason": "lower utility: u=0.80 vs chosen u=0.65", "utility": 0.8},
    {"rejected": "connect",      "reason": "lower utility: u=0.60 vs chosen u=0.65", "utility": 0.6},
    {"rejected": "witness",      "reason": "lower utility: u=0.50 vs chosen u=0.65", "utility": 0.5}
  ],
  "backend": "ollama(stream)",
  "outcome": "spoke"
}
```

---

## Tests

```
python3 tests/test_wo112_choose_confidence.py + test_wo_fix_112_ambient.py
→ 8 passed  0 failed

python3 tests/test_wo082_decision_journal.py
→ 7 passed  0 failed
```

Additional verified status:
- ✅ `confidence` non-null in production
- ✅ Early-return branches journal via `_bypass_journal()` (card 0038)
- ✅ `action_reliability.json` exists and populated
- ✅ `record_failure` fires

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
