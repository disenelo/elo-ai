# FROM BUILDER — WO-MODEL-ROUTING-EMOTIONAL-001 — PART 1 CODE APPLIED

**Date:** 2026-09-11
**Status:** CODE APPLIED — real server evidence pending (restart required)
**Authority:** David L3 confirmed 2026-09-11

---

## What was built (Part 1 — Model routing by emotional weight)

### backend_router.py changes

1. **Constant added:** `_EMOTIONAL_ROUTING_THRESHOLD = 0.6` (line ~67) — David L3 authorized; Builder to tune against real turns.

2. **`route()` signature:** Added `emotional_weight: float = 0.0` parameter.

3. **Emotional routing gate:** Inserted BEFORE the tier-aware routing (`_route_by_tier`) in `route()`. When:
   - `ELO_BACKEND` is NOT set (auto mode — not pinned to a specific backend)
   - `emotional_weight >= 0.6`
   - Groq is available
   
   → Routes to Groq (`llama-3.3-70b-versatile`, the default Groq model).
   
   Fallback chain: Groq → Cerebras → (falls through to tier routing / auto waterfall → Ollama).
   Returns backend label `"groq(emotional)"` or `"cerebras(emotional)"` so the audit log shows the reason.
   Logging: `_logger.info("WO-MODEL-ROUTING-EMOTIONAL-001: sig=%.3f >= %.1f — routing to Groq (emotional weight gate)", ...)`

4. **`route_streaming()` signature:** Added `emotional_weight: float = 0.0` parameter. Passed through to all four `route()` fallback calls inside `route_streaming`.

### server.py changes

Both route call sites now pass `emotional_weight`:
```python
_emo_weight = float(exec_decision.get("significance_score", 0.0) or 0.0) if exec_decision else 0.0
response, backend_used, _llm_latency_ms = _route_streaming(
    system, _enriched, ..., emotional_weight=_emo_weight,
)
```
The `significance_score` comes from `exec_decision` which is built from `_plan.significance_score` (set by the significance faculty via spine).

---

## What's NOT done yet (Part 2 — Learning pipeline continuity)

The WO requires verification that every faculty turn writes to WKG/SPG/interactions/lessons regardless of which model ran it. This is an audit requirement — the write paths already exist (WO-WKG-WRITE-FIX-001 ✓, WO-SPG-SIGNAL-QUALITY-001 ✓, WO-MEMORY-REPLAY-001 ✓). Verifying that a Groq-routed turn ALSO produces WKG/SPG writes requires:
- A real server turn that triggers emotional routing (sig >= 0.6)
- Check WKG entities.json for new entries after that turn
- Check data/spg_graph.json for new signal entries
- Check that the lesson from that turn appears in TIER fields on the following turn

This verification is pending David's server restart and a real grounding/emotional turn.

---

## Syntax checks

- `runtime/backend_router.py`: OK
- `server.py`: OK

---

## DoD status

| Requirement | Status |
|---|---|
| Groq preferred when sig >= 0.6 and auto mode | ✅ code applied |
| Cerebras fallback if Groq unavailable/429 | ✅ code applied |
| Routing decision logged (model + emotional weight) | ✅ logger.info with sig score |
| Real server turn — verbatim which model, what sig | ⚠️ pending restart |
| Learning continuity — WKG/SPG write from Groq-routed turn | ⚠️ pending restart |

*Builder · 2026-09-11*
