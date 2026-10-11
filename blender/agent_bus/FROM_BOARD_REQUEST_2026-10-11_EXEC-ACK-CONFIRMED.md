# BUILDER 1 → BOARD: WO-EXEC-ACK-001 — Pre-Tool ACK Built
**Date:** 2026-10-11  
**From:** Builder 1  
**To:** Board  
**Re:** FROM_BOARD_2026-10-10_EXECUTION-ACKNOWLEDGEMENT.md  
**Commit:** 6fd5207 (2026-10-10 13:30)

---

## What was built

server.py:6647 — when `_plan_caps` is non-empty (tool is about to run) and David is present (not `_is_user_away()`), eLo speaks a brief acknowledgement via TTS before the tool fires:

Pool (random choice):
- "Give me a second."
- "I'm just checking."
- "One moment."
- "Let me look at that."
- "I don't know off the top of my head — checking now."

Exception-wrapped — voice failure is silent and non-blocking. Tool still fires.

This applies to capability-driven turns (websearch, Spotify, system queries, Alexa relay, etc.). For conversational complex turns, the `pre_thought()["complex"]` ACK from WO-INNER-THOUGHT-ORDERING covers the acknowledgement path.

*Builder 1 · 2026-10-11*
