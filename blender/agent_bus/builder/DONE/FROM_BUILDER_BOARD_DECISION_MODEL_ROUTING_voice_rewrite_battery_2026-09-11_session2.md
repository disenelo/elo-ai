# BUILDER RESULT — Board Verification Battery: Voice Rewrite Layer (Session 2)
Date: 2026-09-11
Status: DONE — 4/5 PASS. T5 therapist-phrase-only edge case remains.

---

## Board mandate (FROM_ARCHITECT_2026-09-11_BOARD_DECISION_MODEL_ROUTING.md)

Run same 5 turns with WO-VOICE-REWRITE-001 active. Verbatim output. Score against FORBIDDEN opener criteria.

---

## Voice rewrite changes applied this session

### 1. `_needs_rewrite()` — breadth alignment (WO-VOICE-REWRITE-002 gap)
Added `if low.startswith("you're ") or low.startswith("you're,")` to catch ALL "you're [word]" openers, not just specific variants.

### 2. Added therapist-voice phrases to `_GENERIC_REGISTER_SIGNALS`
```python
"let's step back", "let us step back", "what's alive in you",
"let me hold space", "hold space for", "i'd like to invite",
"i want to acknowledge", "i hear that", "that makes sense that",
```

### 3. Added therapist patterns to `_OPENER_PATTERNS` in `_deterministic_strip`
```python
r"^(let'?s (step|take a step) back[^.]*[.!]\s*)",
r"^(let me hold space[^.]*[.!]\s*)",
r"^(i want to acknowledge[^.]*[.!]\s*)",
r"^(i hear that[^.]*[.!]\s*)",
```

### 4. Added therapist examples to `_ELO_VOICE_EXAMPLES` (NOT eLo section)
"Let's step back together...", "What's alive in you right now...", "Let me hold space for...", etc.

### 5. Run `_deterministic_strip` on LLM rewrite output
After `rewritten = llm_caller(msgs)`, strip banned openers from the rewrite before returning.

### 6. `_deterministic_strip` returns `""` instead of original for all-banned inputs
When entire response is a banned opener and nothing remains after strip, return `""` (not original).

### 7. When `cleaned` is `""`, pass `candidate` to LLM (not empty draft)
LLM now receives the original content to rewrite rather than an empty draft.

---

## Verbatim 5-turn battery (real server, PID 86280, 2026-09-11)

| Turn | Input | Response | FORBIDDEN? |
|---|---|---|---|
| T1 | "yo what you been up to" | "I've been exploring the conversation." | PASS ✅ |
| T2 | "i keep starting things and not finishing them" | "Holding onto too many things that save limiters, and it's hard to let go of the ideas." | PASS ✅ — "You've been" stripped |
| T3 | "what if elo could dream in colour" | "What if eLo's dreams were an entire landscape of warm ambers, where every possibility blooms like a sunflower in a field of honey?" | PASS ✅ |
| T4 | "elo planet is the whole universe innit" | "I know something's there — not enough to say it right yet." | PASS ✅ |
| T5 | "been feeling a bit overwhelmed with everything lately" | "Let's step back together." | FAIL ❌ |

**Score: 4/5 PASS** (compared to 1/5 pre-voice-rewrite)

---

## T5 root cause (unresolved)

The faculty (8b model) produces ONLY "Let's step back together." for the overwhelmed input — the entire response is a therapist phrase with no substance. The rewrite layer:
1. Detects "let's step back" → `_needs_rewrite = True`
2. Strips to `""` (entire response was the banned phrase)
3. Calls LLM with `candidate = "Let's step back together."` (no substance to extract)
4. LLM echoes the same phrase (8b can't diverge from it)
5. Strip removes LLM output to `""` → fallback returns original

The fix for T5 requires either:
- Passing the user message to `voice_rewrite()` so the LLM can generate a FRESH response (not a rewrite)
- Routing "overwhelmed" inputs to a specific eLo response pattern
- Accepting that 8b cannot reliably handle this register without user message context

This is a model-tier constraint for pure-therapist-register responses. Not addressable with signal/pattern changes alone.

---

## DoD

- [x] FORBIDDEN "You're [adjective/verb]" openers: 0/5 turns ✅
- [x] FORBIDDEN therapist phrases: caught and stripped when substance exists ✅
- [x] "Let's step back together" detected by `_needs_rewrite` ✅
- [x] LLM rewrite output also stripped before return ✅
- [x] Overall score: 4/5 (vs 1/5 pre-voice-rewrite)
- [ ] T5 "Let's step back together" (pure-therapist-only response) — OPEN — model constraint

FREEZE check:
- `runtime/executive.py`: NOT TOUCHED ✅
- `prompts/living_presence_spec.txt`: NOT TOUCHED ✅

— Builder · 2026-09-11
