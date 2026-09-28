# FROM BUILDER — Builder Voice Directness (FIX-3 completion)

**Date:** 2026-09-15
**WO:** P1 dispatch 2026-09-15 — "Builder voice directness (few-shot negative examples)"
**Authority:** Board dispatch 2026-09-15

---

## Problem

FIX-3 (WO-EXPRESSION-POLISH-BUNDLE-001) wired the `builder-voice` directive to fire on
build/connect/create action turns. T7 reaudit showed "building momentum" (passive, process-
describing) instead of "Make it real" energy (imperative, action-first).

The directive instructions were present but the LLM was satisfying them at a surface level —
adding momentum language rather than leading with a concrete step.

Root cause: no negative examples telling the model what NOT to do. The 8b model (llama3.1:8b)
tends to produce transition language ("building momentum", "let's explore") when asked to be
direct unless given explicit anti-patterns.

---

## Fix

`runtime/prompt_builder.py` — builder-voice directive string (line 573):

```python
# BEFORE:
"builder-voice: Make it real. Small steps become worlds. "
"Build before announcing. One thing, started now, beats ten things planned. "
"If it can be built in this turn, build it."

# AFTER:
"builder-voice: Make it real. Small steps become worlds. "
"Build before announcing. One thing, started now, beats ten things planned. "
"If it can be built in this turn, build it. "
"NOT: 'building momentum', 'let's explore possibilities', 'I can help with that'. "
"YES: start with the first concrete step. Lead with the action, not the preamble."
```

Two negative examples added:
- `"building momentum"` — the exact T7 failure pattern
- `"let's explore possibilities"` / `"I can help with that"` — class of passive openers

One positive instruction:
- `"Lead with the action, not the preamble."` — gives the model a concrete structural rule

---

## Evidence

Directive fires on `action in ("build", "connect", "create")` or `intent in ("creation", "planning", "making")`.
Pattern verified present in updated directive string:
- `"NOT: 'building momentum'"` ✓
- `"YES: start with the first concrete step"` ✓
- `"Lead with the action, not the preamble"` ✓

Live test requires a build-action turn — not testable without live server.
FIX-3 action classification path unchanged and confirmed correct in T7.

---

## DoD Assessment

| Item | Status |
|------|--------|
| Negative example for T7 failure pattern ("building momentum") added | ✅ SERVING |
| Negative class for passive openers ("let's explore", "I can help") added | ✅ SERVING |
| Positive structural rule ("Lead with the action, not the preamble") added | ✅ SERVING |
| Action classification gate unchanged (build/connect/create) | ✅ SERVING |
| Existing builder-voice instruction text preserved | ✅ SERVING |

**VERDICT: SERVING** (live verification needed on build-action turn)

---

*Builder · 2026-09-15*
