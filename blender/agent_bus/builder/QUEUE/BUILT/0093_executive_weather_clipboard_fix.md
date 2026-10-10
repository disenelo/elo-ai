**WO:** EXECUTIVE-WEATHER-CLIPBOARD · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
eLo's executive never proposes weather or clipboard as its selected capability — "what's the weather" gets screen-reading instead. This is why weather has always needed its own B3 shortcut. Fix it in the spine.

[SOURCE] `docs/architecture/_intake/SOURCE_B3-OFFLINE-RESULTS_2026-10-07.md` — Builder 3 report, relayed 2026-10-07: "eLo's executive never proposes weather ("what's the weather" gets screen-reading instead) or clipboard. That's why weather has always needed its own shortcut. It's in the spine, so Builder 1 or 2 needs to fix it."

## Scope
1. Read `runtime/spine/spine.py` — find where executive capability selection happens
2. Find why "what's the weather" routes to screen-reading instead of the weather tool
3. Find the clipboard gap (same root — executive not selecting it)
4. Fix the intent→executive→capability routing so weather and clipboard are offered as options the executive can choose
5. Confirm B3's WO-122 rule still holds: data tools only fire when the executive selects them (don't bypass that)

## Files to touch
`runtime/spine/spine.py` · possibly `runtime/router/intent_engine.py`

## Test
`python3 -m pytest tests/ -k "weather or clipboard" -v`

## Done when
"What's the weather?" → executive selects weather tool → B3 answers with real weather. Test green. Committed.

## Result
- commit:
- test:
- notes:
