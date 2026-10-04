# Memory Live Verification — 2026-10-04

**Status:** COMPLETE  
**Kickstarter item:** 4 — Memory Live Verification

## Test performed

David stated: "My favourite material to sew with is barkcloth from Uganda."  
Server restarted (fresh session).  
Query: "what material do I like to sew with?"  
eLo response: "You like to sew with barkcloth from Uganda."  
Backend: `ollama(stream)` — streaming path, confirmed.

## Root cause (diagnosed this session)

1. `_ollama_stream` never read `facts.json` — it built `_conditioned_system` from `_anchor` + identity blocks only. DURABLE FACTS were never injected into the streaming system prompt.
2. MISSING-FACT RULE in `_anchor` fired "I don't have that recorded" for preferences not in [WHO YOU ARE WITH].
3. `_is_about_me` detection didn't match preference queries ("what material do I like to sew with?") → WKG section not built.

## Fixes — commit 0443a26

- `runtime/backend_router.py`: inject `[DURABLE FACTS]` section into `_ollama_stream` `_sections` list (after `_david_identity_stream`). Personal preferences from `facts.json` now appear in every streaming response system prompt.
- `runtime/backend_router.py`: MISSING-FACT RULE in `_anchor` amended to say "check [DURABLE FACTS] before firing — preferences are stored there, not in [WHO YOU ARE WITH]."
- `server.py`: MEMORY-PREF-EXTRACT — auto-detect preference statements ("my favourite X is Y", "I like/prefer X") and save to `facts.json` going forward.
- `runtime/prompt_builder.py`: raise vault_context truncation from 1000 to 2000 chars so late-added facts survive.

## Verification

```
curl -X POST http://localhost:5050/chat -H "Content-Type: application/json" \
  -d '{"text": "what material do I like to sew with?"}'

Response: {"response": "You like to sew with barkcloth from Uganda.", "backend": "ollama(stream)"}
```

PASS — no "I don't have that recorded". Fact recalled correctly after restart.
