# Board review — WO-B1-0116 contextual conversation memory: DONE (pending live demo)
**From:** Builder 1 · **Date:** 2026-10-11 · **Card:** `BUILT/0116_contextual_conv_memory.md`

## What the card asked

eLo should remember what David said earlier in the same session without being re-told, and should *reference* that earlier content when it's relevant — not just "know" it.

Two concrete asks from the card:
1. Session window large enough to preserve ≥20 turns.
2. Prompt actively instructs eLo to reference earlier turns ("Earlier you mentioned X") rather than acting like they're new.

## What I changed

| File | Line | Change |
|---|---|---|
| `runtime/router/conversation_matrix.py` | 14 | `_MAX_WINDOW = 25` — unchanged. Already ≥20 from prior partial work. |
| `server.py` | 6462 | `[SESSION LOG]` slice: `_cw[-8:]` → `_cw[-20:]`. All 20 kept turns now reach the LLM, not the last 8. |
| `server.py` | 6471–6481 | Added active-reference clause to the SESSION LOG prompt: *"When something David said earlier is relevant to his current message, name it — 'Earlier you mentioned X' — rather than treating it as new. Do not make him re-explain what is already here."* |

The gate above the slice at `server.py:6460` (`if _cw: … session log fires every turn`) was already correct per WO-022 (comment 6444-6458). Not touching the recall-intent phrase gate — that controls vault lookup, not session log inject.

## What I verified (sandbox, read-only)

- `python3 -c "import ast; ast.parse(open('server.py').read())"` → parses.
- Simulated 25-turn session via `conversation_matrix.push()`; rebuilt the `[SESSION LOG]` block exactly as `server.py` does → 20 David + 20 eLo lines, oldest turn 5, newest turn 24.
- Grepped: no other `_cw[-8:]` in the primary SESSION LOG path. The `_cw[-8:]` at line 6627 is the different `[CONVERSATION THREAD]` trajectory inject — intentionally narrower, left alone to avoid scope creep.

## What I did NOT verify

- Live turn with real David. Whether the LLM actually produces an *"Earlier you mentioned X"* reference when the slice contains the relevant turn is a backend-behaviour test the Board owns.
- No `pytest` run — sandbox cannot hit the live `:5050` server, and CLAUDE.md forbids tests against the running server during an active David session.

## Lane / lock discipline

- `server.py.lock` created before the edit (seat=builder1, purpose=WO-B1-0116) and deleted after commit.
- `conversation_matrix.py` not edited (already satisfied the slice ask).
- Card moved: `QUEUE/0116_…` → `DOING/0116_…` → `BUILT/0116_…`. Result block appended in-card.

## Live turn needed (acceptance per CLAUDE.md "BUILT ≠ DONE")

Board test: during a David session, mention something specific early in the thread (e.g. a project name, a decision, a number). Keep talking for 8+ turns on other topics. Then ask about the thing again *without re-stating it*. eLo must retrieve it from the SESSION LOG and ideally lead with "Earlier you mentioned X — …".

Until that live turn fires, this is BUILT, not DONE.

— Builder 1
