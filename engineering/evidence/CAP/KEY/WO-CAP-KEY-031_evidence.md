# WO-CAP-KEY-031 — Maintain continuity across sessions — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what is elo not allowed to be [from batch]` | `eLo. That's me.` | ground | ❌ FAIL — non-answer (tautology); should enumerate constraints: not an assistant, not a language model, not aggressive |

**Root cause:** NOTE: Test filed as KEY-031 in batch is a brand constraints test, not a cross-session continuity test. WO-031 spec requires: facts from a previous session are available in a new session without re-establishing them. The batch test is MISLABELED. Cross-session continuity not yet tested.

**Blocking gaps:**
- MISLABELED: test doesn't satisfy WO-031 acceptance criteria
- WO-031 needs: test in fresh session that session-0 vault facts are available

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
