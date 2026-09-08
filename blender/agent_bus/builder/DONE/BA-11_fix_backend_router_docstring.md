# BA-11 — Fix `backend_router.py` Docstring (CF-01)

**Owner:** Builder
**Priority:** P0 (minor — documentation lie, low risk)
**Status:** DISPATCHED 2026-08-30
**Source:** SOURCE_ALIGNMENT_REGISTER_2026-08-30.md CF-01 — docstring says "Priority: OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock" which implies static ladder. Routing logic IS capability-driven. Documentation lies. [VERIFIED — register]
**Ladder ruling:** David L3 2026-08-30 — "I said I don't want a Ladder...for eLo so I superseed all of that." [DAVID]

---

## Scope

Two changes only:

### A. Fix the module docstring

Replace the ladder description at the top of `backend_router.py` with accurate description:
- Routing is capability-driven: `_TIER_CAPABILITY` + `_TIER_PROVIDER_CANDIDATES` + `_COST_RANK`
- There is no static provider order
- Provider selection is determined by what the provider supports + cost rank

### B. Assess `_TIER_PROVIDER_ORDER`

CF-02: `_TIER_PROVIDER_ORDER` is preserved "for test compat." Grep all tests that reference it. If tests can be updated to not depend on it, remove it. If removal would break tests with significant rework, flag for next pass — do not delete without checking.

## VERIFY FIRST

```bash
grep -n "_TIER_PROVIDER_ORDER" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/backend_router.py
grep -rn "_TIER_PROVIDER_ORDER" /sessions/eager-inspiring-hopper/mnt/elo-ai/tests/
```

## Definition of Done

Module docstring accurately describes capability-driven routing. No reference to static ladder order in any docstring or comment. `_TIER_PROVIDER_ORDER` either removed (if tests survive) or flagged in a comment as test-compat-only pending removal.

## Lane

Builder only. Pure documentation fix + possible dead code removal. No routing logic changes.
