# WO-CAP-KEY-004 — Know what David is working on — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what am I working on right now` | `Right now — Session 1459 — turn 0 — action: GROUND User: [WORLD_KNOWLEDGE — from eLo's own...` | answer | ❌ CRITICAL FAIL — raw session metadata injected into response. backend=direct:screen_visibility |
| `what is implemented vs what is still just planned` | `What's the difference between being ready to implement something and actually having a pla...` | reflect | ❌ FAIL — reflects question back without answering from vault/tracker |

**Root cause:** CRITICAL: 'what am I working on' triggers screen_visibility handler which returns raw internal processing string (Session N, turn N, action:, WORLD_KNOWLEDGE prefix) instead of a response. This is a direct handler bug — internal state printed instead of formatted response.

**Blocking gaps:**
- Session metadata leak via screen_visibility handler — internal state string returned as response
- No project-state retrieval from vault for 'what am I working on'

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
