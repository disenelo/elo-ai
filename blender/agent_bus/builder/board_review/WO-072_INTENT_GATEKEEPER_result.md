# WO-072 Intent Gatekeeper — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 12/12 ATs pass; already implemented in prior session

---

## What was verified

`intent_gatekeeper.py` + `server.py`:
- Rules-first routing: ambiguous/emotional/conversational fragments stay as conversation — not mis-routed to tools or cancel
- "No but..." style text NOT classified as cancel (chaos guard)
- Real commands ("come sit") still route correctly
- Confidence gate: ambiguous short fragments → conversation
- Fast path: clean commands do NOT trigger LLM normalizer
- Degrade path: use_llm=False, low-confidence rules → conversation, no crash

## ATs

- AT-1 ✅ "anything we can press on with?" → conversation
- AT-2 ✅ "No but it takes time to build you" → conversation (NOT cancel)
- AT-3 ✅ "Strange reply what does that mean?" → conversation (NOT tool)
- AT-4 ✅ "come sit" → sit (real command still routes)
- AT-5 ✅ "how's the company" → company
- AT-6 ✅ "what's the weather" → weather
- AT-7 ✅ confidence gate — ambiguous short fragment → conversation
- AT-8 ✅ degrade (use_llm=False) → conversation, no crash
- AT-9 ✅ fast path — clean command does NOT call LLM normalizer
- AT-10 ✅ cancel guard — "no but..." NOT classified as cancel
- AT-11 ✅ chaos scenario: "No but it takes time to build you" NOT cancel
- AT-12 ✅ py_compile clean on intent_gatekeeper.py and server.py

**Run:** `python3 tests/test_wo072_intent_gatekeeper.py` → **12/12 passed**
