# FROM BUILDER — WO-FIX-ALL-84-26 — FIX-2, FIX-3, FIX-4 — APPLIED

**Date:** 2026-09-11
**Status:** CODE APPLIED — real server evidence pending (restart required)

---

## FIX-2 — EMPTY RESPONSES (turns caf30870, d8b30eaf)

**Root cause found:** `runtime/response_gate.py:717-720` — when `_is_repetition(candidate)` fires (exact match within last 3 responses), returns `""`. Then `server.py:5604-5607` (D-6 guard) detected `last_was_repetition_suppression() == True` and intentionally left response empty ("Do not send fallback; leave response empty so nothing is spoken").

**Fix applied:** `server.py` D-6 guard, lines 5604-5607 → now applies a variation fallback even when repetition was suppressed:
```python
if _was_dedup:
    _sil.warning("D-6: repetition suppressed — applying variation fallback for raw=%r", ...)
    response = "Still here. That one came back the same — say it again?"
    _bubbles = [response]
```

**Evidence required:** Run "yo what you been up to" and "are you listening to me" on real server after restart — both must return non-empty eLo response.

---

## FIX-3 — CAP_CALENDAR ROUTING / TIMEOUT

**Root cause found:** `tools/calendar_agent.py:_run()` — osascript timeout at 8.0 seconds was reached (confirmed via `dispatch_calendar("today")` test — returns "error: Command timed out after 8.0 seconds"). The error string IS passed to the LLM as context but the LLM was ignoring it and pulling from memory.

**Secondary cause:** WKG contaminated entity `statement:i feel good today` (removed in prior session) was likely part of the memory content returned for "today" queries — that cleanup may already address turn 07fbcc0a.

**Fix applied:** `tools/calendar_agent.py:_run()`:
- Timeout reduced: 8.0s → 4.0s
- TimeoutExpired now returns: `"Calendar app did not respond — no events loaded"` (clear, LLM-readable)
- Empty result returns: `"Calendar app returned no data"`
- Generic exception: `"Calendar unavailable: {type(e).__name__}"` (no raw subprocess dump)

**Evidence required:** "what's on today" on real server — must return either real calendar data OR eLo voice saying calendar didn't respond. Never a memory note.

---

## FIX-4 — OVERLOAD PROTOCOL NOT FIRING (turn 669f2282)

**Root cause found:** `runtime/prompt_builder.py:522-526` correctly injects "OVERLOAD MODE: Reduce to ONE line" into the executive_directive when `exec_decision.get("overload_protocol")` is True. But the 8b model ignores this directive and produces expanded prose.

**Fix applied:** `server.py` — post-LLM generation truncation, inserted after `_route_streaming`/`router_route` call and before routing trace write:
```python
# WO-FIX-ALL-84-26 FIX-4: overload protocol enforcement
if exec_decision and exec_decision.get("overload_protocol") and response and response.strip():
    import re as _ovl_re
    _ovl_m = _ovl_re.search(r'[.!?]', response)
    if _ovl_m:
        response = response[:_ovl_m.end()].strip()
```
The 8b model generates freely; this truncates to the first sentence deterministically. The overload thresholds in spine.py (`sig >= 0.90`, `tension > 0.80 AND agency < 0.30`, `threads >= 3`) remain unchanged.

**Evidence required:** Input "tell me everything about everything all at once" on real server — output must be one sentence maximum.

---

## Syntax checks

- `server.py`: `python3 -c "import server; print('OK')"` → OK
- `tools/calendar_agent.py`: `python3 -c "import tools.calendar_agent; print('OK')"` → OK

*Builder · 2026-09-11*
