---
id: WO-026
title: "eLo faster responses — enable streaming + response-mode token budgets + fast model for chat/routing + unify model string + surface latency"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P1
reason: "David 2026-08-02: behaviour tests all green but responses feel slow. Diagnostics found streaming OFF, high/inconsistent max_tokens, one heavy model for everything, and a model-string mismatch. This WO addresses response latency."
review_required: L1 → L3 (David feels the speed in real use)
risk: medium (touches the backend call path; streaming changes output flow — keep behaviour identical, just faster)
status: READY
created: 2026-08-02
diagnostics: "stream:False in backend_router.py:218 + api_layer.py:275 · max_tokens 500/700/512/1024 · claude-sonnet-4-5 (backend_router) vs 4-6 (rest) · llm_latency_ms exists in spine.py:859"
---

# WO-026 — faster eLo responses (latency)

Behaviour is correct (WO-019/020/022 green) — this is purely about **speed of response**. Four levers,
biggest first.

## 1. Enable streaming (the big one)
- `backend_router.py:218` and `core/api_layer.py:275` both send `"stream": False`. Turn streaming **on**
  and consume tokens as they arrive.
- **Stream the first sentence to TTS + chat immediately** (pairs with WO-019's bubble-join) so eLo starts
  speaking/showing on sentence 1 instead of after the whole completion. This is the largest perceived-speed
  win and also fixes "long pause then everything at once."
- Keep the non-stream path as a fallback (flag `ELO_STREAM=1`, default on once verified).

## 2. Response-mode token budgets
- `max_tokens` is 500–1024 across paths — long for casual chat. Set **per response-mode** (CAL / kernel):
  short for ANSWER/CONVERSATIONAL (~200–300), larger only for BUILD/plan/reflect. Shorter generation =
  faster finish.

## 3. Fast model for chat + routing
- Route **conversational + routing/classification turns to a fast model** (`gpt-4o-mini` or a Haiku), and
  reserve Sonnet for deep reasoning (BUILD/REFLECT). Model-by-mode via the existing backend router; env
  overridable (`ELO_FAST_MODEL`, `ELO_DEEP_MODEL`).

## 4. Unify the model string + surface latency
- Reconcile `claude-sonnet-4-5` (backend_router) vs `claude-sonnet-4-6` (api_layer/base_backend) → one
  canonical `ELO_MODEL`; nothing silently on a stale model.
- **Surface `llm_latency_ms`** (already computed in `spine.py:859`) into `blender/routing_trace.json` +
  the voice/response trace, so per-turn latency is visible (and the dashboard can show it).

## Acceptance
1. Streaming on: first sentence appears/speaks within a fraction of the old full-response wait; behaviour
   unchanged (same content, just incremental). Fallback path intact.
2. Conversational turns use the short token budget + fast model; deep turns unchanged.
3. Model string unified; `llm_latency_ms` present in the trace every turn.
4. `tests/test_wo026_response_speed.py`: streaming assembles the same final text as non-stream; token
   budget selected by mode; latency field emitted; frozen kernel green.
5. Handback: before/after latency numbers (first-token + full-response) from the trace; David feels it live.

## Notes
- 🔵 CONFIRM-class once tests pass — but David feels the speed in real use before DONE.
- Pairs with WO-019 (voice) — streaming lets TTS start on sentence 1, compounding that fix.
