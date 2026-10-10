**WO:** VAULT-WRITE-ROUTING · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
"remember this: X" routes to vault_write. David said it and eLo said "I don't have that recorded."

## Scope
In `runtime/router/intent_engine.py` add vault_write intent patterns:
```python
r"\bremember (this|that)\b", r"\bdon'?t forget\b", r"\bsave that\b",
r"\bkeep that\b", r"\bmake a note\b", r"\bwrite that down\b"
```
After a successful vault_write, eLo may respond "Saved." or "Got it — I'll remember that." (Board ruling 2026-10-06). Must NOT say it if write failed.

## Files
`runtime/router/intent_engine.py`

## Test
`python3 tests/test_intent_accuracy.py` or equivalent — "remember this: X" → intent = vault_write. Must pass.

## Done when
implemented + test green + committed.

## Result
- commit:
- test:
- notes:
