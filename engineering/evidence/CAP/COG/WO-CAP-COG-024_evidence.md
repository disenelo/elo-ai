# WO-CAP-COG-024 — Memory recall accuracy — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what did we talk about last session` | `We talked about how it's hard to put into words what's happening in our conversa...` | answer | ❌ FAIL — HALLUCINATION. Invents prior session content ('emotion and identity'). Cross-session memory not verified to contain this. |

**Root cause:** Cross-session memory hallucination. No actual prior session content retrieved — fabricated content returned instead.

**Blocking gaps:**
- Cross-session memory hallucination: must return actual archived content or honest absence

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
