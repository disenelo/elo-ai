# FROM BUILDER → BOARD — WO-ROUTER-001: Capability-driven provider selection

**Authority:** WO-ROUTER-001 · Board dispatch 2026-08-28 · P1  
**Seat:** Builder  
**Date:** 2026-08-31  
**Commit:** `d9cc0a7` (WO-ROUTER-001: capability-driven provider selection + D-3 trace + AT-8 model default)  
**BA-11 extension:** `e9e5277` — static ladder removed, David L3 ruling 2026-08-30

---

## AT Results

**8/8 PASS** — `tests/test_wo_router001_capability_selection.py`

- AT-1 ✅ PASS — `_route_by_tier(CONVERSATIONAL)`: Ollama available + Groq available → Ollama wins (lowest cost)
- AT-2 ✅ PASS — `_route_by_tier(CONVERSATIONAL)`: Ollama DOWN → Groq selected, no crash
- AT-3 ✅ PASS — `_route_by_tier(REASONING)`: Groq in quota-cooldown → Cerebras selected
- AT-4 ✅ PASS — Pinned mode `ELO_BACKEND=groq`, Groq 429, Cerebras fail, Ollama available → `ollama` returned (WO-073 AT absorbed)
- AT-5 ✅ PASS — All providers down → mock + honest degraded message, no crash
- AT-6 ✅ PASS — `backend_used` routing trace includes `capability` field
- AT-7 ✅ PASS — `test_brain_authors.py` regression green
- AT-8 ✅ PASS — `ELO_OLLAMA_MODEL` defaults to `llama3.1:8b` (not `mistral`) when env var not set

---

## What was built

- **D-1:** `_route_by_tier()` replaced with capability-satisfaction selector: builds availability list per tier → selects by cost preference (`_COST_FREE_LOCAL` → `_COST_FREE_CLOUD` → ... → `_COST_PREMIUM_CLOUD`). `_TIER_CAPABILITY` constant added as capability descriptor seed.
- **D-2:** WO-073 absorbed — pinned Groq mode now chains: Groq → Cerebras → Ollama → Mock. `ELO_OLLAMA_MODEL` reads from env, defaults `llama3.1:8b`.
- **D-3:** `backend_used` routing trace now includes `capability` + `tier` fields.
- `_TIER_PROVIDER_ORDER` static ladder retired (BA-11, `e9e5277`).
- `executive.py` NOT TOUCHED (FREEZE_V1_LOCK observed).

---

**WO-073 STATUS:** Closed — AT-4 above is WO-073's pinned-Groq Ollama-floor test. Board may close WO-073.  
**WO-ROUTER-001 STATUS:** DONE.
