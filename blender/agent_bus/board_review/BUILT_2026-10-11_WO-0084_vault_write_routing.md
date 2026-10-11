# Board Review — 0084: Vault Write Routing
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

"remember this: X" routes to vault_write. David said it and eLo said "I don't have that recorded."
Add patterns; eLo may say "Saved." or "Got it — I'll remember that." after a successful write.

---

## Implementation status at review time

All required patterns were already present in `runtime/router/intent_engine.py` at `vault_write`:

```python
("vault_write", [
    r"\bremember\s+(?:this|that)\b",
    r"\bsave\s+(?:this|that)\b",
    r"\bnote\s+(?:this|that|it|down)\b",
    r"\badd\s+(?:this|that)\s+to\s+(?:my\s+)?(?:vault|memory|notes?)\b",
    r"\bwrite\s+(?:this|that)\s+down\b",
    r"\bdon'?t\s+forget\b",
    r"\bkeep\s+(?:this|that)\b",
    r"\bmake\s+a\s+note\b",
])
```

**One bug found and fixed:** `memory` intent pattern at line 28 had
`r"\bremember\s+(?:when|what|that)\b"`, which captured "remember that" before
`vault_write` could see it. Fixed by narrowing to `r"\bremember\s+(?:when|what)\b"` —
"remember when/what" are unambiguously recall requests; "remember that" is a store request.

---

## Test — `tests/test_vault_write_routing.py`

New file. 13 parameterised cases, all green:

```
tests/test_vault_write_routing.py — 13 passed in 0.15s
```

Covered phrases:
- `remember this: I like coffee` → vault_write ✅
- `remember this` → vault_write ✅
- `remember that` → vault_write ✅ (fixed from `memory`)
- `don't forget my birthday` → vault_write ✅
- `dont forget this` → vault_write ✅
- `save this for later` → vault_write ✅
- `save that` → vault_write ✅
- `write that down` → vault_write ✅
- `write this down` → vault_write ✅
- `keep that` → vault_write ✅
- `keep this` → vault_write ✅
- `note this down` → vault_write ✅
- `note that` → vault_write ✅

---

## Known partial issue (not fixed here)

"make a note" (bare) routes to `utility_notes` because `utility_notes` is defined earlier in
the pattern list and has `r"\b(?:make|create|new|add)\s+(?:a\s+)?note\b"`. This is a
pre-existing ordering conflict. "make a note" can mean "open Apple Notes" or "store to vault" —
routing it to utility_notes is defensible. Fixing this requires a separate card or David L3
ruling on intent disambiguation.

---

## Regression check — 38/38 intent tests green

```
tests/test_recall_intent.py — 19 passed
tests/test_wo_intentions_001.py — 5 passed
tests/test_elo_intentions_001.py — 13 passed  
tests/test_wo072_intent_gatekeeper.py — 1 passed
```

---

## Board decisions required

1. **"make a note"** intent: currently utility_notes. If vault_write is required, a separate
   card should narrow the `utility_notes` pattern or adjust ordering. No action taken here.

*Builder 1 · 2026-10-11*
