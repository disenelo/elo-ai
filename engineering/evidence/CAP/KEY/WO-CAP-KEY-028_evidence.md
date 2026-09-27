# WO-CAP-KEY-028 — Understand idea vs decision — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `I am thinking about switching to a different motor` | `What kind of motor are you considering, and what made you think about switching?` | reflect | ⚠️ PARTIAL — treats as exploration correctly (reflect mode); asks clarifying question |
| `I decided we are switching to a different motor` | `Hey, what kind of motor you looking at, and why you switch?` | reflect | ❌ FAIL — treats decision same as idea (reflect mode); should acknowledge decision as closed with 'Got it, locking that in' |

**Root cause:** eLo treats 'I am thinking about X' and 'I decided X' with the same mode and same follow-up question. No distinction between exploratory idea (keep open) and decision (close, confirm, record).

**Blocking gaps:**
- Decision not distinguished from idea — same mode/response for both
- Decision should trigger confirmation + journaling, not more questions

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
