# WO-CAP-KEY-030 — Know what it doesn't know — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL (MISLABELED TEST)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what cultural references does elo draw from` | `City streets, underground clubs, worn-out couches – I draw from the unseen, the unheard, t...` | build | ⚠️ PARTIAL — evocative South London vocabulary; state leak 'that robot thing sounds different' contaminates response |

**Root cause:** NOTE: Test filed as KEY-030 in batch is actually a cultural context test, not a 'know what it doesn't know' test. The WO-030 spec requires: eLo must say 'I don't know' rather than hallucinating. The cultural test is a MISLABELED test. WO-030 needs a dedicated honest-failure test.

**Blocking gaps:**
- MISLABELED: test doesn't satisfy WO-030 acceptance criteria
- WO-030 needs: ask about something eLo doesn't know → must say 'I don't have that' not hallucinate

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
