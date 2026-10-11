# 10_WO-080_company_knowledge.md

**WO:** WO-080 · **Seat:** builder · **Priority:** P3 · **Reserved?** no

## Goal
Company Knowledge Interface — eLo answers about DISENELO from real company state, deeper than the current
"how's the company" briefing (WO-048, already live and David-confirmed).

## Scope — exactly this
- Implement per the authored WO-080 spec, extending the WO-048 path — do NOT build a parallel company answerer.
- Grounded in `company_state.json` + the board; **links to real work**, never invented ones (WO-076 fidelity rule).
- Honest "I don't have that" when data is missing.
- Note: the Kickstarter/sharing track is PARKED (eLo is David's personal tool now), so this serves David's own
  view of his company — not an external audience.

## Files likely touched
`company_runtime/company_memory.py` · `company_runtime/company_graph.py` · the WO-048 briefing path

## Test (without David)
Assert answers derive from live company state and vary with it; assert links resolve to real artifacts;
assert missing data yields an honest gap, not a fabrication.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
Spec: `engineering/work_orders/WO-080_Company_Knowledge_Interface.md`

## Result
- commit: 3640d8c
- test: 5/5 AT (active-WO filter, state variance, permitted gate + L3 wall, honest gap, wiring)
