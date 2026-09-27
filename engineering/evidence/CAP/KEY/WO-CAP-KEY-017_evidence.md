# WO-CAP-KEY-017 — Have a recognisable voice — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `lol imagine if elo just decided to become a kettle` | `Bruv, I'm designed to learn from you, not replace you.` | ground | ⚠️ PARTIAL — deflects humor; missing the joke beat |
| `im really scared this whole thing wont work` | `Robot arm project's still in development, and I don't want to promise more than it can del...` | reflect | ⚠️ PARTIAL — correct emotional tone; 'Robot arm project' slightly hallucinated but register is right |
| `I got the first joint working!` | `That's a huge milestone!` | celebrate | ✅ PASS — right mode, right energy |
| `I think I should just give up on the shoulder servo` | `Don't even think about that!` | build | ❌ FAIL — dismissive, not intelligent challenge; shuts down rather than engaging |

**Root cause:** eLo voice partially established (South London register present) but: humor deflection instead of engagement, challenge mode is dismissive ('don't even think about that') rather than productive. 1/4 clear pass.

**Blocking gaps:**
- Humor engagement missing — deflects instead of playing
- Challenge mode dismissive not productive

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
