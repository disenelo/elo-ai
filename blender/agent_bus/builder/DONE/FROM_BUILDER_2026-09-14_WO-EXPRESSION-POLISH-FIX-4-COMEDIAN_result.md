# FROM BUILDER → BOARD — WO-EXPRESSION-POLISH-BUNDLE-001 FIX-4: Accidental Comedian FAST Path
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-EXPRESSION-POLISH-BUNDLE-001.md
**Fix:** WO-ACCIDENTAL-COMEDIAN-FAST-PATH-001

---

## FAST path routing verification

`runtime/backend_router.py:1148-1157` — FAST routing active conditions:
```python
# action in ("celebrate", "react", "stay_silent") → FAST
# JOYFUL/PLAYFUL tone AND sig < 0.4 → FAST
# any action AND sig < 0.2 (clean presence) → FAST
```

Groq selected when FAST path fires (`_groq_available()` → `groq(FAST)`). WO-MODEL-ROUTING-001 confirmed active.

FAST routing confirmed for creative/playful turns:
```
tone=JOYFUL  action=answer    intent=inquiry      → FAST=True  ✓
tone=DIRECT  action=celebrate intent=conversation → FAST=True  ✓
tone=PLAYFUL action=answer    intent=humour       → FAST=True  ✓
```

---

## Few-shot block added

**`runtime/prompt_builder.py`** — before `_push("executive_directive", ...)`:

Fires when: `tone in (JOYFUL, PLAYFUL) OR action in (celebrate, react) OR intent == humour`

4 pairs from real session JSONL expressed turns (accidental comedian × 2, compression × 2):

```
[eLo voice — accidental comedian: meaning arrives sideways. Never set up a joke.
Never signal humour. The funny part is a side-effect of meaning it.]
David: "it's working now but i don't totally understand why"
eLo: "That's alive. The limiter fix showed up right when it was needed."

David: "the routing isn't picking up the calendar events"
eLo: "That calendar's gone mute, like it's waiting on a handshake from the rest of the system."

[eLo voice — compression: the whole thing in one line. Say it and stop.]
David: "i feel like the game, the book, the robot — they all keep bleeding into each other"
eLo: "Worlds keep bleeding into each other."

David: "you keep noticing things about me, it's kind of funny"
eLo: "You've got a smile on your face, and it's not just the code."
```

Examples sourced from `runtime/logs/expressed_elo_audit.jsonl` — turns with JOYFUL/CHILDLIKE-WISE register. No joke setup, no "haha", meaning landing through commitment to the observation.

---

## DoD

- [x] FAST routing confirmed active for playful/creative turns
- [x] Few-shot block wired to FAST-path-eligible conditions
- [x] 4 example pairs: 2 accidental comedian, 2 compression — from real JSONL evidence
- [x] Block does not fire on generic DIRECT/conversation turns
- [ ] Live FAST path turn with accidental quality — in FIX-5 REAUDIT (needs Groq active)

---

*Builder · 2026-09-14*
