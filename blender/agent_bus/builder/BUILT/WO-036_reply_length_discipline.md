# WO-036 — Reply Length Discipline BUILT
**Seat:** Builder 1  
**Priority:** P2  
**Date:** 2026-10-11  
**Status:** Already implemented in repo

## Verified

- `prompts/living_presence_spec.txt` contains BREVITY RULE + "Short inputs get short replies"
- Banned openers ("I notice you...", "I hear you...", "I see you...") in spec
- Reflexive mirroring in BANNED behaviours
- Style monitor in `server.py` reads last 2 replies, injects `[STYLE MONITOR]` note when triggered
- `server.py` syntax clean

## Test result

7/7 AT: `python3 tests/test_wo036_reply_length.py` — all pass.

*Builder 1 · 2026-10-11*
