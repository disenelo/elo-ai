# Result Card — FROM_ARCHITECT_2026-10-06_B3-BOARD-RULINGS
**Builder:** Builder 1
**Date:** 2026-10-06
**Commit:** 2dec359
**Status:** COMPLETE — Issues 3, 4, 5, 6, 7 resolved

---

## Issue 5 — Identity drift suffix removed — FIXED

`server.py` ~line 8033: `response = response.rstrip() + _dg_suffix` was appending "— [I'm eLo: calm, observant, playful]" to the outgoing response every time identity drift fired. This reached David's chat and TTS.

Fix: removed the response mutation entirely. Correction store + inner_event remain as the silent corrective action. Nothing is appended to outgoing text.

---

## Issue 3 — graph_loader.py word-boundary fix — FIXED

`knowledge/graph_loader.py`: added `_kw_match(keyword, text_lower)` helper using `re.search(r"\b" + re.escape(keyword) + r"\b", text_lower)`. Replaced bare `k in t` at two sites:
- `_find_entities()` score sum (line 183)
- `retrieve()` kw_score sum (line 255)

Now "ai" only matches as a standalone word, not inside "brain", "again", "said".

---

## Issue 6 — MISSING-FACT RULE exempted on injected context — FIXED

`runtime/backend_router.py` system prompt: added EXCEPTION clause to MISSING-FACT RULE. When user message contains `[WEB_SEARCH:`, `[WORLD_`, `[CAPABILITY_RESULT:`, or `[POP_CULTURE_CONTEXT:` — real information was injected and the missing-fact rule is wrong to fire. LLM now told to use the injected content instead.

---

## Issue 4 — voice_rewrite no longer uses mock backend — FIXED

`server.py` ~line 7189:
1. `_vr_skip` extended from `== "direct:web_search"` to `.startswith("direct:")`. All direct backends (time, calculator, vault-daily, etc.) are now exempt from voice_rewrite.
2. `_vr_llm()` now checks `_vr_backend == "mock"` after `router_route`. If mock was returned (all live providers exhausted), the original user message is returned unchanged — never a canned mock rewrite. The raw response is always better than mock filler.

---

## Issue 7 — e704c53 garble fix covers both B3 cases — CONFIRMED

Live test:
```
"Same thing as always Pinkie try to take over the world"  → n_garbled=2 < 3 → frustrated=False ✓
"You'd have to do a websearch to read up about it"        → n_garbled=1 < 3 → frustrated=False ✓
```

Both sentences stay below the threshold raised in e704c53. No additional fix required.

---

## Files changed

| File | Change |
|---|---|
| `server.py` | Identity drift suffix removed (~line 8033); `_vr_skip` extended; `_vr_llm` mock guard |
| `knowledge/graph_loader.py` | `_kw_match()` helper; two `k in t` → `_kw_match()` |
| `runtime/backend_router.py` | MISSING-FACT RULE EXCEPTION clause for injected context |

Builder 1 · 2026-10-06
