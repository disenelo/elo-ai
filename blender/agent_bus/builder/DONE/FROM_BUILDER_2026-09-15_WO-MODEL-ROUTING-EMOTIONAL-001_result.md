# FROM BUILDER → BOARD — WO-MODEL-ROUTING-EMOTIONAL-001: Emotional Routing to Groq
**Date:** 2026-09-15
**WO:** FROM_ARCHITECT_2026-09-11_WO-MODEL-ROUTING-EMOTIONAL-001.md
**Authority:** David L3 — 2026-09-11

---

## Changes Applied

**`runtime/backend_router.py`** — three additions:

**1. `route()` — emotional override (non-streaming path)** (around line 1292):
- `_EMOTIONAL_ACTIONS = ("ground", "witness", "reflect")` — action-name gate
- `_EMOTIONAL_ROUTING_THRESHOLD = 0.6` — significance score fallback gate
- If action in tuple OR sig ≥ 0.6: calls `_groq_call()` before Ollama
- On HTTP 429: sets `_groq_quota_cooldown_until = time.monotonic() + 60.0`, falls to Ollama

**2. `route_streaming()` — emotional override (streaming path)** (around line 1713):
- Same gate logic as `route()`
- Uses `_groq_call()` (non-streaming) — compound-beta SSE stream returns empty raw in ThreadingHTTPServer context
- Fires `on_first_sentence` manually from `_groq_call` result before returning
- Dedicated minimal emotional system prompt (394 chars) — full living_presence_spec (~5500 tokens) triggers HTTP 413 on compound-beta, and compound-beta's compound reasoning mode overrides eLo voice with a long general spec
- 429 cooldown same as `route()`

**3. `_groq_call()` and `_groq_stream()`** — LiteLLM prefix strip:
- `if "/" in model: model = model.split("/", 1)[-1]` — strips `groq/` prefix that `.env` may carry

**`.env`** — two updates:
- `ELO_GROQ_MODEL=compound-beta` (was `compound-beta-mini` — too restrictive rate limits, 429 on every server call; switched to `compound-beta` which has adequate rate limits)
- `ELO_FIRST_TOKEN_MS=8000` (raised from 2500ms — server load + SSL overhead)

---

## Diagnosis: why it wasn't working before

| Root cause | Fix |
|---|---|
| `ELO_GROQ_MODEL=groq/compound-mini` — LiteLLM prefix invalid for native Groq API → HTTP 404 | Added `if "/" in model: model = model.split("/", 1)[-1]` in both `_groq_call()` and `_groq_stream()` |
| `compound-mini` is not a valid Groq model ID | Corrected to `compound-beta-mini` |
| `compound-beta-mini` rate limits → HTTP 429 on every server call | Switched to `compound-beta` (adequate limits confirmed) |
| Full living_presence_spec payload (5500 tokens) → HTTP 413 on compound-beta | Dedicated minimal emotional system prompt (394 chars) |
| compound-beta's compound reasoning mode overrides eLo voice with long general spec | Minimal prompt with explicit format constraints (1-2 sentences, no "I", no analysis) |
| `_logger.warning` suppressed by server log config — failures were invisible | Added `print()` diagnostics (`[EMO_CHECK]`, `[EMO_ENTER]`, `[EMO_CALL]`, `[EMO_RAW]`, `[EMO_WIN]`, `[EMO_HTTP]`, `[EMO_EXCEPT]`) |

---

## Structural note

**`ground` actions at TIER1** are intercepted by `social_reflex` before reaching `route_streaming`. TIER1 social_reflex returns a response directly without calling `route_streaming` — those turns do not pass through the Groq override. This is by design (TIER1 is a fast path) and outside the scope of this WO. The override applies to TIER2+ turns where executive assigns `action` in the emotional tuple.

---

## Evidence — live server

**Turn 1 — emotional witness turn:**
```
Input:   "witness me in this moment — sit with me in the stillness"
Action:  reflect (executive classification)
Sig:     0.000 (action-name gate triggers, sig gate not required)

[EMO_CHECK] action=reflect sig=0.000 is_emo=True groq_avail=True
[EMO_ENTER] in_cooldown=False cd_until=0.0
[EMO_CALL] calling _groq_call for action=reflect sys_len=394
[EMO_RAW] raw_len=108 first_ms=1225
[EMO_WIN] returning groq(emotional) for action=reflect
[eLo] backend=groq(emotional) action=reflect

HTTP response: {
  "response": "Stillness holds us, breath and heartbeat echo in quiet. Together we sit, the moment unfolding without words.",
  "mode": "reflect",
  "backend": "groq(emotional)"
}
```

**Voice check:**
- Starts with "Stillness" — not "I", not a FORBIDDEN opener ✓
- No therapist phrases ("it sounds like", "I hear that") ✓
- Short, poetic, 2 sentences ✓
- Witnesing / present — not analytical ✓
- LLM latency: 1225ms (Groq fast path; Ollama was 11000–31000ms on same hardware)

**Audit entry (expressed_elo_audit.jsonl turn_id: 6c6247e8):**
```
action:    reflect
latency:   1225ms
lessons:   ['Completed a capability milestone — reinforce this pattern.']
tier_violations: []
gaps:      []
```

**Learning continuity:** the spine post-processing (vault_write, lessons, tier fields) runs on every faculty turn regardless of which model ran inference — confirmed by audit entry existing for the Groq turn with populated lessons + vault_context. Model routing is below the spine layer.

---

## DoD

- [x] One real server turn on an emotional grounding input ✓
- [x] Verbatim model used: `groq(emotional)` in HTTP response + `[EMO_WIN]` print + backend line ✓
- [x] Emotional weight score shown: sig=0.000, action="reflect" (action-name gate triggered) ✓
- [x] Verbatim expressed output: "Stillness holds us, breath and heartbeat echo in quiet. Together we sit, the moment unfolding without words." ✓
- [x] No FORBIDDEN opener ✓
- [x] No therapist pattern ✓
- [x] Learning layer (lessons, audit) populated on Groq turn ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-15*
