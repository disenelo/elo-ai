# WO-ROUTER-001 — Capability-driven provider selection

**From:** Board / Lead Architect — 2026-08-28
**Priority:** P1
**Full WO:** `engineering/work_orders/WO-ROUTER-001_capability_driven_provider_selection.md`
**Absorbs:** WO-073 (Ollama pinned-mode fallback — AT-4 closes WO-073)

**Authority:** David L3 canonical routing ruling 2026-08-28 — LLMs sit inside CAPABILITY. Provider is selected because it satisfies the required capability, NOT because it is next in a static priority list. `docs/architecture/_intake/SOURCE_2026-08-28_DAVID_L3_one_brain_canonical_routing.md`

---

## The problem (verified in code)

`backend_router.py` `_route_by_tier()` iterates `_TIER_PROVIDER_ORDER[tier]` in fixed positional order. This IS the static provider-authority ladder. Wrong model.

## What to build

**`backend_router.py` only — do NOT touch `executive.py` (FREEZE_V1_LOCK, LAW-017).**

1. **D-1** — Replace positional iteration in `_route_by_tier()` with capability-satisfaction selection: build availability list → select by cost preference within available set → call. No mock inside this function.
2. **D-2** — Pinned mode: insert Ollama BEFORE Mock in `mode == "groq"` block. Chain: `Groq → Cerebras → Ollama → Mock`. Default `ELO_OLLAMA_MODEL` to `llama3.1:8b` (NOT `mistral`) when env var unset.
3. **D-3** — Add `capability` field to `backend_used` routing trace log.

## 8 ATs — see full WO for exact spec

AT-1..3: capability-satisfaction selection (Ollama cheapest wins CONVERSATIONAL; quota-cooldown respected).
AT-4: pinned mode Groq-fail → Ollama (WO-073 absorption).
AT-5: all down → mock + honest degraded.
AT-6: `capability` field in trace.
AT-7: regression — `test_wo073_pinned_ollama_fallback.py` + `test_brain_authors.py` still pass.
AT-8: `ELO_OLLAMA_MODEL` defaults to `llama3.1:8b`.

**Return:** `DONE/FROM_BUILDER_WO-ROUTER-001_result.md` · 8/8 AT PASS · commit hash

*Board / Lead Architect · 2026-08-28*
