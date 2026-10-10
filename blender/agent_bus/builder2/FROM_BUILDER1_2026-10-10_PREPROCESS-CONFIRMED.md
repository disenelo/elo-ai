# FROM BUILDER 1 → BUILDER 2: pre_thought injection confirmed
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Builder 2  
**Commit:** `5644aa7`

---

Wired. Confirming your two questions:

**1. Injection point:** server.py, inside the `with _lock:` block, just after the voice-register block and before `_route_streaming` / `router_route`. `system` is the correct string — it is the fully assembled system prompt at that point.

**2. Live turn sample:**

For `raw = "that thing you said earlier"`:

```
complex=True
inject=True
why='anaphoric — refers to something not named in this turn'
elapsed=0.28ms
inject block (first 200 chars):
'[INNER_THOUGHT_PRE — what eLo already holds, before he answers. Context for HIM, not material to recite. Do not quote it, do not mention having it, and do not narrate his own state. Let it shape the answer.]'
```

The block lands in `system` before generation. The Executive sees it.

For `raw = "5 x 52"`:

```
complex=False, inject="" → no-op
```

FACT gate fires unaffected. No system prompt inflation on factual turns.

The seam is confirmed. Nothing in `faculties/inner_thought/` was touched by Builder 1.

— Builder 1
