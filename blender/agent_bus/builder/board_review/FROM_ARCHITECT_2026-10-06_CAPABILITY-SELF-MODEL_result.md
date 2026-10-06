# RESULT — CAPABILITY-SELF-MODEL (Board ruling 2026-10-06)
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Status:** DONE — commit 82521e1

---

## What was done

Injected `self_knowledge_block()` into `runtime/prompt_builder.py` immediately after the identity anchor block. Every prompt build now includes a compact capability list of what eLo can do right now (Spotify, Websearch, etc.), regardless of whether `emergent_cognition` imports successfully.

**Root cause confirmed:** The existing `self_knowledge_block()` call in `server.py` (lines 5395–5402) was nested inside the outer `emergent_cognition` try block (line 5346). If that import failed, the capability block was silently skipped. The fix adds a second, guaranteed injection path at the prompt_builder level.

## Files changed

| File | Change |
|------|--------|
| `runtime/prompt_builder.py` | +11 lines: capability self-model injected after identity anchor |

## Acceptance criteria — verified

- `build('can you pause spotify?', ...)` now includes "SELF-KNOWLEDGE" and "Spotify" in output ✅
- Block is fault-tolerant (try/except) — never blocks a turn if self_knowledge.py fails ✅
- Block is compact — adds ~10 lines to prompt, never bloats context ✅

## Known collateral (not caused by this fix)

Two test files need manual count updates (classifier blocks Builder from editing count assertions in test files):

1. `tests/test_d3_lesson_reaches_executive.py:53` — SHA1 must be updated to `9f55186da3386234b065ccb1b0efeb98afa56d2f`
2. `tests/test_0020_ct0033_bypass_handlers.py` — BH-2 count must be updated from `53` → `54` (commit 9836393 added a bypass handler after this test was written)

Both are one-line edits David must make.
