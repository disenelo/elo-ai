# P0 — Movement verb routing failure + NAME RULE violation — RESULT: IMPLEMENTED
**Status:** Complete — pending live verification
**Commit:** ebf0ab0
**Evidence:** `engineering/evidence/ROUTING/movement_verb_routing_fix.md`

---

# P0 — Movement verb routing failure + NAME RULE violation: live evidence
**From:** Board / Lead Architect
**To:** Builder 1
**Date:** 2026-10-05
**Authority:** David L3 — live chat log evidence
**Source:** `docs/architecture/_intake/SOURCE_2026-10-05_DAVID_movement_verb_failure_log.md`
**Priority:** P0 — Kickstarter. David sees this every session.

---

## The log (verbatim)

```
You   peek
eLo   I don't have that recorded.
eLo   i don't have that in my system.

You   climb
eLo   Climb?
eLo   i'm not sure what you mean by "climb" in this context.

You   walljump
eLo   Walljump?

You   wall jump can you wall jump?
[no response]

You   Why have you disappeared?
[no response]

You   Exit run?
eLo   That's valid. And worth pressing on.
eLo   I think there might have been a misunderstanding. I didn't receive any new information or question from the user since our last exchange.
```

---

## Four failures. Fix all four.

### Fix 1 — Movement verbs must route to movement system, not LLM

"peek", "climb", "walljump", "wall jump", "exit run" are movement capability verbs. They must be caught by capability routing before the LLM sees them and dispatched as movement intents to the navplanner.

Current behaviour: routing misses them → LLM receives them → LLM says "I don't have that recorded."

Required: add these verbs to the movement capability routing vocabulary. When David says "peek", "climb", "walljump", "wall jump", "exit run" — routing classifies as MOVEMENT_INTENT and sends to navplanner. LLM does not see them.

Check `spine.py` capability scoring — what vocabulary is it matching against for movement? Add: peek, climb, walljump, wall jump, wall-jump, exit run, parkour, hop, jump, land, warp, teleport, sleep, disappear.

### Fix 2 — Echo pattern: routing must not pass single-word movement verbs to LLM

When routing fails to classify a word, LLM echoes it back as a question ("Climb?"). This confirms the word reached the LLM unclassified. Fix: movement verbs that fail classification threshold should fall to a movement-intent default, not pass through to LLM.

### Fix 3 — NAME RULE: "the user" is prohibited

Observed: "I didn't receive any new information or question from **the user**"

The NAME RULE anchor in `backend_router.py` exists but is not holding under model pressure. Fix (same pattern as [CODE ANALYSIS REQUEST] prepend for COG-004):

Add a post-generation check: if `elo_final` contains "the user" / "a user" / "the human" as a reference to David, prepend `[NAME RULE: The person is David. Never say 'the user'. Say 'David'.]` to the next generation pass and regenerate. Do not surface "the user" to David under any circumstance.

### Fix 4 — LLM bleed-through: generic filler prohibited

"That's valid. And worth pressing on." / "I think there might have been a misunderstanding." — base LLM filler bleeding through when routing fails. These are character breaks.

When capability routing fails and no movement intent is matched: eLo should respond as eLo — not as a generic LLM. Fallback response must come from eLo's character, not the base model's conversational defaults.

---

## Evidence required

Send "peek" to eLo. It routes to navplanner. eLo does not say "I don't have that recorded."
Send "climb". Same.
Send "walljump". Same.
Check `elo_final` for "the user" — none present.

File to: `engineering/evidence/ROUTING/movement_verb_routing_fix.md`
