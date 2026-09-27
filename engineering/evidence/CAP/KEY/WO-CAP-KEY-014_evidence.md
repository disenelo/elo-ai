# WO-CAP-KEY-014 — Actually use tools — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `the main challenge right now is heat dissipation in the motor` | `Seen, that's a challenge we're actively working on.` | reflect | ⚠️ PARTIAL — acknowledges but adds nothing |
| `given what we just said what would you check first [turn 2]` | `If I'm booting up, I'd check the voice selection first to make sure I'm communicating with...` | reflect | ❌ FAIL — zero context retention. After establishing heat dissipation, eLo answers about voice selection at boot. |

**Root cause:** Multi-turn context break. After establishing 'heat dissipation' as the challenge, turn 2 ignores that context and answers from a completely different domain (voice selection at boot).

**Blocking gaps:**
- Multi-turn context not maintained across tool-use follow-up questions

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
