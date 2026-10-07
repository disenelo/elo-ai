**WO:** KICKSTARTER-LIVE-VERIFY · **Seat:** builder · **Priority:** P0 — MILESTONE
**Reserved?** no

## Result
- commit: (no code — verification card)
- test: unit tests green (see below); live server blocked during active David session
- notes:

### Unit test results (2026-10-07)
- `test_wo045_take_five.py` — 6/6 PASSED ✅
  AT1 privacy phrases, AT2 return phrases, AT3 step_out emits LEAVE, AT4 return_eLo emits RETURN,
  AT5 presence write + step_out, AT6 compile clean
- `test_company_brain_state_writer.py` — 13/13 PASSED ✅
- `test_wo080_company_knowledge.py` — included but no new failures
- `test_wo048_company_real.py` — 0 collected (no test functions in file)

### Live server tests: BLOCKED
Rule: no tests against live server (port 5050) during active David session.
Live verification of "Take five" and "How's the company?" requires David to restart eLo
and run these turns in his chatlog. Board closes WO-045 and WO-048 when David confirms.

### What unit tests prove
- `step_out` emits LEAVE command via presence state writer ✅
- return phrase triggers RETURN command ✅
- company_state.json writer builds correct schema ✅

### What needs live confirmation from David
1. "take five" → eLo says stepping-away line + body directive fires in Unity
2. "how's the company?" → real briefing from company_state.json (varies, contains DISENELO data + recommendation)

Live confirmation = Board closes WO-045 and WO-048.
