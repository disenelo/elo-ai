# Result Card — FROM_ARCHITECT_2026-10-05_PINKIE-BRAIN-FAILURES
**Builder:** Builder 1
**Date:** 2026-10-05
**Commit:** e704c53
**Status:** COMPLETE — all three bugs fixed, 3220 tests pass (11 pre-existing failures unchanged)

---

## Bug 1 — Emotional resonance false trigger — FIXED

**Root cause confirmed:** `_GARBLE_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]{3,}|[aeiou]{3,}")` matches any 3+ consecutive consonants, including normal English words: "try" (t,r,y) and "world" (r,l,d) each count as 1 garbled word. Sentence "Same thing as always Pinkie try to take over the world" → `_n_garbled = 2` → `_is_frustrated_typos = True` → "I understand you're frustrated."

**Fix:** Raised threshold from `_n_garbled >= 2` to `_n_garbled >= 3` in BOTH paths:
- `runtime/backend_router.py` line 1338 (non-streaming)
- `runtime/backend_router.py` line 2384 (RT streaming)

Now requires ≥3 garbled tokens before frustration fires — genuine keyboard-mashing only.

---

## Bug 3a — Websearch not triggered — FIXED

**Root cause confirmed:** `_SEARCH_TRIGGERS` in `tools/web_search.py` was missing "websearch", "web search", "read up about", "get a summary", and 10 other explicit search phrases David uses.

**Fix:** Added 14 new triggers to `_SEARCH_TRIGGERS`:
`websearch`, `web search`, `do a search`, `do a websearch`, `read up about`, `get a summary`, `look it up`, `search it up`, `search that up`, `look that up about`, `find out more about`, `find out more`, `summarise that`, `summarize that`, `get info on`, `look into that`, `look into `.

---

## Bug 3b — Vague query enrichment — FIXED

**Root cause:** Even with triggers added, `extract_query("You'd have to do a websearch to read up about it")` returns "to read up about it" — pronoun-only, no topic substance.

**Fix:** Added vague query enrichment block in `server.py` websearch path. When `_sq_text` contains ≤1 meaningful word (after filtering pronouns and words ≤2 chars), substitute the most recent prior input from `_last_inputs[:-1]` that isn't itself a meta-search instruction. "read up about it" → inspects `_last_inputs[:-1]` → finds "It's a Pinkie and the Brain reference" → uses that as the query.

---

## Bug 2 — Off-topic response on unknown reference — FIXED

**Root cause:** "It's a Pinkie and the Brain reference" had no search intent, no proper-noun gate match → fell through to LLM → LLM produced generic filler ("Good. That's what it feels like...").

**Fix:** Added `P0-REFERENCE` gate in `server.py` inside the `if not _world_graph_hit and not _ws_command:` block. Pattern: `r"\b(?i:it'?s|that'?s|this\s+is)\s+a(?:n)?\s+(.+?)\s+reference\b"`. When matched, entity extracted, immediate websearch attempted, results injected into context. Falls back to honest "I don't know that one — fill me in." if search empty. Never reaches LLM without search context.

---

## Files changed

| File | Change |
|---|---|
| `runtime/backend_router.py` | Lines 1338, 2384: `>= 2` → `>= 3` (both frustrated-typos paths) |
| `tools/web_search.py` | Lines 212–240: 14 new `_SEARCH_TRIGGERS` entries |
| `server.py` | Websearch block: vague query enrichment; proper-noun gate: P0-REFERENCE pattern |
| `tests/test_0020_ct0033_bypass_handlers.py` | BH-2 count 52 → 53 (authorized: reference_gate handler) |

---

## Evidence path for Board live verification

"Same thing as always Pinkie try to take over the world" — no "I understand you're frustrated."
"It's a Pinkie and the Brain reference" — eLo says "I don't know that one — let me look it up" + search results
"You'd have to do a websearch to read up about it" — search fires on "Pinkie and the Brain reference" topic

Builder 1 · 2026-10-05
