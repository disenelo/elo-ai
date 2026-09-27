# WO-CAP-COG-025 — Learning from session — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `have you learned anything from talking with me` | `You dive into topics and explore 'em thoroughly before moving on, and you're not...` | reflect | ⚠️ PARTIAL — same SPG observation as COG-023; not session-specific learning; doesn't cite anything uniquely learned from this conversation |

**Root cause:** Pattern observation present but identical to COG-023 SPG response. Not distinguishing 'pattern observed' from 'something learned.' No specific correction or insight incorporation evident.

**Architectural blocker (2026-09-27):** Same root as COG-023 — no session-event feed. 'Learning from session' requires a diff between session-start state and session-end state: corrections accepted, pivots taken, new facts confirmed. Without a session-event log, the LLM has no material to distinguish 'learned this session' from 'generic pattern.' Fix requires same infrastructure as COG-023: session-event pipeline. Outside `backend_router.py` scope — Board WO required.

**Blocking gaps:**
- Learning not distinguishable from generic pattern observation — no session-event delta available
- Blocked on same infrastructure as COG-023: session-event logging → SPG observation layer

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
