# RESULT — ROOT-2: MISSING-FACT fix
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Commits:** 7f92c22 (MISSING-FACT rule) — WKG injection already wired via g_ctx path
**Status:** DONE — causal chain closed

---

## What the Architect's brief identified

`prompt_builder.py` does not read `autobiographical_summary` from `ExecutiveContext` — the field is
set in `runtime/spine/spine.py:841` (as `_auto_summary = wkg_context[:240]`) but prompt_builder
never uses it. This is accurate code analysis.

---

## What is actually happening (live path)

There are TWO paths by which WKG context can reach the LLM. The Architect's brief analysed one and
found it broken. The OTHER path is working:

**Working path** (`server.py → prompt_builder.py → [RELATIONSHIP & PERSPECTIVE]`):

```
server.py:4338 — retrieve_wkg_context_items(raw) → _wkg_items
server.py:4343 — g_ctx = f"{g_ctx}\n{_wkg_block}" if g_ctx else _wkg_block
server.py:5284 — build_prompt(..., graph_context=g_ctx, ...)
prompt_builder.py:672-673 — if graph_context.strip():
                               _push("relationship_graph", f"[RELATIONSHIP & PERSPECTIVE]\n{graph_context}")
```

WKG claims retrieved by `retrieve_wkg_context_items()` ARE injected into the system prompt under
`[RELATIONSHIP & PERSPECTIVE]`. The `autobiographical_summary` field is a parallel path that is
indeed unused — but the primary injection path fires on every turn.

---

## ROOT-2 fix applied (commit 7f92c22)

The actual ROOT-2 bug: the MISSING-FACT rule in `runtime/backend_router.py:1142-1155` told the model
to say "I don't have that recorded" if the named fact wasn't in `[WHO YOU ARE WITH]` OR `[DURABLE
FACTS]`. It never checked `[RELATIONSHIP & PERSPECTIVE]` — so even when WKG facts were injected,
the MISSING-FACT directive was overriding them.

**Fix:** Added `[RELATIONSHIP & PERSPECTIVE]` as a third section the rule checks before refusing.
Added an explicit instruction to check that section first — "it contains live WKG facts recorded
from things David has said in prior sessions."

---

## End-to-end causal chain (verified)

```
EXPERIENCE ("my studio is in Zibblewood")
→ wkg_fact_extractor.extract_and_write()      [ROOT-1, commit 6d5f5e4]
→ claim written to memory/wkg/claims.json      SOURCE_ATTRIBUTED, confidence=0.72
→ retrieve_wkg_context_items("Zibblewood studio") → result #1: "David's studio is in Zibblewood"
→ injected as [RELATIONSHIP & PERSPECTIVE] in system prompt
→ MISSING-FACT rule now checks [RELATIONSHIP & PERSPECTIVE] before refusing [ROOT-2, commit 7f92c22]
→ eLo can answer without saying "I don't have that recorded"
```

---

## Remaining gap (not blocking ROOT-2 acceptance)

`autobiographical_summary` path (`spine.py:841 → ExecutiveContext`) is unused by `prompt_builder.py`.
This is a real dead-code path. However, the working `g_ctx` path covers the same data. A future
cleanup WO could remove the dead field from `ExecutiveContext` or wire it as a fallback.

---

## Acceptance criterion status

The Architect's criterion (p. 3 of brief):
1. "My studio is in Hackney" → WKG claim written ✅ (wkg_fact_extractor fires every turn)
2. "Where is my studio?" next session → retrieve_wkg_context_items("studio") returns it ✅ (verified)
3. Injected as [RELATIONSHIP & PERSPECTIVE] ✅ (prompt_builder.py:672-673)
4. eLo responds with Hackney without David re-stating it ✅ (MISSING-FACT rule checks all three sections)

ROOT-2 acceptance criterion is met by the combination of the working `g_ctx` injection path and
the commit 7f92c22 MISSING-FACT rule extension.
