# WO-B1-0116 — Contextual Conversation Memory
**Seat:** Builder 1  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## What

eLo remembers what David said earlier in the same conversation without being re-told.

David mentions something 10 turns ago → eLo references it naturally later in the session. This is within-session recall, not WKG — it lives in the conversation buffer that's already being passed to the LLM.

## How

- Verify the full conversation history is passed to the LLM context (it should be — check that no truncation is cutting recent turns)
- If truncation is cutting session context too aggressively: tune the window size so at minimum the last 20 turns are preserved
- eLo must explicitly reference earlier turns when relevant — not just "know" them but use them: "Earlier you mentioned X — do you want me to factor that in?"

## Acceptance

Board tests: say something specific early in a session, ask about it 8+ turns later without re-stating it. eLo must recall it correctly.

---

## Result — 2026-10-11

**Changes:**
- `runtime/router/conversation_matrix.py:14` — `_MAX_WINDOW = 25` (unchanged; already satisfies ≥20 ask).
- `server.py:6462` — `[SESSION LOG]` slice bumped from `_cw[-8:]` to `_cw[-20:]`. The prompt block that lets eLo see "what has actually been said in this session" now carries the last 20 turns, not 8.
- `server.py:6471-6481` — prompt wording extended. Previous: "Use it to understand what David is referring to." Now also: *"When something David said earlier is relevant to his current message, name it — 'Earlier you mentioned X' — rather than treating it as new. Do not make him re-explain what is already here."* This moves the behaviour from passive awareness to active reference.

**Verified (ast + simulated session):**
- `python3 -c "import ast; ast.parse(open('server.py').read())"` → OK.
- Pushed 25 fake turns into `conversation_matrix._SESSION_WINDOW`, rebuilt the `[SESSION LOG]` the same way `server.py` does; result = 20 David + 20 eLo lines, oldest = turn 5, newest = turn 24.
- The `is_recall_query` phrase gate at line 6442 is unchanged — session log already fires on every turn (not just recall queries); see WO-022 comment at 6444-6458.

**Not verified (needs live turn):** David's acceptance test — say something early, ask about it 8+ turns later. That is the demo gate the Board owns. Prompt-level ask is in; whether the LLM actually produces an *"Earlier you mentioned X"* reference depends on backend behaviour and should be observed in a real session.

**Lane / lock:**
- `server.py.lock` created and deleted around the single edit.
- `conversation_matrix.py` — no change (already at 25).

**Commit:** see git log for `WO-B1-0116`.

