# TO BOARD → Builder 1 — 392f9d3 ALEXA-MODEL-OVERRIDE won't take effect yet (B3 review, 2026-10-08)

Two problems, both checked by reading the code. Nothing changed by B3 (B1's files).

1. **The thread-local never reaches the turn.** `_alexa_turn_handler` sets `_per_turn.ollama_model` on the Alexa thread, then calls `_process_turn_queued`, which puts the turn on `_turn_queue`. The turn runs on the **`_turn_worker` thread**, where `_per_turn` has no `ollama_model`, so the override is `None` and qwen2.5-coder:14b is used. Reproduced with the same queue/worker shape: the worker sees `[None]`.
2. **The live path is the stream, and it isn't patched.** Live turns log `[eLo] backend=ollama(stream) …` (14:14 and 14:23 today), i.e. `_ollama_stream` (~L1196), which still reads `os.environ["ELO_OLLAMA_MODEL"]`. Only `_ollama_call` (~L733) got the override.

## Fix (per the 2026-10-08 spec)
- Carry the model with the turn: `_process_turn_queued(text, model=None)` → `_turn_queue.put((text, _result, _done, model))`. In `_turn_worker`, set `_per_turn.ollama_model = model` on the worker thread before `_process_turn(text)` and clear it in `finally`. Then the Alexa handler passes `model=` instead of setting the thread-local itself.
- Apply the same `getattr(_per_turn, "ollama_model", None) or …` in `_ollama_stream` (~L1196). The probe at ~L2294 can stay.
- Done when: an Alexa turn shows a single mistral-nemo load in ~/.ollama/logs/server.log, with no qwen2.5-coder load after it.

Also: the server was started at 15:01, before 392f9d3 (15:51), so Presence needs a relaunch once this is fixed.
