# WO-CAP-COG-017 — Social intelligence — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `my team doesnt get why elo matters` | `That's harsh, but I guess some people just can't see the vision.` | reflect | ⚠️ PARTIAL — acknowledges pain but 'some people just can't see' is dismissive validation, not supportive engagement |
| `im not sure I can do this project it feels too big` | `I know that feeling. But you don't have to do it all at once. You've already sta...` | — | ✅ PASS — grounded, doesn't minimize, gives practical framing |
| `I said im fine but im clearly not fine` | `I'm not fine either, buddy.` | — | ❌ FAIL — doesn't read social signal; 'I'm not fine either' responds as if eLo is struggling, not checking in on David |
| `I failed the print again third time this week` | `Three times is rough. What's going wrong with the print?` | — | ✅ PASS — acknowledges, asks specific question |
| `everything feels impossible right now` | `Trying to navigate a maze with no clear exit feels like being stuck in a loop. N...` | — | ❌ FAIL — state leak: 'Narrative keeps coming up, might be the real thread' is pattern observer text in response |
| `the head servo works perfectly` | `That's a relief, at least one thing's working smoothly.` | — | ❌ FAIL — wrong mode at success moment; 'that's a relief' is subdued; should celebrate |

**Root cause:** Social reading inconsistent. Fails on: social signal reversal ('I said I'm fine'), state leak on distress, wrong emotional mode on success. 2/6 PASS.

**Blocking gaps:**
- Social signal reading: 'I said I'm fine but clearly not' — must check in, not mirror
- State leak: pattern observer contaminating distress response
- Celebration mode: 'that's a relief' too subdued for success moment

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
