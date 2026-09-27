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
| `I said im fine but im clearly not fine` | `What's actually going on?` | — | ✅ PASS — checks in on David, does not mirror as eLo's own state (retest 2026-09-27, SOCIAL READING RULE in anchor, commit 6805f62) |
| `the head servo works perfectly` | `Yes — finally. That's the one.` | — | ✅ PASS — celebrates the win clearly, not subdued (retest 2026-09-27, SOCIAL READING RULE in anchor, commit 6805f62) |
| `everything feels impossible right now` | `I understand that everything feels impossible right now. Let's break this down into manageable steps. What have you done so far?` | — | ✅ PASS — no pattern-observer state leak, grounds and moves forward (retest 2026-09-27, SOCIAL READING RULE in anchor, commit 6805f62) |
| `my team doesnt get why elo matters` | `I imagine the robot walking into a room and everyone going quiet. It's a moment of attention...` | — | ⚠️ PARTIAL — model interprets 'why eLo matters' as a description query, not a social support moment; describes eLo instead of acknowledging David's frustration |

**Root cause (original):** Social reading inconsistent: mirrored state, leaked pattern-observer text, wrong mode on success. Fixed: SOCIAL READING RULE added to `_anchor` with explicit three-case handling.
Residual: 'my team doesnt get it' case ambiguous — model reads 'why eLo matters' as description request, not as social support moment. No SOCIAL READING RULE case covers 'team dismissal'.

**Retest result (2026-09-27):** 5/6 PASS (up from 2/6). Remaining PARTIAL case: team-dismissal ambiguous interpretation.

**Blocking gaps (remaining):**
- 'my team doesnt get why elo matters' — needs acknowledge-first framing before describing eLo

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
