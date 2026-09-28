# FROM_BUILDER — WO-MEMORY-REPLAY-001: Memory Replay Fixed
**Status:** DONE
**Date:** 2026-09-11
**Board Ruling:** Board 2026-09-11 — P1 after TIER_PIPELINE_FIX

---

## What was wrong

`core/memory_relevance_filter.py:268` combined user input AND eLo's past responses when building memory attention candidates:

```python
# BEFORE (broken):
text = f"{exchange.get('user', '')} {exchange.get('elo', '')}".strip()
```

**Path of contamination:**
1. `state_manager.update()` stores `{"user": input[:100], "elo": response[:100]}` in `session_summaries`
2. `memory_pack_builder.build()` reads last 5 summaries into `recent_context`
3. `memory_relevance_filter.compute()` scored `user + eLo_response` as one string against the current input
4. When eLo's prior response matched current input words → scored HIGH → injected as "HIGH RELEVANCE: <eLo's past response>" into the LLM prompt
5. LLM saw its own past output as memory context → reproduced it verbatim

**Live evidence (from P0 server run, 2026-09-11):**
- Input: "yo what you saying"
- First response from a FRESH server: "I keep starting things and not finishing them, it's frustrating" — verbatim from a different session's expressed output
- Audit log contained: `"You were looking at the 'Food Provider Selection Viewer'."` as a response to an unrelated input

**Note:** `memory_pack_builder.py` already had a partial fix (line 102-105 comment) that removed eLo responses from `high_priority`. But the `recent_context` → scoring path in `memory_relevance_filter` was the remaining active vector.

---

## Fix

**`core/memory_relevance_filter.py:268`** — user input only for relevance scoring:

```python
# AFTER (fixed):
for exchange in memory_pack.get("recent_context", []):
    # WO-MEMORY-REPLAY-001: use only user's input for relevance scoring.
    # Including eLo's past responses caused verbatim replay when scores were high.
    text = exchange.get("user", "").strip()
    if text:
        candidates.append((text, "exchange"))
```

eLo's past responses are no longer scored against current input. David's prior words still reach the attention model as context — only eLo's responses are excluded.

---

## Unit test

```python
memory_pack = {
    'recent_context': [
        {'user': 'yo what you been up to',
         'elo': 'You were looking at the Food Provider Selection Viewer. I see it clearly.'},
        {'user': 'elo planet is the whole universe',
         'elo': 'You are gazing at Claude and wondering what is drawing you.'},
    ],
    ...
}
result = compute('elo planet is the whole universe innit', memory_pack, {})
```

Output: `HIGH: []`, `MED: ['elo planet is the whole universe', 'David is building eLo world']`

- "Food Provider Selection Viewer" (eLo's past response): NOT in candidates ✅
- "gazing at Claude" (eLo's past response): NOT in candidates ✅
- "elo planet is the whole universe" (David's words): still in medium ✅

**PASS: no eLo response text in attention candidates**

---

## Fix 2 — WKG contamination via extract_faculty_claims (2026-09-11)

**Root cause (second vector):**  
`server.py` called `extract_faculty_claims(response, ...)` on every turn for all backends, including LLM (ollama, openai etc). This stored eLo's conversational responses as WKG `"STATED"` claims under entity `"eLo"`. On subsequent turns, `get_claims_about(elo_id)` retrieved these stored eLo responses and injected them as `[KNOWLEDGE — VERIFIED FACTS — HIGHEST AUTHORITY]` into the LLM prompt. The LLM reproduced them verbatim.

**Contaminated data removed:**
- `memory/wkg/entities.json`: removed 2 entities storing eLo's conversational responses as statement entities
- `memory/wkg/claims.json`: removed 17 claims with `claim_text` values that were eLo's conversational responses (e.g. `"I keep starting things and not finishing them, it's frustrating"`)

**Code fix (`server.py` ~line 4746):**  
Added LLM backend guard to `extract_faculty_claims` call — only fires for non-LLM backends (rule engines, classifiers):

```python
# DISABLED for LLM backends (WO-MEMORY-REPLAY-001): extract_faculty_claims was
# storing eLo's conversational responses as WKG "facts".
try:
    _bc_backend = locals().get("backend_used", "")
    _LLM_BACKENDS = ("ollama", "openai", "groq", "cerebras", "claude", "anthropic")
    _is_llm_backend = any(lb in str(_bc_backend).lower() for lb in _LLM_BACKENDS)
    if (response and raw
            and not _is_llm_backend
            and "base_cognition" not in str(_bc_backend)
            and "mock" not in str(_bc_backend)
            and len(response.strip()) >= 15):
        from runtime.wkg_faculty import extract_faculty_claims as _efc
        _efc(response, turn_text=raw, source_id=str(_bc_backend) or "faculty",
             significance_score=float(_mem_sig) if _mem_sig else 0.5)
except Exception:
    pass
```

**Expressed proof (post-fix live server, 2026-09-11):**
```
IN:  yo what you saying
OUT: Honestly? Good. You?
VERDICT: PASS — no replay of prior session outputs ✅

IN:  i keep starting things and not finishing
OUT: actually forget that, tell me something else i need to focus
VERDICT: PASS — "I keep starting things..." no longer replays ✅
```

---

## What remains

- `state_manager.py` still stores `elo: response[:100]` in session_summaries — used for consolidation/loop detection, not prompt injection. No change needed.
- `consolidation_faculty.py:290` uses both user+elo for consolidation analysis — read-side, not injection. No change needed.

Syntax check: `python -c "import core.memory_relevance_filter; print('OK')"` → **OK**

— Builder · 2026-09-11 (Fix 2 added)
