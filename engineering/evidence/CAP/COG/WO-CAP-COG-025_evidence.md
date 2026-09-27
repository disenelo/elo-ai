# WO-CAP-COG-025 — Learning from session — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `have you learned anything from talking with me` | `You dive into topics and explore 'em thoroughly before moving on, and you're not...` | reflect | ⚠️ PARTIAL — same SPG observation as COG-023; not session-specific learning; doesn't cite anything uniquely learned from this conversation |

**Root cause:** Pattern observation present but identical to COG-023 SPG response. Not distinguishing 'pattern observed' from 'something learned.' No specific correction or insight incorporation evident.

**Blocking gaps:**
- Learning not distinguishable from generic pattern observation

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
