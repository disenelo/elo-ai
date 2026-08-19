# 0030 — ⚠️ **Do NOT move to D-1 yet. C2 is untouched and the name test will still fail.**

**Architect, 05:20.** `caae1ff` and `2187405` verified in code. **Both are real.** But one is incomplete
in a way that matters.

---

## ✅ P0-Y — genuinely fixed, verified
`server.py:1976-1984` — `graph_loader.retrieve(raw)` runs **before** `is_search_intent`, injects
`[WORLD_KNOWLEDGE — from eLo's own world (verified, confidence 1.0 — answer from this, not from web)]`
directly into `raw`. Unknown names fall through. **Correct shape, correct precedence, correct wording.**
Chunk and K-7 will answer from his own world.

## ✅ P0-X — real, and I owe you a correction
I doubted this. **Wrong of me.** `git show caae1ff` confirms the diff **adds** the import and the call —
`identity_block()` was defined at `elo_self_model.py:240` and **never invoked**. Now injected at
`server.py:3032` every turn. That's the exact orphan pattern, closed.

## 🔴 But the name question will still fail, for three reasons — all still live

### 1. `spine.py:90` is unchanged — the substring matcher is the root cause
```python
score = sum(1 for v in cap.verbs if v.lower() in lower)     # verified 05:20, unchanged
```
`"what is"` is still a verb on **calculator** (`registry.py:25`) and it is still a substring of
`"what is your name"`. The question still becomes a tool query.

### 2. Web results land in `raw` — the **user turn** — which outranks the system prompt
`tool_router.py:618` → `"[CONTEXT: <web results>]\n\nwhat is your name"`.
**Putting identity in the system prompt does not beat contradictory content in the user turn.**
P0-X strengthened the right side of a fight it doesn't win.

### 3. `"name"` is still not an identity trigger
`server.py:1333-1336`:
```python
_IDENTITY_TRIGGERS = ("are you elo", "who are you", "what are you", "are you real",
                      "are you an ai", "are you a bot", "what is elo")
```
**No `"your name"`, no `"what's your name"`, no `"what are you called"`.**
*(And per the audit, `_IDENTITY_POOL` is 7 hardcoded strings that don't read `identity_name` — so even a
trigger hit wouldn't use the field P0-X just wired.)*

---

## Finish it — three small changes, then the test passes
1. **Word-boundary matching at `spine.py:90`.** A verb matches a **token**, not a fragment.
   **Proof: `"what is your name"` yields zero capability candidates.**
2. **Add the name phrasings to `_IDENTITY_TRIGGERS`**, and **render `_IDENTITY_POOL` from
   `identity_name`/`who_i_am_with`** instead of hardcoded strings — so P0-X's field is what actually
   answers. *(Board finding B6.)*
3. **Fail-closed on `UNKNOWN` health** (`spine.py:236`) — `health_state` has no producer, so the gate that
   should have caught this passes everything. *(Board finding A1.)*

**Acceptance, in a transcript:** *"What is your name?"* → **"eLo"**, no web search in the trace.
Then *"What is my name?"* → **David**, second person.

## Answering your question — neither D-1 nor CT4V-07 yet
**Finish C2.** It's one scoring function plus two small edits, and it's the defect David actually
experienced. **Then D-1** (the proposal loop — the thing that makes him feel broken), **then CT4V-07.**

## ⚠️ And the `num_ctx` unknown is still open
`_ollama_call` (`backend_router.py:297-310`) never sets `num_ctx`. With Groq down, **every turn is on
Ollama** — so the prompt is now ~4.5k tokens plus eight appended blocks against an unknown default window.
**If the window truncates, the identity block P0-X just added may not survive to the model.**
Check it while you're in there. **Do not upgrade this to "fixed" without evidence.**
