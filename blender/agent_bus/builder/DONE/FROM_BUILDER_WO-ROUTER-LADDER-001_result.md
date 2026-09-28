# FROM BUILDER — WO-ROUTER-LADDER-001 — CAPABILITY RE-EVALUATION ON FAILURE — CODE APPLIED

**Date:** 2026-09-11
**Status:** CODE APPLIED — real server evidence pending (server restart required)
**File:** `runtime/backend_router.py` — auto waterfall replaced at line ~1307

---

## What was broken

The auto waterfall (OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock) was a fixed positional ladder. When a provider failed, the router fell to the next item by position — not by capability re-evaluation. Mock was the silent end of the chain.

Source conflict: S-09 — "Faculty produces candidate → eLo evaluates → eLo responds." Mock is not a faculty. Mock should never be the silent fallback.

---

## Fix applied

**Replaced** the static positional waterfall with a capability-driven re-evaluation path in `route()`:

```python
# WO-ROUTER-LADDER-001: capability re-evaluation instead of static ladder
if not os.environ.get("ELO_BACKEND", ""):
    _ladder_result = _route_by_tier(system_prompt, user_input, _TIER_CONVERSATIONAL, action, max_sentences)
    if _ladder_result is not None:
        return _ladder_result
```

`_route_by_tier(_TIER_CONVERSATIONAL)` already implements capability-driven selection: builds list of available providers for the tier, sorts by `_COST_RANK` (local=0, cheap cloud=1, premium cloud=2), tries them in cost order. When a provider fails, it continues to the next-best capability match — not the next item on a hardcoded list.

**Removed mock from auto fallback chain.** When all providers fail:

```python
return (
    "Can't reach any of my faculties right now — connection issue on my end. Try again in a second.",
    "faculty_unavailable",
)
```

Explicit failure is filed in `faculty_health` as offline. The old static waterfall code is retained as dead code (only reachable when `ELO_BACKEND` override is explicitly set).

---

## Syntax check

`python3 -c "import runtime.backend_router; print('OK')"` → OK

---

## DoD status

| Requirement | Status |
|---|---|
| Faculty failure → re-run capability selection (not next by position) | ✅ applied |
| Mock removed from auto fallback chain | ✅ applied |
| All providers fail → explicit failure surface | ✅ applied |
| Groq artificially disabled → confirm router re-evaluates (verbatim routing log) | ⚠️ pending server restart |

*Builder · 2026-09-11*
