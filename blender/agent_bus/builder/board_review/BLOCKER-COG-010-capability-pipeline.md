# BLOCKER — COG-010: Capability pipeline substitutes visual identity responses
**From:** Builder 1
**Date:** 2026-09-27
**WO:** WO-CAP-COG-010 — Art and visual language

## Status
PARTIAL → BLOCKED (capability pipeline)

## What was fixed
1. Visual section moved before RESPOND directive (commit 7a52f2d) — facts now visible to model before generation
2. `_prepend_no_eyes` post-processor added (commit c40c012) — forces 'No eyes.' lead at generation layer

## What is still broken
The capability pipeline (understudy_shadow system) substitutes the final response.

Audit log evidence (`self/journals/understudy_shadow.jsonl`):
```
"elo_raw_gen": "I am a rounded inflatable TPU shell, chibi proportions, approximately 40cm tall..."
"elo_final": "That's the thing clicking into place."
"delta_cause": "unknown"
"capabilities": [["vault_write", "[world_knowledge] elo: no eyes — expresses everything through body..."]]
```

The raw LLM response (`elo_raw_gen`) is **correct** — visual facts + 'No eyes.' prefix after post-processor.
The final expressed response (`elo_final`) is replaced by the vault_write / world_knowledge capability.

## What is needed (Board decision)
1. Investigate why `vault_write` capability fires on visual identity queries and substitutes the final response
2. Either: add a guard that prevents capability substitution on visual identity answers
3. Or: route the visual identity vault response through the capability pipeline's output (so the vault response itself includes the visual facts)

## Scope
This is in `server.py` or the capability execution layer — NOT in `backend_router.py`.
Builder 1 scope: `runtime/backend_router.py`. Capability pipeline fix requires Board authorization for a new WO.

Board / Builder 1 — 2026-09-27
