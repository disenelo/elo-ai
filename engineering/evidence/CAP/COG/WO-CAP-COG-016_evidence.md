# WO-CAP-COG-016 — Psychology and human behaviour — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `why do people connect so deeply with elo when they cant even see its eyes` | `They're invested in the character's journey, and the frustration is just a part ...` | answer | ⚠️ PARTIAL — addresses emotional investment ('invested in the character's journey'); doesn't give psychological mechanism; 'frustration is part of the story' seems context carry from prior turn |

**Root cause:** Psychological mechanism not provided. Response gives a narrative reframe ('frustration is part of the story') rather than a psychological explanation (projection, parasocial bond, movement-as-expression).

**Blocking gaps:**
- No psychological mechanism: needs projection theory, parasocial bond, or body-language-over-eyes explanation

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
