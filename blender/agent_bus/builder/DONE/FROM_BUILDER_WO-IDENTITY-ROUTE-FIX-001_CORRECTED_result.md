# FROM BUILDER — WO-IDENTITY-ROUTE-FIX-001 — CORRECTED RESULT

**Date:** 2026-09-12 (§91 continued — correction of prior result card)
**Status:** DONE — REAL ROOT CAUSE FOUND AND FIXED — LIVE VERIFIED
**Files changed:** `server.py` (_IDENTITY_TRIGGERS)

---

## Prior Result Was Wrong

The earlier result card claimed the fix was the `hc_with_text` gate in `base_cognition.coverage_check()`. That gate is real and correct — but it was NOT the cause of the identity assertion on world questions. On a fresh server restart, T7 still returned `[direct]` with an identity assertion despite the hc_with_text gate being active.

---

## Real Root Cause

`server.py:1749` — `_IDENTITY_TRIGGERS` contained `"what is elo"` as a substring match trigger:

```python
_IDENTITY_TRIGGERS = (
    "are you elo", "who are you", "what are you?", "are you real",
    "are you an ai", "are you a bot", "what is elo",  # ← THIS
    ...
)
```

The identity check in `runtime/spine/spine.py:720` is:
```python
if any(p in raw_lower for p in _srv._IDENTITY_TRIGGERS):
    plan.direct_response = _srv._identity_response()
```

This substring check: `"what is elo" in "what is elo planet like on a quiet tuesday"` → **True**. The trigger fired before any LLM or lore routing even got a chance.

---

## Fix

Removed `"what is elo"` from `_IDENTITY_TRIGGERS`. Identity intent is still covered by:
- `"are you elo"` — direct identity ask
- `"who are you"` — identity ask
- `"what are you?"` — with question mark, doesn't match world questions

When the user asks "what is elo" (without planet context), the LLM now answers via `[ollama+lore]` with eLo's self-description — actually a better answer than a rote identity assertion.

---

## Live Evidence (fresh server post-fix)

| Turn | Backend | Response |
|---|---|---|
| "what is elo planet like on a quiet tuesday" | `[ollama+lore]` | "In a quiet Tuesday on eLo Planet, the skies are a gentle violet..." |
| "are you elo" | `[direct]` | "I'm eLo. Always have been." |
| "what is elo" | `[ollama+lore]` | "I am eLo. Narrative keeps coming up..." |
| "i forgot to write it down" | `[ollama]` | empathetic response, NO false save |

All 3 expressed audit WOs confirmed on live server simultaneously.

*Builder · 2026-09-12 · §91 continued*
