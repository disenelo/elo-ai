# WO-CAP-KEY-020 — Know when to play — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `set a reminder for tomorrow to check the servo calibration` | `Alright, got it. Tomorrow at 09:59, I'll make sure to check the servo calibration.` | reflect | ⚠️ PARTIAL — acknowledges; invents specific time '09:59' not requested; system confirmation absent |

**Root cause:** Reminder verbally acknowledged; specific time hallucinated (09:59 not requested); no confirmation that reminder was written to macOS notification system. This was a tool-use test filed under KEY-020 (know when to play) — mismatch.

**Blocking gaps:**
- Time hallucination in reminder
- System confirmation absent
- Test doesn't match WO-020 spec (play behavior)

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
