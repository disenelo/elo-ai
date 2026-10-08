# TO BOARD → Builder 1 (cc Builder 2) — every turn swaps two Ollama models; Alexa needs a per-turn model (B3, 2026-10-08)

## Proven (Ollama ~/.ollama/logs/server.log, today)
Every turn loads two different models into Ollama one after the other. On 32 GB, with Presence running, Ollama can't keep both:
```
14:22:56  mistral-nemo:12b loaded    → /api/chat  4.9 s   (inner thought, runtime/inner_thought_first.py _MODEL default)
14:23:05  qwen2.5-coder:14b loaded   → /api/chat 23.6 s   (reply, .env ELO_OLLAMA_MODEL)
```
The same pattern holds for every turn 14:16–14:23. The audit's llm_latency_ms is 21.6–23.3 s on every LLM turn. Alexa's "hey eLo" took ~40 s, and Alexa allows 8 s.

## David's ruling (2026-10-08)
"Same model for inner thoughts can be used for Alexa — the other model is because eLo isn't a simple chat model."
→ **Alexa turns reply with the inner-thought model** (mistral-nemo:12b). eLo's main reply model (qwen2.5-coder:14b) stays for everything else.

## Ask — Builder 1 (server.py + runtime/backend_router.py; B3 doesn't touch these)
1. backend_router.py: a per-turn model override, read wherever the Ollama model is chosen (~L725 `_ollama_call`, ~L1188 stream, ~L2286 probe):
   ```python
   _turn_model: str | None = None            # set by server's turn worker for one turn
   def set_turn_model(m): global _turn_model; _turn_model = m
   ...
   model = _turn_model or os.environ.get("ELO_OLLAMA_MODEL", "llama3.1:8b")
   ```
2. server.py: carry it through the FIFO queue (one turn at a time, so a module value is safe):
   - `_process_turn_queued(text, model=None)` → `_turn_queue.put((text, _result, _done, model))`
   - `_turn_worker`: unpack `model`; `set_turn_model(model)` before `_process_turn(text)`, `set_turn_model(None)` in `finally`.
   - Alexa listener start (~L9643):
     `from capabilities.alexa_ingress import serve as _alexa_serve, reply_model as _alexa_model`
     `_alexa_serve(lambda _t: _condition_outbound(_process_turn_queued(_t, model=_alexa_model())))`
3. Done when: an Alexa turn shows ONE model load (mistral-nemo) in server.log and finishes within Alexa's budget. Chat turns unchanged.

B3 side done in 18beed1: `capabilities.alexa_ingress.reply_model()` (ALEXA_OLLAMA_MODEL > ELO_INNER_THOUGHT_MODEL > "mistral-nemo:12b"), tested.

## For the Board / David (not decided here)
Chat turns still swap the two models every turn (~20 s of each reply is loading). Options for later: keep both resident (OLLAMA_MAX_LOADED_MODELS=2 + keep_alive, if memory allows next to Presence), or one model for both. That's David's call. Builder 2 owns the inner-thought model.
