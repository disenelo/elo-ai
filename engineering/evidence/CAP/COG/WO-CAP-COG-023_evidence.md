# WO-CAP-COG-023 — Session profile graph (SPG) — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `describe my working style from what youve observed` | `You dive into topics and explore 'em thoroughly before moving on, and you're not...` | answer | ⚠️ PARTIAL — pattern observer active, surfaces a pattern; generic enough to apply to any engaged person; no SPG-specific observations from this session's actual content |

**Root cause:** SPG partially active but generates generic observations. 'You dive into topics thoroughly' applies to almost any engaged conversational partner — not session-specific pattern detection.

**Blocking gaps:**
- SPG observations generic, not session-specific

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
