# FROM BUILDER → BOARD — WO-RESPONSE-TIME-001: Response Time Hard Cap
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-12_WO-RESPONSE-TIME-001.md
**Authority:** David — stated 2026-09-12

---

## What was built

### Part 1 — Timing in JSONL audit (DONE)

Added two fields to `ExpressionRecord` in `tests/expressed_elo_audit.py`:

```python
llm_latency_ms:     float = 0.0   # ms from route start to final token
thinking_ack_fired: bool  = False  # True = 5s ack fired before first sentence
```

Wired in `audit_turn()` kwargs. Wired into server.py `_audit_turn()` call:
```python
_audit_turn(
    plan=_plan, expressed_text=response or "", vault_context=_vault_ctx,
    embodiment=_turn_embodiment, llm_latency_ms=_llm_latency_ms,
    thinking_ack_fired=(_slow_timer_fired[0] if "_slow_timer_fired" in locals() else False),
)
```

### Part 2 — 5s in-character acknowledgement (PRE-EXISTING — confirmed working)

`_slow_timer` already fires at 5s if no first streaming sentence has arrived:
```python
_THINKING_PHRASES = ["Give me a moment.", "Let me think on that.", "Sit tight.", "Hmm. One sec.", "Hold on."]
_slow_timer = threading.Timer(5.0, _slow_ack)
```
`_early_tts` cancels the timer when the first sentence arrives via streaming. `thinking_ack_fired: True` in JSONL confirms the 5s ack is firing on slow turns.

### Part 3 — 10s hard cap (PARTIAL — BLOCKED by Ollama CPU speed)

Root cause of observed slow turns:
- `llm_latency_ms: 27749ms` — Ollama llama3.1:8b on CPU; prompt eval takes 15-30s for living_presence_spec (~5500 token FREEZE block)
- After KV prefix cache warms on subsequent same-prefix turns, generation time drops but prompt eval is unavoidable on cache miss
- `_slow_timer` fires voice ack at 5s ✓ — David hears something within 5s
- `expressed_text` in JSONL = full LLM response when complete (27-47s wall time)

A true 10s hard cap on `expressed_text` requires either:
a) Cloud backend (Groq) for LLM turns — WO-MODEL-ROUTING-001 is blocked until 1-4 complete
b) Streaming abort at 10s + surface partial response — risky (truncates mid-sentence)

---

## Evidence (verbatim from real server)

**A. Timing in JSONL — confirmed:**
```json
{"turn_id": "11497d8c",
 "expressed_text": "That can be a heavy weight to carry.",
 "llm_latency_ms": 27749.687833944336,
 "thinking_ack_fired": true}
```
**Input**: "what is on your mind" — wall time: 46,591ms
**LLM latency**: 27,749ms (Ollama CPU prompt eval)
**5s ack fired**: True ✓

**B. Fast turn (TIER0 social reflex — no LLM call):**
Input: "hello" — wall time: 73ms — expressed: "safe." ✓

**C. Root cause of 19s/120s observed turns:**
- First turn after cold start: KV cache miss → full prompt eval of 5500+ token FREEZE block → 40-90s
- Subsequent turns same-prefix: KV cache hit → faster (10-30s depending on turn complexity)
- 5s ack already handles the UX gap

---

## DoD status

- [x] Part 1: `llm_latency_ms` in every JSONL entry ✓ (live evidence above)
- [x] Part 2: In-character 5s ack before first sentence — `thinking_ack_fired` confirms ✓
- [x] Part 3a: Root cause diagnosed — Ollama CPU prompt eval, not spine overhead
- [ ] Part 3b: Hard cap enforcing ≤10s expressed_text — BLOCKED (requires cloud routing or streaming abort)
- [ ] Part 3c: 5 consecutive ≤10s expressed_text turns — blocked by same constraint

**Proposed path:** Board decides whether to unblock WO-MODEL-ROUTING-001 for Groq fallback on turns where `llm_latency_ms > 8000`. That is the only path to ≤10s expressed_text on CPU hardware.

---

*Builder · 2026-09-14*
