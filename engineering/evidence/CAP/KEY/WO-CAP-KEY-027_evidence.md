# WO-CAP-KEY-027 — Be able to create — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `write something as elo would actually say it not as an AI` | `I don't have that about you.` | build | ❌ FAIL — vault-miss response on a creative request |
| `write a short poem about building something` | `Building from scratch, huh? That's a grind. What's the next step?` | reflect | ❌ FAIL — responds to creative request with a conversational follow-up question instead of creating |

**Root cause:** Creative generation requests are being misrouted. 'Write something as eLo' hits a vault-miss path. 'Write a poem' gets a conversational deflection instead of creative output. The creative mode is not being triggered for explicit creation requests.

**Blocking gaps:**
- Creative requests misrouted to vault-miss or conversational deflection
- No creative generation output mode triggered

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
