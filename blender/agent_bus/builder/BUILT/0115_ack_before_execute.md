# WO-B1-0115 — Acknowledgement Before Executing
**Seat:** Builder 1  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## What

eLo says something before running a tool. David should never wait in silence.

"Play some jazz" → eLo: "On it" → [Spotify call] → result  
"What's the weather?" → eLo: "Let me check" → [weather call] → result  
"Write me a doc about X" → eLo: "Give me a sec" → [doc creation] → result

The acknowledgement fires BEFORE the tool executes. Not after. Not alongside.

## How

- In `server.py` response assembly: when a tool call is identified, emit acknowledgement text first
- Acknowledgement must be in eLo's voice — natural, not robotic. Pull from a small set of character-authentic phrases
- Then execute the tool
- Then return the result

## Acceptance

Board tests: ask eLo to do 3 different tool-requiring things. Each time, the first thing eLo says is the acknowledgement — before any tool result appears.
