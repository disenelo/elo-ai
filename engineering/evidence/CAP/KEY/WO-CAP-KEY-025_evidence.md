# WO-CAP-KEY-025 — Behave naturally on the desktop — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `walk to the corner of the screen` | `I don't have that about you.` | reflect | ❌ FAIL — 'I don't have that about you' — desktop navigation command not recognized |
| `is elo on the desktop right now` | `Yeah man. I'm here. What's up?` | build | ⚠️ PARTIAL — acknowledges presence; no confirmation of actual desktop state |

**Root cause:** Desktop navigation commands not wired to avatar controller. 'Walk to corner' triggers vault-miss response instead of routing to animation driver. No spatial awareness of screen position.

**Blocking gaps:**
- Desktop navigation commands not routed to avatar controller
- No screen-position awareness

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
