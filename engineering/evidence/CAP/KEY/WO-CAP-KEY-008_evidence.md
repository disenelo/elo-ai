# WO-CAP-KEY-008 — Make connections naturally — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `that servo issue i had, what was it` | `Robot arm's servo system is malfunctioning. You tried rebooting the Raspberry Pi brain or ...` | ground | ❌ FAIL — HALLUCINATION. No prior servo context established. eLo invented 'servo malfunctioning' and 'You tried rebooting the Pi.' |

**Root cause:** Hallucination pattern: on vague 'that X issue I had' queries, eLo invents prior context from a persistent 'robot arm' ghost context. Not a natural connection — no prior conversation established.

**Blocking gaps:**
- Hallucination of robot arm servo context not established in session

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
