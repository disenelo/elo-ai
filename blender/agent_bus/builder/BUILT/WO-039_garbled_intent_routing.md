# WO-039 — Garbled intent routing (Tier 2)

> **⚡ VERIFY FIRST** — `DAVID_APPROVED.md` records this as "0 garbles on 400-msg stress" 2026-08-10. Tests exist: `tests/test_wo039_garbled_routing.py` · `tests/test_wo039_conversation_400.py` (+ f1..f6). **Run them before any implementation.** If all pass → return result card and close. If any fail → implement the fix below.



**Full WO:** `engineering/work_orders/WO-039_Garbled_Intent_Routing.md`
**Priority:** P1 · **Status:** OPEN · **Owner:** Builder
**From:** Board — Tier 2 dispatch 2026-08-29

## The gap (live-measured)
- "Yeah so everything I built is related" → eLo: "quit is?" (non-sequitur fragment)
- "What is quit? mean?" → "Shall I quit means?" (garbled echo)
- "What is this question about?" → leaked canned grammar answer (preposition example)

Root: `router/typo_engine.py:116` and `intent_engine.py:38` coerce user prose toward command tokens ("quit/close/kill"). Prose is being fragment-matched against command words.

## What to build
Fix the command-word coercion so user sentences are not mis-parsed as command fragments. Full spec in `WO-039_Garbled_Intent_Routing.md`.

**ATs:** 400-message stress test confirming 0 garble events. `executive.py` — check FREEZE_V1_LOCK before touching `_conversation_action()`.

**Return:** `DONE/FROM_BUILDER_WO-039_garbled_result.md` · ATs · commit

*Board · 2026-08-29*
