**WO:** INTENT-FIRST-ROUTER · **Seat:** builder · **Priority:** P0 — THIS IS CARD 1, BUILD THIS FIRST
**Reserved?** no

## Goal
eLo picks the right provider before the first call goes out. No ladder. No fallback cascade. No 30-second wait on a dead local model. "What time is it" answers in under 2 seconds.

## What exists and must be replaced
`backend_router.py` currently runs a sequential ladder: try Ollama → wait → fail → try Groq → wait → fail → try Cerebras. Every turn pays the cost of every failed rung. With Ollama not running, every response costs 8–30 seconds of silence before a real model answers. This is not a tier system. It is a ladder and it must go.

## The replacement — intent-first routing
1. Read the intent from the turn (already classified by `intent_engine.py` — `action`, `conversational`, `build`, `reflect`, etc.)
2. Map intent → provider directly:
   - `conversational` / `time` / `factual` / `lookup` → Groq (fast, cheap, always first)
   - `build` / `reflect` / `plan` / `challenge` → best available reasoning model
   - `local_only` → Ollama only (and if Ollama is down, say so immediately — do not cascade)
3. Check provider health ONCE at startup (not per turn). Mark dead providers as unavailable. Skip them — do not attempt and wait for timeout.
4. If the chosen provider fails: ONE retry on the next tier. Log it. Do not silently cascade through every provider.

## The timeout problem
`ELO_OLLAMA_TIMEOUT_S=180` and `ELO_BACKEND=local` with Ollama not running = every turn stalls 8+ seconds minimum. Fix: health check on boot, skip dead providers instantly, do not wait per-turn.

## Files to touch
`runtime/backend_router.py` · `runtime/spine/spine.py` (where provider is selected per turn)

## Test
Response time for "what time is it" must be under 3 seconds. Measure before and after.
`python3 -m pytest tests/ -k "router or backend or latency" -v`

## Done when
"What time is it" answers in under 3 seconds. No ladder. Provider chosen from intent before first call. Test green. Committed.

## Live turn needed
> David says to eLo: "What time is it?"
> eLo responds in under 3 seconds with the correct time.

## Result
- commit:
- test:
- notes:
