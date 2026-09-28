# FROM BUILDER → BOARD — WO-WKG-LABEL-LEAK-001: WKG Label Leak
**Date:** 2026-09-15
**WO:** Dispatched from FROM_BUILDER_REAUDIT_EXPRESSED_WOS_result.md
**Authority:** Re-audit finding — 2026-09-12

---

## Prior failure

"I keep returning to world_knowledge." — raw WKG entity label `world_knowledge` appearing in expressed response. The WKG context injection was echoing the system prompt block label verbatim, causing the LLM to reproduce it in the response.

---

## Fix already applied

`WO-WORLD-KNOWLEDGE-LEAK preventative` (2026-09-12): Added `"world_knowledge"` and `"i keep returning to world"` to `_PACK_CONTAMINATED` in `memory/memory_pack_builder.py`. These patterns prevent recycling of the `[WORLD KNOWLEDGE]` system prompt block label back into context.

---

## Re-run evidence (2026-09-15)

**"i keep returning to this idea":**
```
Response: "That thought keeps looping, like a track you can't skip, innit? Let it ride, maybe it'll drop a fresh line when you least expect it."
Backend:  groq(emotional)
Label leak: False
```

**"something about elo planet feels familiar":**
```
Response: "Elo planet's pulse hits the same chord, feels like a place you've already walked, innit?"
Backend:  groq(emotional)
Label leak: False
```

No `world_knowledge` label in either response. ✓

---

## DoD

- [x] `world_knowledge` does not appear in expressed response ✓
- [x] `_PACK_CONTAMINATED` guard in memory_pack_builder.py covers this pattern ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-15*
