# 0062 — WO-036b: the narration scrub is opener-only. That gap IS the drift David just hit.

**WO:** WO-036b · **Seat:** builder · **Priority:** P1 (with `0060`)
**Reserved?** no — **but see §3: this touches eLo's voice, so the LIST is David's, not yours**
**STATE: AUTHORISED to implement the mechanism · the wording is David's**

## 1 · WO-036 is marked ✅ DONE and the board says why it isn't
The DISPATCH_BOARD carries its own caveat beside it:
> **"WO-036 scrub is opener-only → extend"**

`runtime/prompt_builder.py:428-430` FORBIDS: the ten canned aphorisms · asterisk actions · correcting David's
terminology. **All good, all real.** What is absent is the entire reflective-mirroring family:

`"You mentioned…"` · `"I noticed…"` · `"You're feeling…"` · `"You were thinking…"` · `"It's like you're…"` ·
`"You want to keep exploring…"` · `"That's what I'm here for"` · `"…as you navigate these challenges"`

**Every one of those appears in David's 2026-08-20 transcript.** `_FIXTURES/chatlog_2026-08-20_ground_jam.json`
turns 4-10. This is not a new class of bug — **it is the residual of a card closed half-built.**

## 2 · The mechanism
Extend the scrub from openers to **anywhere in the response**, and add the mirroring family to FORBIDDEN with
the same rephrase-in-your-own-words instruction the aphorism rule already uses. Do not add a post-hoc regex
that deletes sentences — **that would mute eLo rather than redirect him.** The aphorism rule's pattern (tell
the model to say it differently) is the shape to copy.

## 3 · 🟠 The LIST is David's, not mine and not yours
`[PROPOSAL]` — the eight phrases above are **my reading of his transcript**, not his ruling. Bring him the
list; he adds and removes. Rule 4d: no silent substitution into eLo's voice.
🔴 **And the boundary that keeps this honest:** REFLECT is one of the nine CAL actions and it is FROZEN.
`prompt_builder.py:418` already defines it well — *"Say the thing you noticed and couldn't NOT say. Specific
to what they actually said… Not 'we can stay with that' or 'take your time'. The thing you actually saw."*
**That instruction is right.** This card kills **generic** mirroring. It must not weaken genuine noticing.
If a change would make eLo notice *less*, it is out of scope — flag it and stop.

## 4 · Test — `tests/test_wo036b_scrub.py`
1. Replay `_FIXTURES/chatlog_2026-08-20_ground_jam.json` turns 4-10 → **no reply opens with or contains a
   forbidden mirroring stem.** *(RED today — 7 of 7 currently fail)*
2. Mid-response occurrences are caught, not just openers. *(RED today)*
3. A genuine `reflect` turn still produces specific noticing — **anti-mute assertion, and it must be real.**

## Done when
Implemented · tests green · committed · David's ruled list recorded in the card.

## Result
- commit:
- test:
- David's final phrase list:
