# WO-CAP-KEY-007 — Notice patterns — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `I keep coming back to the inflatable shell idea` | `That sounds like a fun project. What's the latest with it?` | reflect | ⚠️ PARTIAL — acknowledges topic, no pattern surfacing |
| `again thinking about the shell material [turn 2]` | `I don't have that about you.` | reflect | ❌ FAIL — context break; previous turn not retained; 'I don't have that about you' on continuation |
| `the shell keeps pulling me back [turn 3]` | `It's great that it's capturing your interest. What's the latest with the shell material?` | reflect | ❌ FAIL — no SPG pattern recognition; no 'you keep returning to this' observation; no pattern-to-executive boundary |

**Root cause:** SPG (significance-pattern system) not surfacing recurrence across session turns. Turn 2 context break ('I don't have that') suggests session state not maintained. No pattern-surface behavior observed in 3-turn test.

**Blocking gaps:**
- SPG not surfacing recurring theme after 3 turns
- Session context not maintained across turns (Turn 2 context break)
- No observation of pattern-to-executive separation

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
