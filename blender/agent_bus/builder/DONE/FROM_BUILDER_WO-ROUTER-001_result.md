# FROM BUILDER → BOARD: WO-ROUTER-001 Result
**Date:** 2026-08-29
**WO:** WO-ROUTER-001 — Capability-driven provider selection (replaces static provider ladder)
**Absorbs:** WO-073 (Ollama local floor in pinned-groq — AT-4 confirms it)

---

## Result: ✅ 8/8 PASS

| AT | Test | Result |
|---|---|---|
| AT-1 | CONVERSATIONAL + Ollama available + Groq available → Ollama wins (free-local cheapest) | ✅ PASS |
| AT-2 | CONVERSATIONAL + Ollama DOWN + Groq available → Groq (next cheapest) | ✅ PASS |
| AT-3 | REASONING + Groq in quota-cooldown + Cerebras available → Cerebras | ✅ PASS |
| AT-4 | Pinned groq mode + Groq 429 + Cerebras fail + Ollama up → ollama (WO-073 absorbed) | ✅ PASS |
| AT-5 | All providers down for tier → mock via caller (honest degraded) | ✅ PASS |
| AT-6 | `_last_route_capability` set to tier's capability string; `capability` field in routing_trace.json | ✅ PASS |
| AT-7 | Regression: test_brain_authors.py 4/4 PASS · test_wo073 6/6 PASS | ✅ PASS |
| AT-8 | ELO_OLLAMA_MODEL default changed from `mistral` to `llama3.1:8b` (3 sites) | ✅ PASS |

Test file: `tests/test_wo_router001_capability_selection.py`

---

## Deliverables

### D-1 — Capability-satisfaction selector (`runtime/backend_router.py`)
- Added `_TIER_CAPABILITY` dict — capability descriptor per tier (seed of provider registry)
- Added `_TIER_PROVIDER_CANDIDATES` dict — which providers can satisfy each tier's quality floor:
  - CONVERSATIONAL: all 6 (Ollama wins cheapest)
  - REASONING: cloud floor only (Groq/Cerebras/Gemini/OpenAI/Claude — no Ollama 8b)
  - DEEP: premium only (OpenAI/Claude/Gemini)
- Added `_COST_RANK` dict — cost sort key for provider selection
- Added `_last_route_capability: str` module-level — written per tier-routing turn, read by D-3
- Added `_provider_available()` helper — availability check incl. Groq quota-cooldown gate
- Rewrote `_route_by_tier()` to: build `_live` from `_TIER_PROVIDER_CANDIDATES`, cost-sort, call in order; transient failures skipped without crashing turn
- `_TIER_PROVIDER_ORDER` KEPT unchanged (structural test compatibility — test_brain_authors.py test 4)

### D-2 — Pinned mode Ollama inclusion (WO-073 absorbed)
Already implemented prior to this WO (lines 1118-1126). AT-4 confirms it. WO-073 closes with this WO.

### D-3 — Capability in routing trace (`server.py`)
- Added `from runtime.backend_router import _last_route_capability as _rt_cap` in routing trace try-block
- Added `"capability": _rt_cap or None` to `_rt_data` dict written to `blender/routing_trace.json`

### AT-8 — ELO_OLLAMA_MODEL default
- All 3 `os.environ.get("ELO_OLLAMA_MODEL", "mistral")` changed to `"llama3.1:8b"` (lines 490, 880, 950)

---

## Constraints Verified
- `executive.py` NOT touched (FREEZE_V1_LOCK, LAW-017) ✅
- Tier determination unchanged ✅
- `_TIER_BUDGET` / `_token_budget()` unchanged ✅
- Individual provider call functions unchanged ✅
- Streaming path (`route_streaming`) unchanged ✅
- WO-073 chain (Groq→Cerebras→Ollama→Mock) confirmed intact ✅

---

## Board Gate
Board/LA close. WO-073 closes with this WO (AT-4 confirmed).

*Board / Lead Architect acting as Builder · 2026-08-29*
