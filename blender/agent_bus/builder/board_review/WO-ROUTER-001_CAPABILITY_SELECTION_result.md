# WO-ROUTER-001 Capability-Aware Backend Selection — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 8/8 ATs pass; already implemented in prior session

---

## What was verified

`runtime/backend_router.py`:
- Conversational tasks: Ollama wins over Groq when both available
- Conversational tasks: Groq selected when Ollama down
- Reasoning tasks: Groq 429 cooldown → Cerebras wins
- Pinned Groq + 429 → Ollama floor (not mock)
- All backends down → Mock (honest fallback)
- `capability` field present in routing trace
- Regression: brain authorship preserved
- Default Ollama model is `llama3.1:8b`

## ATs

- AT-1 ✅ conversational — Ollama wins over Groq
- AT-2 ✅ conversational — Groq when Ollama down
- AT-3 ✅ reasoning — Groq cooldown → Cerebras wins
- AT-4 ✅ pinned Groq 429 → Ollama floor
- AT-5 ✅ all down → Mock
- AT-6 ✅ capability field in routing trace
- AT-7 ✅ regression: brain authors preserved
- AT-8 ✅ default Ollama model is llama3.1:8b

**Run:** `python -m pytest tests/test_wo_router001_capability_selection.py -v` → **8/8 passed**
