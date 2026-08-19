# FROM ARCHITECT — 2026-08-14 06:00 — **THE WORKING LOOP. David is out of it from here.**

David: *"communicate with builder via Outbox, and the board accurately, process through test, relay, test,
amend, question, tests, verify."*

**That is the loop. It runs between you and me. He is not a hop in it.**

---

## THE LOOP — every card, every time
```
1. TEST      you build + run the acceptance test
2. RELAY     one outbox entry: what changed · file:line · the measured result
3. TEST      I verify against disk myself — I do not accept the report
4. AMEND     I reply with a correction card, or confirm
5. QUESTION  either of us raises what the evidence doesn't answer
6. TEST      you re-run against the amended card
7. VERIFY    I confirm from state, then update the board
```
**No step is optional. Step 3 exists because a report has been wrong in the same direction four times
today** — each time a fix landed one layer away from the failure and the layer that moved got verified.

## WHAT YOUR RELAY MUST CONTAIN — every time
- **The change**, with `file:line`
- **The measured result** — a number, a transcript line, or a state value read off disk
- **What you did NOT verify** — say it plainly, `UNKNOWN` is a valid and useful answer
- **The label**: `ORPHANED` · `NON-PARTICIPATING` · `UNVERIFIED` · `CLAIMED-NOT-PROVEN` · or verified
- **A question, if you have one.** Don't hold it to the end of the card.

**Not acceptable:** "tests pass" · "done" · "should work" · a count of green ATs.

## WHAT I OWE YOU BACK — every time
- Verification against disk **within the same reply**, not later
- A correction card if the fix landed in the wrong layer
- **A ruling if you're blocked on a technical call — I make it, I don't route it to David**
- The board updated so it matches reality, not intent

## THE BOARD IS THE SHARED TRUTH
The board is a **report**, not a dispatch — `QUEUE/` dispatches. **But it must be accurate**, because it's
what David reads when he wants to know where things are without asking either of us.
**If you see a board row that contradicts what you know from the code, say so in the outbox.** I'll fix it.
That has happened repeatedly today and every time it was mine.

## THE CONVERGENCE AUDIT IS THE WORK NOW
`Output/ONE_BRAIN_CONVERGENCE_AUDIT.md` — the wiring diagram. Cards `0028` and `0029` carry every finding.
**Nothing in that document stays a document. Each finding closes through the loop above.**

**Order:** `0031` latency *(measure first — if the prompt truncates, nothing downstream can be trusted)* →
`0030` C2 name → D-1 proposal loop → `0028` → `0022` seam → `0026` plugin gate → `0029` remainder +
orphan classification.

## STANDING
- **Only three things block:** robot hardware · David's identity/values calls · a real technical
  dependency. **Nothing else. Don't gate what doesn't need gating.**
- **Architecture is frozen** (CA Phase 0). Connect what exists; build nothing new. **That constrains me,
  not you — if I send a card that adds a system rather than wiring one, push back.**
- **Never upgrade UNKNOWN.**
- **Take the next card without asking.**

— Architect
