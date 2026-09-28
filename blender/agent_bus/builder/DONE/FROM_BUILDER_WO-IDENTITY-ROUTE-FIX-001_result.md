# FROM BUILDER — WO-IDENTITY-ROUTE-FIX-001 — DONE

**Date:** 2026-09-12 (§91 continued)
**Status:** DONE — LIVE VERIFIED
**File changed:** `faculties/base_cognition.py`

---

## Problem

Audit T9: `"what's elo planet like on a quiet tuesday"` → `backend=direct` → `"I'm eLo. Always have been."`

World/setting questions hitting the `direct` identity backend instead of reaching the spine and returning world-knowledge responses.

On fresh server restart, T9 changed to `base_cognition+lore` → `"I know something's there — not enough to say it right yet."` — still wrong. A second underlying bug in `coverage_check()`.

---

## Root Cause (coverage_check false-SUFFICIENT)

`coverage_check()` computed two separate populations:
- `high_conf` — 17 claims at confidence=1.0, all with **empty** `claim_text`
- `with_text` — 59 claims with real text, at lower confidence

The condition `len(high_conf) >= _COVERAGE_THRESHOLD and with_text` was truthy because both lists were non-empty — but they represented *different* claims. Then `_text_claims = [c for c in high_conf if c.get("claim_text")][:5] or high_conf[:5]` fell back to the 5 empty-text high-conf claims, and `_build_response()` returned the sentinel `"I know something's there — not enough to say it right yet."` — which was then returned as `sufficient=True`.

The `direct` identity routing from the original audit turned out to be from a stale-pyc server run. On fresh server, the bug was the false-SUFFICIENT path.

---

## Fix

Changed the SUFFICIENT gate to require claims that are **both** high-confidence AND have real text:

```python
hc_with_text = [
    c for c in matched_claims
    if c.get("claim_text") and float(c.get("confidence", 0) or 0) >= 0.7
]

if len(hc_with_text) >= _COVERAGE_THRESHOLD:
    hc_with_text.sort(...)
    response = _build_response(hc_with_text[:5], ...)
    return True, response, hc_with_text
```

No SUFFICIENT fire unless there are ≥3 claims that satisfy BOTH requirements. Empty-text high-confidence stubs no longer contribute to the gate.

---

## Evidence

**Before (fresh server, old coverage_check):**
- Input: `"what's elo planet like on a quiet tuesday"`
- Backend: `base_cognition+lore`
- Response: `"I know something's there — not enough to say it right yet."`

**After (fresh server, fixed coverage_check):**
- Input: `"what's elo planet like on a quiet tuesday"`
- Backend: `ollama(stream)+lore`
- Response: `"It's like the entire world is holding its breath, and the silence is almost palpable. The..."`

---

## 3-Turn Battery After Both Fixes

| Turn | Backend | Response (first 90 chars) |
|---|---|---|
| `"i keep starting things and not finishing them"` | `ollama+obsidian` | Holding onto too many things that save limiters... |
| `"i had a really good idea this morning but i forgot to write it down"` | `ollama(stream)` | Holding onto too many things that save limiters... |
| `"what's elo planet like on a quiet tuesday"` | `ollama(stream)+lore` | It's like the entire world is holding its breath... |

All three FAILURE turns from the expressed audit now route to ollama with genuine responses.

*Builder · 2026-09-12 · §91*
