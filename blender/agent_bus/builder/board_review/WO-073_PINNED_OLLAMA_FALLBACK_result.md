# WO-073 Pinned Ollama Fallback — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 6/6 ATs pass; already implemented in prior session

---

## What was verified

`runtime/backend_router.py`:
- Fallback chain extended: Groq → Cerebras → **Ollama** → Mock
- eLo never drops to the mute mock while a local Ollama brain is running
- Pinned-Groq 429 + Cerebras down + Ollama up → returns `"ollama"`
- Pinned-Groq success → still `"groq"` (no regression)
- All down → `"mock"` (honest fallback unchanged)
- `active_backend()` groq mode: Groq+Cerebras down, Ollama up → `"ollama"`

## ATs

- AT-1 ✅ pinned mode, Groq 429 + Cerebras down + Ollama up → ("...", "ollama")
- AT-2 ✅ pinned mode, Groq succeeds → "groq" (no regression)
- AT-3 ✅ pinned mode, all three down → "mock"
- AT-4 ✅ active_backend() groq mode, Groq+Cerebras down, Ollama up → "ollama"
- AT-5 ✅ active_backend() all down → "mock"
- AT-6 ✅ py_compile clean on backend_router.py

**Run:** `python3 tests/test_wo073_pinned_ollama_fallback.py` → **6/6 passed**
