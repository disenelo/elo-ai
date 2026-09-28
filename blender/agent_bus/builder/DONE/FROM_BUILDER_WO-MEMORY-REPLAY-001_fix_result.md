# BUILDER RESULT — WO-MEMORY-REPLAY-001: Memory Replay Fix
Date: 2026-09-11
Status: DONE — write path and retrieval path fixed; live verified 2/2

---

## Bug summary

`memory/interactions.json` records were storing pipeline-enriched `raw` in the `user` field
instead of David's actual words. When the world_graph_gate fires at server.py:2548, it sets:

```python
raw = f"[WORLD_KNOWLEDGE — from eLo's own world (verified, confidence 1.0 — answer from this, not from web)]\n"
      + "\n".join(_g_ctx_lines) + f"\n\nUser asked: {raw}"
```

The subsequent `_write_interaction(raw, response, ...)` call at line 4736 then stored the
entire enriched string as the `user` field. On retrieval, the system prompt injection at
line 4423 would surface this as "David: '[WORLD_KNOWLEDGE...]'" — the LLM would then
echo the world knowledge context as eLo's current response.

Root cause: identical to the F-5 bug already fixed for `state_manager.update` (line 5218).
Both used `raw` where `_original_raw` was correct. `_original_raw` is captured at line 2086
before any enrichment.

---

## Fix 1 — Write path (server.py:4736)

```python
# Before:
_write_interaction(raw, response, _mem_cats, mode=_action, project_tag=_mem_project_tag)

# After (WO-MEMORY-REPLAY-001):
_write_interaction(_original_raw, response, _mem_cats, mode=_action, project_tag=_mem_project_tag)
```

`_original_raw` = David's actual words, captured before world_graph_gate, file_agent,
image_gen or any other enrichment prefixes `raw`.

---

## Fix 2 — Retrieval read path (server.py:4423-4431)

Two changes:
1. Filter out any previously-contaminated records (where `user` starts with `[WORLD_KNOWLEDGE`
   or `[FILE_AGENT_RESULT]`) from the retrieval injection.
2. Tighten the system prompt instruction from "Use the actual words above — do not paraphrase
   into a mood gloss" (which told the LLM to echo David's words) to:
   "These are David's past words for memory context — do not repeat or echo them as eLo's
   current response."

```python
# Before:
_raw_lines = [
    f"- [{r.get('timestamp','')[:10]}] David: {r.get('user','')[:120]!r}"
    for r in _raw_hits if r.get("user")
]
if _raw_lines:
    system = system + (
        "\n\n[RECENT INTERACTIONS — concrete turns]\n"
        + "\n".join(_raw_lines)
        + "\n\nUse the actual words above — do not paraphrase into a mood gloss."
    )

# After (WO-MEMORY-REPLAY-001):
_raw_lines = [
    f"- [{r.get('timestamp','')[:10]}] David: {r.get('user','')[:120]!r}"
    for r in _raw_hits
    if r.get("user") and not r["user"].startswith(("[WORLD_KNOWLEDGE", "[FILE_AGENT_RESULT]"))
]
if _raw_lines:
    system = system + (
        "\n\n[RECENT INTERACTIONS — David's past inputs for context]\n"
        + "\n".join(_raw_lines)
        + "\n\nThese are David's past words for memory context — do not repeat or echo them as eLo's current response."
    )
```

---

## Live verification (real server, port 5050, no preloaded Faculties)

```
interactions before: 1117

Turn 1:
IN:  'i want to build something great with elo, its my dream project'
OUT: "I'm curious about the emotional world you're envisioning."
WRITE: user='i want to build something great with elo, its my dream project' → PASS

Turn 2 (world_graph_gate fires — raw was enriched with [WORLD_KNOWLEDGE...] prefix):
IN:  'who are the enemies in elo planet'
OUT: "Amber \nEnemies in the eLo universe are actually Corrective Elements..."
WRITE: user='who are the enemies in elo planet' → PASS

interactions after: 1119
New records written: 2
Overall: PASS — _original_raw stored in both turns
```

Turn 2 is the key check: world_graph_gate enriched `raw` with `[WORLD_KNOWLEDGE...]`,
but `_original_raw` was used, so the stored record contains David's clean question.

---

## Contaminated records (pre-fix)

Records written before this fix with `[WORLD_KNOWLEDGE...]` or similar in the `user` field
remain in `interactions.json`. The read-path filter (Fix 2) prevents them from being
injected into the system prompt on retrieval. No records deleted (append-only rule).

Board may choose to purge or re-label contaminated records in a future cleanup pass.

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |

— Builder · 2026-09-11
