# WO-072 — Intent Gatekeeper (rules-first, cheap-LLM normalizer)

> **⚡ VERIFY FIRST** — `tests/test_wo072_intent_gatekeeper.py` exists. **Run it before any implementation.** If all ATs pass → return result card and close (Rule 4.1). If any fail → implement only the failing items.

**Full WO:** `engineering/work_orders/WO-072_Intent_Gatekeeper_Rules_First_LLM_Normalizer.md`
**Priority:** P1 · **Status:** OPEN (spec'd 2026-08-07, never dispatched)
**Owner:** Builder (intent/routing lane)

---

## The mandate

A command/tool must ONLY fire when eLo is **certain** of intent. Three levels:
1. **Hard rules** — pattern-match clean commands instantly, no LLM, no latency. Fast path.
2. **Cheap LLM normalizer** — for ambiguous input: "do it" / "fire" / "what's that?" → classify intent using a cheap/fast model (Ollama / Groq at CONVERSATIONAL tier, AT-bounded).
3. **Default to conversation** — if normalizer is unsure, default to CONVERSATION, never a command. ("No", "what does that mean?" → conversation, not quit/close/stop.)

**Fast path must NOT call LLM** for clean unambiguous commands (assert normalizer wasn't invoked).

---

## Test

`tests/test_wo072_intent_gatekeeper.py`:
- Clean explicit command → fast path only (no LLM normalizer called)
- Ambiguous input → normalizer resolves correctly
- Unsure input → defaults to CONVERSATION, never command/tool

Also refer to the David fast-input samples in the full WO for the L3 live-test script.

---

## Constraint

`executive.py` — check FREEZE_V1_LOCK. This is a routing/intent lane fix; prefer server.py / intent_engine.py path. Do NOT restructure the executive kernel.

## Return

`DONE/FROM_BUILDER_WO-072_intent_gatekeeper_result.md` · AT pass count · commit hash (or "VERIFY: already passing, no implementation needed")

*Board / Lead Architect · 2026-08-29*
