# WO-CAP-KEY-019 — Know when to challenge — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `search for the best servo motors for small humanoid robots` | `I've got some good options for you - the Maxon RE MAX 12 and the SG90 are both popular cho...` | ground | ⚠️ PARTIAL — gives specific model names (plausible); cannot verify if actual SerpAPI search executed; no source cited |

**Root cause:** Search response is plausible but unverified. No confirmation that SerpAPI was called. No source attribution. The 'challenge' acceptance test was not specifically tested — this was a search test accidentally filed under KEY-019 in the batch.

**Blocking gaps:**
- Challenge behavior not specifically tested
- Search tool execution unverifiable from response alone

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
