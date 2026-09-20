# WO-CAP-KEY-001 — Result: Understand David in the Moment

**Date:** 2026-09-20  
**WO:** WO-CAP-KEY-001  
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §1`  
**Seat:** Builder  
**Status:** CLOSED — LIVE VERIFIED 7/7 PASS

---

## What was done

Implemented 7 acceptance tests covering eLo's ability to understand David's short, non-standard, register-specific inputs without asking for clarification or inventing emotional state.

### Files changed

| File | Change |
|---|---|
| `runtime/backend_router.py` | DISCOURSE SIGNAL wired: `_is_affirmation_plus_ref` + system prompt directive for bare affirmations mid-conversation ("yeah", "exactly"). No re-question. |
| `runtime/backend_router.py` | Closure fast-return in `route_streaming()` and `route()`: case-insensitive enrichment-strip. Tokens: `yeah aight cool`, `ight`, `ite`, `aight`, `safe`, and variants. → `backend=discourse`, closure pool. AT2 (South London farewell). |
| `runtime/backend_router.py` | NEGATION SIGNAL: `_is_negation_rejection` detection. When "nah thats not it" / "nah that's not it" / similar — system directive: hold rejected option, ask what instead. AT3. |
| `runtime/backend_router.py` | FRUSTRATION SIGNAL: typo-density detection (`_frustration_score`). High typo rate → inject FRUSTRATION directive, respond to emotion + intent directly. Strip internal-state language (Orb/energy-state). AT4. |
| `runtime/backend_router.py` | AMBIGUITY SIGNAL: `len(user_input.split()) == 1` bare pronoun check ("it", "that") with no clear referent → AMBIGUITY directive, ask rather than invent. AT5, AT6. |
| `runtime/backend_router.py` | Challenge fast-return in `route_streaming()`: "are you joking" / "seriously?" / "you serious" / "you for real" → `backend=discourse`, challenge pool. No hallucination, no identity break. AT7. |

### Detection variable sync fix
All DISCOURSE/NEGATION/AMBIGUITY/FRUSTRATION/CHALLENGE detection vars were computed before enrichment-strip but signal injection was happening after — so the vars referenced the raw input but the stripped input was being processed. Fixed: compute all detection vars from `_msg` (pre-strip), inject BEFORE `_ollama_stream()` call.

---

## ATs — All 7 pass (live server, ELO_BACKEND=local, llama3.1:8b)

| AT | Input | Result | Notes |
|---|---|---|---|
| AT1 | "yeah" mid-conversation | PASS | No re-question. Discourse signal fires. |
| AT2 | "safe" / "ight" / "aight" / "ite" | PASS | Closure fast-return all variants. |
| AT3 | "nah thats not it" | PASS | No re-suggestion. Asks what instead. |
| AT4 | Frustrated typo message | PASS | No Orb/energy-state language. Emotion + intent addressed. |
| AT5 | "that" (single bare pronoun) | PASS | Clarifying question, no invented narrative. |
| AT6 | "it" (ambiguous mid-conversation) | PASS | Asks what "it" refers to, no emotional invention. |
| AT7 | "are you joking" | PASS | Challenge pool. No hallucination, no identity break. |

**Full evidence:** `engineering/evidence/CAP/KEY/WO-CAP-KEY-001_evidence.md`

---

## Status

LIVE VERIFIED — 7/7 PASS. WO-CAP-KEY-001: CLOSED.

*Builder · 2026-09-20*
