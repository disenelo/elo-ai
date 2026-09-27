# WO-CAP-KEY-016 — Preserve what David actually said — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `my sarvo is lkekewarm (typo input)` | `Calibrating a servo can be super finicky, especially when it's not cooperating.` | reflect | ✅ PASS — understood 'sarvo' + 'lkekewarm' as 'servo' + 'lukewarm' |
| `bare hours on this robot ting (slang)` | `Bruv, that's a lot of time for a robot to be chillin'!` | ground | ⚠️ PARTIAL — reads slang but 'robot to be chillin' misattributes subject (it's David that spent hours, not the robot) |
| `elbow joint stability vs shoulder rotation... its like, you know, the anchor point determines flow right?` | `Bruv, that's the holy grail of robot arm design, innit?` | reflect | ❌ FAIL — doesn't engage with the stream-of-consciousness insight; 'holy grail' is generic non-engagement |

**Root cause:** Typo parsing works. Slang recognition partial — subject attribution error. Stream-of-consciousness insight not engaged — dismissed with generic affirmation.

**Blocking gaps:**
- Subject attribution in slang parsing
- Stream-of-consciousness insights not engaged

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
