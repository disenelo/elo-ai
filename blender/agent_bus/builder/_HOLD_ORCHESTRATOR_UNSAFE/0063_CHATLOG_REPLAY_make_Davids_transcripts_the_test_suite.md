# 0063 — Build the chatlog replay harness. David's transcripts ARE the test suite.

**WO:** WO-CHATLOG-REPLAY · **Seat:** builder · **Priority:** P1 (after `0061`, alongside `0060`)
**Reserved?** no
**LAYER:** `[DAVID INTENT]` 2026-08-20 — *"I use chatlogs as diagnostic tests"*
**STATE: AUTHORISED**

## Why this card exists
Every acceptance test in the repo was **green** while eLo answered David in a single grounding register for
seven turns, invented baseball, and repeated himself. **David found it by reading the log.**

> `[DAVID]` *"I use chatlogs as diagnostic tests"*

So a transcript he sends is **a failing test with no runner.** Build the runner.

## The work
1. A loader for `blender/agent_bus/_FIXTURES/chatlog_*.json` (first fixture already written — his
   2026-08-20 session, 10 turns, 7 marked FAIL with the reason at each turn).
2. A replay harness that drives each `user` turn through the **real** executive + prompt_builder + router and
   captures the reply, the chosen CAL action, valence, intent and backend.
3. Assertions from the fixture's own `pass_condition` and per-turn `verdict` fields — **the fixture is the
   spec; do not restate it in code.**
4. `--record` mode that writes a new fixture skeleton from a live session, so the next log David sends
   becomes a test in one command rather than an afternoon.

## 🔴 Two rules for this harness
- **Fixtures are EVIDENCE and are never edited to make a test pass.** If reality disagrees with the fixture,
  the code is wrong or David is re-consulted. Editing his transcript to go green is falsifying the record.
- **Assert on register and behaviour, not on exact strings.** eLo is generative; "did not route every turn to
  ground", "did not repeat itself", "answered the question" are the assertions. **A test demanding an exact
  sentence would freeze him, which is the opposite of the point.**

## Test
The harness's own first run must reproduce **7 failures** on the 2026-08-20 fixture. **If it reports fewer,
the harness is not wired to the real pipeline** — that is the disconnection check.

## Done when
Harness committed · fixture replays · 7/7 known failures reproduced · `--record` demonstrated on one session.

## Result
- commit:
- failures reproduced (expect 7):
- notes:
