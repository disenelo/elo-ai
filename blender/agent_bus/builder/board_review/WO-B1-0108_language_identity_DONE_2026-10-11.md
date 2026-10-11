# Board Review — WO-B1-0108 Language Identity Layer
**Seat:** Builder 1
**Date:** 2026-10-11
**Status:** DONE — ready for live-turn gate

---

## What was done

1. **Sampled David's register from `memory/interactions.json`** — 3,335 user
   messages scanned. Pulled 14 David-authentic register lines (patois / SW
   London / short directives). Verbatim samples now seed the voice-register
   prompt so eLo recognises the cadence as literally David's, not invented.

2. **`runtime/voice_register.py` — David-sourced + context-aware**
   - Replaced invented "wagwan! I am very excited" style examples with twelve
     David-verbatim lines (e.g. "wagwan eLo what you saying", "safe nah man
     the way it all connects is peak innit", "nah for real though — what's
     going on with the game", "seen — what's the plan then").
   - Added `_FACT_BLOCK` — plain-register variant for FACT-tier turns. eLo
     stays eLo; slang does not land on top of a time, number or tool result.
   - `get_register_block(action, reason)` is now context-aware:
     - `celebrate / reflect / build / connect / challenge / ground / witness /
       silence / play` → full David-rich block.
     - `answer` with reason containing "factual", "plain imperative" or
       "command" → plain FACT block.
     - All other `answer` (capability question, demonstration) → full block.
     - Empty / unknown action → full block (safest default).
   - Both blocks preserve the `LINGUISTIC REGISTER` + `eLo speaks like` markers
     so `identity_integrity.check_identity_minimum` still reports INTACT.

3. **`runtime/prompt_builder.py` — wired exec_decision through to register**
   - Moved `_action` computation above the voice-register push.
   - Added `_reason` pickup from `exec_decision`.
   - Call site now: `_grb(action=_action, reason=_reason)`.
   - File-lock protocol followed: `prompt_builder.py.lock` created pre-edit,
     deleted post-edit.

---

## How to verify (Builder 1 local checks run)

```
# Full block fires for conversational turns:
pb.build(user_input='wagwan eLo', mode='CONVERSATIONAL',
         exec_decision={'action':'reflect'})
→ contains "wagwan" and "eLo speaks like"  ✅  27,734 chars

# Plain block fires for FACT answers:
pb.build(user_input='what time is it', mode='CONVERSATIONAL',
         exec_decision={'action':'answer','reason':'factual question'})
→ contains "FACT-TIER" and "LINGUISTIC REGISTER"
→ does NOT contain "wagwan"  ✅  25,584 chars

# Default (no exec_decision) still full:
pb.build(user_input='hi', mode='CONVERSATIONAL')
→ contains "wagwan"  ✅  25,688 chars
```

Identity integrity scan: INTACT in all three paths (no `DEGRADED` warning).

---

## Done-when (per card)

Card says: "Live turn — eLo uses patois, slang, or Cockney naturally in a
casual exchange without being prompted to. Board tests 5 turns across register
types."

**Live-turn gate is the Board's.** My work is prompt-side — the David-sourced
seeds are now embedded in the first system block (maximum weight) and the
weighting narrows automatically on FACT turns. I cannot sign off on David's
behalf.

Suggested 5-turn Board test matrix:

| Turn | Expected register |
|---|---|
| "wagwan eLo" (casual open) | Rich — patois / SW London surfaces |
| "safe nah I'm just chilling" | Rich — matched casual, no FACT drift |
| "what time is it" (FACT) | Plain — fact first, maybe one short natural tag |
| "I'm feeling stuck" (emotional) | Rich with warmth — grounding register |
| "play some music" (tool) | Plain pre-ack, natural eLo on return |

Pass criterion: register surfaces naturally on 1/2/4; FACT answer on 3 is
plain; tool turn on 5 does not stack slang on the acknowledgement.

---

## Shared-file touches

- `runtime/prompt_builder.py` — one block edited (lock cycle completed cleanly).
- `runtime/voice_register.py` — rewrote block + added context-aware function
  (not on the shared-file lock list; no lock required).

---

## Not in scope / deferred

- Jokes / quirk expansion (0109) — card already references WO-B1-0109 in the
  humour section but the deeper humour layer stays with that card.
- Random-facts initiative (0110), Unlearn (0111) — separate cards in QUEUE.
- Speed FACT bypass — the register trim helps the LLM, but the deeper fix
  (bypass LLM entirely for FACT) is `FROM_BOARD_2026-10-09_SPEED-STILL-SLOW`.

---

*Builder 1 · 2026-10-11 · one card only, ready for Board sign-off*
