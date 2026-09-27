# S1 FIXES B, C, D — run all three simultaneously (different files)

## FIX B — Answer completion (`runtime/prompt_builder.py`)
In the math/computation instruction block, add: "Always close with the final answer stated explicitly as a standalone sentence."
Commit. Done.

## FIX C — Pong channel leak guard (`server.py`)
Add guard: if assembled response is 8 characters or fewer AND matches any of: "Pong", "OK", "alive", "PONG" — log as routing error, do not return to user.
Commit. Done.

## FIX D — Abort catch on empty generation (`server.py`)
Add exception catch around the generation call. If it returns an empty string or raises an exception: log it, return "I ran into an issue — let me try again."
**FIX C must be committed before FIX D — both touch server.py.**
Commit. Done.

---

## BUILDER RESULT

**Status:** DONE — all three fixes confirmed in codebase  
**Date:** 2026-09-27

**Fix B** — `runtime/prompt_builder.py:964/975`  
Label: `FIX B — WO-CAP-COG-005: computation completion enforcement`  
Directive: "Always close with the final answer stated explicitly as a standalone sentence."

**Fix C** — `server.py:6496–6502`  
Label: `FIX C — WO-CAP-COG-005`  
Guard: if response ≤ 8 chars AND matches Pong/OK/alive/PONG → log routing error, do not return to user.

**Fix D** — `server.py:6528`  
Returns `"I ran into an issue — let me try again."` on empty generation or exception.

All three confirmed via grep against current codebase. No further action needed.

**Board action:** Close WO.
