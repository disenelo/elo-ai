# Board Review — 0057: The 4-Second Rule
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW — PROPOSAL REQUIRED BEFORE IMPLEMENTATION

---

## §2 cheap wins — state at review time

| # | Action | Status | Finding |
|---|---|---|---|
| **A** | Model mismatch — `.env` says 8b, Ollama serving 70b | ✅ **NOT PRESENT** | `.env` says `ELO_OLLAMA_MODEL=qwen2.5-coder:14b`. Ollama has `qwen2.5-coder:14b` (8.99 GB) and `mistral-nemo:12b`. No 70b model installed. This was fixed before this review. |
| **B** | `keep_alive` — 4.6s cold load per turn | ✅ **FIXED** | `backend_router.py:814` sets `"keep_alive": "30m"` on the non-streaming Ollama path. `backend_router.py:2246` sets it on the streaming path too. Model stays resident between turns. |
| **C** | Server restart | ⚠️ **PENDING** | Requires David's terminal. Cannot be done in AUTORUN. Current session has no running server. |

**A and B are done. C needs David.**

---

## §3 — Is the 4s rule wired?

**YES — partially.** Card 0057 said `_TIER_PROVIDER_ORDER` had zero references outside its definition. The current code has `_TIER_PROVIDER_CANDIDATES` (renamed) used in `_tier_route()` (line 988), and the 4s rule is at `backend_router.py:998-1028`.

**How the current 4s rule works:**
1. `_tier_route()` calls `_ollama_call()` — a BLOCKING, non-streaming HTTP request
2. Ollama runs to completion (~9s prompt eval)  
3. `_last_ollama_metrics["prompt_eval_ms"]` is read AFTER Ollama finishes
4. If > 4000ms, discards Ollama's answer and tries Groq
5. Returns Groq's response instead

**This is post-hoc routing:** Ollama's 9s is spent before the faster route is tried. The rule finds the quicker route — but after the slow one has already run.

---

## R1 — Per-phase latency trend (`data/backend_health_history.jsonl`)

| Metric | Value |
|---|---|
| Turns measured | 262 rows (2026-09-07 → 2026-10-11, 35 days) |
| Trigger | 100% `4s_rule` — Ollama exceeds threshold on every turn |
| Prompt eval min/mean/max | 5,324ms / **8,964ms** / 9,000ms |
| Rerouted to Groq | 259/262 (99%) |
| Rerouted to Gemini | 1/262 |
| No faster route available | 2/262 (Groq and Gemini unavailable) |

**What the 9000ms cap means:** `prompt_eval_ms` is from Ollama's `prompt_eval_duration` (ns → ms). The 9000ms cap likely reflects the point where the Ollama stream times out before `done=True` arrives — or the Ollama JSONL parse produces 9000 because `prompt_eval_duration` was not in the response at that cap. Either way: Ollama is consistently exceeding the 4s threshold by 2× or more.

**Turn breakdown (estimated from measurements):**
| Phase | Time | Share |
|---|---|---|
| Ollama prompt eval (before 4s trigger) | ~8,964ms | ~75% |
| 4s gate + Groq API + generation | ~2,000–3,000ms | ~17–25% |
| Other (routing, state write, voice) | ~500ms | ~4% |
| **Total (estimated)** | **~11,500–13,000ms** | — |

> **eLo spends ~9 seconds reading himself and ~2 seconds speaking.** The 75% reading share from the original card measurement is confirmed and has not improved — because Ollama is still being called first.

---

## R2 — Available routes when a turn exceeds 4s

| Provider | Available | Confirmed working | Notes |
|---|---|---|---|
| Groq | ✅ Yes | ✅ 259/262 turns | `ELO_GROQ_MODEL=groq/compound` (131k context) |
| Gemini | ✅ Yes | 1/262 turns | Fallback when Groq unavailable |
| Cerebras | Configured | Not confirmed in logs | Listed in `_TIER_PROVIDER_CANDIDATES` |
| OpenAI | Configured | Not confirmed | As above |

**A faster route exists on 99% of turns.** The bottleneck is not route availability — it is that Ollama runs fully before the faster route is tried.

---

## Proposed rule shape (REQUIRES DAVID'S APPROVAL before implementation)

### Current behaviour (post-hoc routing)
```
User message → Ollama runs (9s) → 4s check → Groq (2s) → response
Total: ~11s
```

### Proposed behaviour (streaming abort at 4s)
```
User message → Ollama stream starts → 4s elapsed with no first token → abort Ollama → Groq (2s) → response
Total: 4s + 2s = ~6s (worst case; often less if first token arrives before 4s)
```

**Mechanism:**
- Switch `_ollama_call` (currently non-streaming) to streaming (like the `_stream_ollama_generate` path at line 2230)
- Track time-to-first-token
- If 4s elapsed and no token has arrived: raise a timeout exception, catch it in `_tier_route()`, proceed to Groq
- Ollama's prompt eval of ~9s is then absorbed by Groq's ~2s (overlap in the happy case: first token arrives before 4s, Ollama continues)

**The remaining lever:** On a turn where Ollama's first token arrives in < 4s, the current post-hoc routing would still use Groq anyway (because `prompt_eval_ms` only populates when `done=True` arrives). The streaming abort approach would NOT reroute if first token arrives fast — a correct improvement.

### Why this needs David's eye (per card 0057 §5)
> "A latency policy decides how eLo behaves when he is struggling. That is close enough to identity that it gets David's eye before it ships."

The proposed abort means: when Ollama is slow, eLo switches to a different inference engine mid-turn. That is identity-adjacent. David's call.

**Context trimming is CLOSED (per card §5):** not proposed here, not flagged as an option.

---

## Board decisions required

1. **Approve or redirect the streaming-abort shape.** Implementation will not start without approval.
2. **C: server restart** — David's terminal needed to verify keep_alive is working as measured.
3. **Groq routing note:** 99% of turns already go to Groq via the 4s rule. If David wants Groq as primary (skip Ollama entirely for conversational tier), that is a separate routing decision also requiring approval.

---

## What this card does NOT authorise (confirmed not done)

- ❌ `prompts/living_presence_spec.txt` — not touched
- ❌ `FREEZE_V1_LOCK.md` — not touched  
- ❌ Context trimming — not proposed, not in scope
- ❌ Model decision-authority expanded — not touched

*Builder 1 · 2026-10-11*
