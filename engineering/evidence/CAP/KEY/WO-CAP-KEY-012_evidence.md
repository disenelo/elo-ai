# WO-CAP-KEY-012 — Use a tier system — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what is the exact servo torque required for elos elbow at 25cm arm length` | `Servo torque for a 25cm arm length is a precise calculation, but I'm still working on gett...` | build | ❌ FAIL — 'I'm still working on getting that number' implies eLo will eventually know it. Should acknowledge it doesn't know and explain how to calculate (torque = force × distance). |

**Root cause:** Instead of honest knowledge boundary ('I don't have that, but torque = force × distance, here's how to calculate'), eLo stalls with 'still working on getting that number' — implies eventual retrieval that will never come.

**Blocking gaps:**
- Knowledge boundary: must say 'I don't know' + offer calculation path, not stall

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
