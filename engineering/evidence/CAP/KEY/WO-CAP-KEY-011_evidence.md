# WO-CAP-KEY-011 — Use faculties as intelligence inputs — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `lets talk about the shoulder joint` | `Shoulder joint, ball-and-socket joint. Allows for a wide range of motion in the arm.` | build | ⚠️ PARTIAL — brief but correctly identifies subject |
| `what are the failure modes [turn 2, same topic]` | `Failure modes include system crashes, data corruption, voice misrecognition, and hardware ...` | reflect | ❌ FAIL — context break. After establishing 'shoulder joint', eLo answers about software failure modes (Groq, Claude). Complete context break. |

**Root cause:** Multi-turn context not maintained. Turn 2 does not reference the established 'shoulder joint' topic — answers from a different domain (software/AI failure modes).

**Blocking gaps:**
- Context not retained across consecutive turns on same topic

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
