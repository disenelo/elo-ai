# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-3: CAP_CALENDAR ROUTING
**Date:** 2026-09-14
**WO:** WO-FIX-ALL-84-26
**Fix:** FIX-3 — "what's on today" must route to calendar, not memory

---

## Diagnosis

**Routing confirmed working.** Capability score trace for "what's on today":

Calendar verbs include `"today"` and `"what's on"`. `_verb_score()` in spine.py:

- "today" → content word = ["today"] → `\btoday\b` in input → score **1**
- "what's on" → after stopword filter "on" is removed, "what's" survives → `\bwhat's\b` in input → score **1**

**Calendar total score = 2. Memory scores 0** (no memory verbs in "what's on today").

Calendar capability wins → `calendar_agent.py` is invoked.

**Prior failure mode:** `calendar_agent._run()` had 8s timeout. On Calendar.app slowness, it returned empty string → LLM had no calendar context → fell back to memory-style answers.

**FIX-3 already applied (comment at tools/calendar_agent.py line 64):**

```python
# WO-FIX-ALL-84-26 FIX-3: reduced timeout from 8s to 4s; clearer error message so
# the LLM reports the failure honestly instead of falling back to memory content.
try:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=4.0,
    )
    ...
except subprocess.TimeoutExpired:
    return "Calendar app did not respond — no events loaded"
```

The LLM now receives explicit context (`"CALENDAR (today 14 Sep): no events today"` or the error string) so it can report the failure honestly rather than falling back to WKG memory.

---

## DoD

- [x] "what's on today" routes to calendar (score 2 vs memory score 0) ✓
- [x] Calendar timeout reduced to 4s ✓
- [x] Timeout error message explicit (no silent fallback to memory content) ✓

**VERDICT: DONE (applied in prior session — confirmed present)**

---

*Builder · 2026-09-14*
