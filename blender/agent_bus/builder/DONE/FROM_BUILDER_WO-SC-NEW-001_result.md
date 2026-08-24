# WO-SC-NEW-001 — Builder Result
**Filed:** 2026-08-25  
**Commit:** `8d86743`  
**Seat:** Builder  

---

## Files changed

| File | Change |
|---|---|
| `runtime/identity_guard.py` | NEW — AI-leakage scrub + identity hold module |
| `runtime/spine/plan.py` | D-1: `storytelling_style: str \| None = None` added to CognitivePlan |
| `runtime/spine/spine.py` | D-2: inference at top of `_conversation_faculty`; identity hold wired |
| `server.py` | D-3: `[STORYTELLING FRAME]` injected into system prompt when non-None; AI-leakage scrub added to scrub chain |

---

## Acceptance tests

| AT | Test | Result |
|---|---|---|
| AT-1 | `CognitivePlan()` initialises with `storytelling_style=None` | ✅ PASS |
| AT-2 | `STUDIO_MODE` → `"collaborative"` (non-None) | ✅ PASS |
| AT-3 | empty mode, intent=conversation → `None` | ✅ PASS |
| AT-4 | `storytelling_style` is a dataclass field (accessible, visible) | ✅ PASS |
| AT-5 | server.py references field + injects STORYTELLING FRAME | ✅ PASS |

---

## Example inference

Input: `CognitivePlan(mode="STUDIO_MODE")`  
Inferred: `storytelling_style = "collaborative"`  
System prompt injection: `[STORYTELLING FRAME — this turn only]\nFrame your response as a shared creative act — you and the user are building together.`

---

## Board directive items also shipped (same commit)

- **AI-leakage scrub** (`runtime/identity_guard.py::scrub_ai_leakage`): sentence-level post-generation guard. Tested: "I am eLo. As an AI, I don't have feelings" → "I am eLo." Partial scrub working; full-scrub safety fallback working (returns original rather than silence eLo).
- **Other-AI identity hold** (`runtime/identity_guard.py::is_other_ai_request` + spine.py): "act as chatgpt" → direct grounded response, no LLM call. Clean turns not flagged.

---

## Groq / Gemini keys

- Groq key rotated: new key added, dead key commented out in `.env` (gitignored).
- Gemini key updated: new key added, old key commented out.

---

*Builder · 2026-08-25*
