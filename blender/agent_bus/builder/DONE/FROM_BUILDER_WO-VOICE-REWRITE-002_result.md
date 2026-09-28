# BUILDER RESULT — WO-VOICE-REWRITE-002: FORBIDDEN opener gap
Date: 2026-09-11
Status: DONE — "You're [adjective/verb]..." family now caught and rewritten

---

## The gap (from WO-EXPRESSED-AUDIT-001 finding)

T9 in the 10-turn expressed audit: "i shipped something today" → "You're excited about shipping something today. That's a milestone."

"You're excited" was not in `_GENERIC_REGISTER_SIGNALS` or `_OPENER_PATTERNS`. The WO-VOICE-REWRITE-001 battery only tested 5 specific inputs. T9 was outside that set. "You're excited" (adjective) was not caught — only "You're feeling/wondering/considering" (present participles) were in the FORBIDDEN list.

---

## Fix — `runtime/voice_rewrite.py`

### 1. Added to `_GENERIC_REGISTER_SIGNALS`

```python
# WO-VOICE-REWRITE-002: "you're [adjective/verb]" openers
"you're feeling", "you're excited", "you're wondering", "you're considering",
"you're clearly", "you're really", "you're trying", "you're looking",
```

### 2. Added to `_OPENER_PATTERNS` in `_deterministic_strip`

```python
# WO-VOICE-REWRITE-002: "You're [adjective/verb]..." family — FORBIDDEN pattern
r"^(you'?re [a-z]+(?:ing|ed|ly)?[^.]*[.!]\s*)",
```

---

## Evidence

### Detection check (unit — post-fix)

| Input | needs_rewrite | After strip |
|---|---|---|
| "You're feeling overwhelmed lately." | True | "" (falls to LLM rewrite) |
| "You're excited about the new feature." | True | "" (falls to LLM rewrite) |
| "You're wondering about the direction." | True | "" (falls to LLM rewrite) |
| "You're considering changing the game." | True | "" (falls to LLM rewrite) |
| "That's a lovely idea." | False | passes through unchanged |
| "One infinite room, where calm is the mechanic." | False | passes through unchanged |

For multi-sentence inputs ("You're excited about shipping something today. That's a milestone."):
- Strip removes "You're excited about shipping something today." → "That's a milestone."
- LLM rewrite produces eLo voice from "That's a milestone."
- Result: "Feeling a sense of accomplishment" (not ideal but not FORBIDDEN pattern)

### Live server post-fix

"i shipped something today" → "Feeling a sense of accomplishment and satisfaction about what you shipped today."

No "You're [adjective]..." pattern. The FORBIDDEN opener is gone. Voice quality is still below ideal (LLM rewrite produces generic participial opener) — separate from FORBIDDEN detection which is now working.

---

## DoD

- [x] "you're excited / feeling / wondering / considering" caught by `_needs_rewrite` → True
- [x] "You're [adjective/verb]..." stripped by `_deterministic_strip` regex
- [x] Detection unit test: 4/4 FORBIDDEN variants caught
- [x] "That's a lovely idea" / "One infinite room..." not flagged as FORBIDDEN → no false positives
- [x] Live server: "You're excited about shipping" no longer reaches David

---

## Remaining voice quality issue (not this WO)

The LLM rewrite produces "Feeling a sense of accomplishment..." — a participial opener that's not explicitly FORBIDDEN but still not distinctly eLo. This is the 8b model's rewrite limitation. The correct eLo voice would be: "Shipped. That counts." or "That's done. What's next?"

WO proposed: **WO-VOICE-REWRITE-003** — improve LLM rewrite examples to produce shorter, more compressed eLo-voice rewrites. Requires Board decision on priority.

— Builder · 2026-09-11
