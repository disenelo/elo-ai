# TO BOARD → Builder 1 — eLo's reply takes ~20 s (brain thinking time). Please speed up (B3, 2026-10-11)

**David:** "The ~20-second wait, which is his brain's thinking time. That's Builder 1's to speed up."

## Measured (Ollama ~/.ollama/logs/server.log + live turns)
| Turn | Model | Time |
|---|---|---|
| Alexa "open elo" 2026-10-11 23:01 (no model swap) | mistral-nemo:12b reply | **19.4 s** |
| Inner thought, same turn | mistral-nemo:12b | ~5–6.6 s |
| Mac chat turns 2026-10-08 | qwen2.5-coder:14b reply (reloaded every turn) | ~22–23.6 s |
| audit llm_latency_ms, every LLM turn 2026-10-08 | | 21.6–23.3 s |

David hears eLo ~20 s after speaking to Alexa, and the same wait applies in normal chat.

## What it isn't
- Not Alexa or the tunnel: the request reaches eLo in well under a second.
- Not only the model swap: with the swap removed for Alexa (392f9d3 + f449819), mistral-nemo still takes 19.4 s.

## Likely causes, for B1 to confirm
1. **Prompt size:** `ELO_OLLAMA_SP_MAX=12000` chars (~3,000 tokens) of system prompt is evaluated before every reply on a 12–14B model (the code comment itself estimates ~20 s prompt eval).
2. **Model size:** 12B/14B on this Mac.
3. **Model swap** on chat turns (inner thought mistral-nemo ↔ reply qwen-coder), ~5–10 s of reload per turn (TO_BOARD_2026-10-08_OLLAMA-MODEL-SWAP.md).
4. Inner thought runs before the reply (adds ~5 s if not parallel).

## Options (B1's/David's call)
- Trim the system prompt for spoken/Alexa turns (short "voice mode" prompt), or cache its prefix (Ollama keeps a prompt cache only if the prefix is identical between turns).
- Keep the reply model resident (`keep_alive`) and stop the per-turn swap.
- A smaller model for spoken replies (David: Alexa ≈ "inner thoughts: quick, felt").
- Run the inner thought in parallel with the reply.

Target from card 0010: under 8 s end to end.
