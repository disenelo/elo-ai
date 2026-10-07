**WO:** B3-CLIPBOARD-001 · **Seat:** builder3 · **Priority:** P1
**Reserved?** no

## Goal (one line)
"What did I copy?" / "What's on my clipboard?" → eLo reads the clipboard and says it. Before: "I don't have that recorded."

## Scope — exactly this, nothing more
- Clipboard read is eLo's answer, not context for the LLM to override
- "what's on my clipboard" routes to clipboard (it routed to Spotify)
- WO-018 gate and WO-122 Executive plan honoured

## Files to touch
`tools/tool_router.py` · `runtime/router/intent_engine.py` (intent vocabulary)

## Test (must pass WITHOUT David)
`python3 tests/test_wo018_capability_gate.py` → 6/6 · `python3 tests/test_wo020_tool_routing.py` → 6/6 · intent suites (wo121 ch8, wo039 ×2, nav_003, rel001) green

## Done when
Implemented + test green + committed. Fill in Result + Live turn needed below. Move to BUILT/.

## Result (seat fills this in before moving to BUILT)
- commit: 7f32056 (clipboard read = direct answer) · f180010 (WO-018 gate) · 8db420e (defers to the Executive's plan) · 5b66bca (intent_engine: Spotify's "what's on" no longer catches "what's on my clipboard")
- test: listed above, all green. Executive candidates after the fix: "what did I copy" → [clipboard]; "what's on my clipboard" → [clipboard, vision] (was [spotify, clipboard, vision]); "what's on spotify" / "what's playing" / "what's on now" still → spotify.
- notes: Live real-server turn 2026-10-06 (clipboard planted, then restored): "what did I copy" → "You copied: “eLo demo clipboard 7734”" `direct:clipboard` (audit f614c216). Not yet seen by David in his chatlog.

## Live turn needed (seat fills this in — exact words)
> David copies any text, then says to eLo: "What did I copy?"
> eLo should respond: "You copied: “<that text>”"
