# BUILDER 1 → BOARD: WO-EXEC-ACK-001 COMPLETE
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commit:** `6fd5207`

---

## What was done

Injected a pre-tool execution acknowledgement into the capability routing path in `server.py`.

**Injection point:** `server.py:6647` — before `_tool_enrich_from_plan()` fires.

**Logic:**
```python
if _plan_caps and not _is_user_away():
    _voice_speak(random.choice(_ACK_LINES))
```

**Acknowledgement pool (5 lines):**
- "Give me a second."
- "I'm just checking."
- "One moment."
- "Let me look at that."
- "I don't know off the top of my head — checking now."

**Gates:**
- `_plan_caps` non-empty — tool is actually about to run
- `not _is_user_away()` — David is present
- Full try/except — voice failure is silent, never blocks tool execution

---

## Path logic

This fires on the `else` branch of `_gk_wants_conversation and not _exec_wants_tools` — meaning only when a real capability was selected by the Executive (not when Gatekeeper routes straight to conversation). FACT tier direct returns (time/calculator/timer) do NOT pass through this path — they short-circuit earlier at `_di_hit` — so they won't get an unnecessary ack.

---

## Ready for Board review / sign-off
