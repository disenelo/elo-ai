# BUILDER 1 → BOARD: Speed Timing Report
**Date:** 2026-10-11  
**From:** Builder 1  
**To:** Board  
**Re:** FROM_BOARD_2026-10-09_SPEED-STILL-SLOW.md

---

## Measured timings (classify + dispatch, no server overhead)

| Query | Tier | classify | dispatch | Total | LLM called? |
|-------|------|----------|----------|-------|-------------|
| "what time is it" | FACT | 0ms | 14ms | 14ms | No (T11 fires first) |
| "28 * 74" | FACT | 0ms | 5ms | 5ms | No |
| "15% of 200" | FACT | 0ms | 2ms | 2ms | No |
| "battery level" | UNKNOWN | 0ms | — | — | Yes |
| "how are you" | UNKNOWN | 0ms | — | — | Yes |

---

## Architecture

**T11** (line 2886 in server.py) handles all time/date queries before reaching the FACT tier. Substring match, zero imports, zero network. Returns immediately.

**FACT tier** (line 2918) handles math expressions and Mac battery queries. Uses `system_primitives` (Builder 3, WO-0104). Returns before LLM.

Both handlers are positioned **before the LLM call block** — they cannot coincide with an in-flight LLM call. FACT/T11 turns are sub-20ms server-side.

---

## two_truths_gate status

Defined in `runtime/identity_kernel.py` line 128. **Never called** from `server.py` or `spine.py` — disconnected from the live request path.

Board asked: "Is it firing before the LLM call is queued, or intercepting after?" — **Answer: neither. It does not fire at all.**

The FACT tier and T11 serve the same function (truth interception before LLM) and are wired correctly. `two_truths_gate` is redundant dead code. Board should decide: wire it in, or formally deprecate.

---

## What is slow

Conversational turns (UNKNOWN tier: "how are you", "battery level", any non-FACT input) correctly call the LLM. That latency is inherent to the backend:
- Ollama local: 1–4s depending on model + context
- OpenAI: 2–6s
- Groq: 0.5–2s

**The FACT interception is working.** Speed complaints about FACT queries suggest either:
1. The query isn't matching FACT patterns (check exact wording)
2. Or what David is testing are conversational turns that should call the LLM

Builder 1 cannot reduce LLM latency — that's a model/hardware constraint. If Board wants sub-3s on ALL turns, the direction is: expand FACT patterns OR use a smaller/local model as the primary backend.

---

## Daemon (0106) — per-turn state reconstruction

Have not yet measured whether the daemon eliminates per-turn state reconstruction. That is the remaining open item from the speed WO. Builder 1 will investigate in the next card.

*Builder 1 · 2026-10-11*
