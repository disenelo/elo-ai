---
id: WO-043
title: "Faculty Bus isolation — stop prompt/routing contamination leaking foreign snippets into generation."
owner_seat: SEAT-ENG-001 (Builder / eLo OS — Faculty Bus)
priority: P0
review_required: David — no unrelated content appears in replies
status: OPEN — Chief Architect diagnosis 2026-08-03
epic: "Executive Authority" (root of WO-039 garble — WO-039 is the symptom)
---
# WO-043 — bus isolation / no contamination
## The bug (Chief Architect)
Snippets that don't belong to the conversation appear: "quit is?", a preposition/grammar answer,
"Shall I quit means?". This is NOT hallucination — it's a foreign prompt leaking into generation.
Suspects: conversation-buffer corruption, wrong prompt selected, faculty routing, vector-retrieval
mismatch, memory contamination, conversation splice.
## Fix (Builder Faculty Bus)
- Isolate per-faculty context on the bus so one faculty's prompt/example/retrieval can't splice into
  another's generation. Add a contamination guard: reject/scrub content whose source ≠ the current
  conversation. (WO-039 covers the `quit`-keyword coercion; this covers the leak channel itself.)
## Acceptance
1. Replies contain only conversation-sourced content. 2. No leaked example/grammar/command text.

---
## CONFIRMED LEAK CHANNEL (David's hypothesis, grounded 2026-08-03) — the "37°C" injection
David: "something is leaking through and not being processed via eLo's executive."
He is RIGHT, and here is the exact channel:
- `server.py` ~621-686 builds `_ambient_fact_ctx` and injects it into the system prompt EVERY turn:
  `"FACT AVAILABLE (use it naturally in speak if the moment feels right...): {fact}"`.
- So an AMBIENT weather fact (a broad area forecast, e.g. 37°C) is handed to the model with a
  "weave it in if it fits" instruction — with **NO executive gate** deciding whether it is TRUE for
  what David actually said ("it feels hot in my studio" ≠ "what's the area forecast") or RELEVANT.
- On the intended primary model this mostly behaved. On the **backup model (Cerebras, WO-032)** it
  FUSES the injected fact + David's emotional line into an ungrounded assertion ("it's 37° in your
  studio"), then defends it. Same mechanism drives the "I notice…" rambles: many injection points
  (ambient_fact, web_search, screen, relationship, project, entity) each hand context to the model
  with no single executive arbitration → the weaker model surfaces all of it as noise.

**This is precisely the ADR-Exec-002 violation** (a faculty injecting private state that the Executive
never arbitrated into one truth) + ADR-Exec-001 (asserting unverified state — "37° in your studio").
FIX (Builder): injected facts/tool outputs must pass through the Executive, which decides relevance +
truth BEFORE they can reach speech; nothing is "woven in if it fits." One arbitrated truth → speak.
This is the ROOT of the "eLo doesn't sound like eLo" regression, compounded by the backup model.

---
## CONCRETE INSTANCE — `[WEB_SEARCH:]` marker leaks into the reply (David live 2026-08-05)
eLo prints `[WEB SEARCH:]` in its user-facing reply. Mechanic: on search intent (server.py:1752), the
tool runs and PREPENDS `[WEB_SEARCH: {query}]\n{results}\n\nUser asked: {raw}` into the prompt as
context (server.py:1766). The model — especially the Groq/backup — **echoes the control marker** into
its output instead of silently using the results. So the search result does NOT flow cleanly through
the spine → reply; the raw injection token leaks. Same leak channel as the ambient-fact "37°C" case.

**Fix — two layers:**
1. **Tactical guard (quick, Builder):** strip ANY control/injection markers (`[WEB_SEARCH...]`,
   `[WEB_SEARCH_RESULTS]`, `User asked:`, ambient-fact tags) from the final user-facing reply — a hard
   post-generation scrub. A control token must never reach the user.
2. **Proper fix = WO-050:** search routes through the spine → search faculty → Executive assembles a
   clean reply with the result integrated. The marker stays an INTERNAL control token, never in output.
   (David's "flow through the spine to the reply" — this is exactly it.)

David's diagnosis confirmed: the search info is NOT flowing through the spine to the reply — the marker
is escaping. Validates WO-050.
