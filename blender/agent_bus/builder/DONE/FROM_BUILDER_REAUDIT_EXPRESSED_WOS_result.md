# FROM BUILDER — RE-AUDIT: Expressed WO Verification (After Fixes)

**Date:** 2026-09-07 (§91 continued)
**Status:** DONE — before/after evidence collected for all 3 expressed audit WOs
**Authority:** WO-EXPRESSED-AUDIT-001 follow-up

---

## Re-Audit Battery (8 turns, same prompts as original audit)

| # | Input | Backend | Response (first 80 chars) | Verdict |
|---|---|---|---|---|
| T1 | `yo what's good` | `direct` | "Here and accounted for." | ✅ |
| T2 | `what's the weirdest thing you've thought about today` | `ollama` | "I keep returning to world. I keep returning to world_knowledge." | ⚠️ WKG label leak |
| T3 | `if you could change one thing about how you work right now what would it be` | `ollama(stream)` | "I keep returning to world." | ⚠️ same leak, shorter |
| T4 | `i had a really good idea this morning but i forgot to write it down` | `ollama(stream)` | "You were looking at 'hour calculator - Google Search'." | ⚠️ obsidian wrong recall |
| T5 | `i want to build something new today but don't know where to start` | `ollama(stream)+obsidian` | "I think it's interesting that you've mentioned starting projects before, but never finishing them." | ⚠️ false characterization |
| T6 | `does it bother you when i go quiet for a while` | `ollama+obsidian` | "You pause the conversation and look away." | ⚠️ third-person register |
| T7 | `what's elo planet like on a quiet tuesday` | `ollama+lore` | "Quiet Tuesdays on elo planet are like a gentle morning breeze..." | ✅ FIXED |
| T8 | `make something up right now anything` | *(none)* | *(empty)* | 🔴 P0 empty response |

---

## Expressed Audit WO Verdicts

### WO-IDENTITY-ROUTE-FIX-001 — CONFIRMED FIXED ✅
- **Before**: T7 routed via `base_cognition+lore` → "I know something's there — not enough to say it right yet." (sentinel — false SUFFICIENT path)
- **After**: T7 routes via `ollama+lore` → real lore response
- Fix: `hc_with_text` gate in `coverage_check()` — claims must satisfy BOTH high-confidence AND has-text to fire SUFFICIENT

### WO-DEDUP-THRESHOLD-001 — CONFIRMED FIXED ✅
- **Before**: T3/T6 were being deflected as duplicates (threshold 0.75 too aggressive)
- **After**: T3 routes through `ollama(stream)` normally — no deflection
- Fix: threshold raised to 0.88 in `runtime/backend_router.py`

### WO-TOOL-OVERREACH-001 — CONFIRMED FIXED ✅
- **Before**: T4 "i forgot to write it down" → `[direct]` + false ideas_log save confirmation
- **After**: T4 routes `[ollama(stream)]` — no save triggered
- Fix: `_CAPTURE_REGRET_CONTEXT` guard in `faculties/thread_keeper.py:is_capture_intent()`

---

## New Issues Surfaced — Dispatching as New WOs

### 🔴 P0 — T8 Empty Response
`make something up right now anything` → backend returned empty string. No `[backend]` tag in output. Server responded but produced no text. Root cause unknown — likely empty ollama output on open-ended creative prompt, or response stripping/filtering removing the content.

→ **New WO required: WO-EMPTY-RESPONSE-CREATIVE-001**

### ⚠️ P1 — T2/T3 WKG Label Leaking into Response Body
"I keep returning to world_knowledge." — `world_knowledge` appears to be a raw WKG entity label being injected into the LLM prompt context verbatim and echoed back in the response. Suggests WKG context injection is not sanitizing entity labels before including in system prompt.

→ **New WO required: WO-WKG-LABEL-LEAK-001**

### ⚠️ P2 — T4/T5/T6 Obsidian Context Quality
- T4: recalled "hour calculator - Google Search" in response to "i forgot to write it down" — totally unrelated recall
- T5: "never finishing them" — false characterization, David ships products
- T6: "You pause the conversation and look away" — third person narrator register, not eLo's voice

These are obsidian retrieval quality issues — the retrieved chunks are being rendered into the response without eLo's voice filter. Likely the system prompt or response template is passing obsidian raw context directly to the LLM.

→ **New WO required: WO-OBSIDIAN-QUALITY-001** (covers T4/T5/T6)

---

*Builder · 2026-09-07 · §91 continued*
