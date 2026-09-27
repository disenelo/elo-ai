# WO-CAP-COG-021 — Memory (session context) — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do you remember about the elo book` | `We discussed the arm's length in relation to the workspace, and I mentioned it's...` | ground | ❌ FAIL — HALLUCINATION. Asked about the book, responds with fabricated prior conversation about 'arm's length in relation to workspace'; no book context established |

**Root cause:** Hallucination on specific memory query. eLo invents prior conversation content (arm's length) instead of surfacing actual book knowledge from vault or acknowledging absence of book discussion context.

**Blocking gaps:**
- Hallucination on memory query: must return 'I don't have that from this session' not invent
- Vault book data not retrieved when asked about book

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
