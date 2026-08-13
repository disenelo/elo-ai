---
id: WO-045
title: "'Can you take 5' → eLo pops OFF screen for privacy, and comes back when called."
owner_seat: SPLIT — SEAT-ENG-001 (Builder: intent phrasings → leave cmd) + SEAT-ENG-004 (UI/Avatar: pop-off + hide + return)
priority: P2
review_required: L3 (David — eLo actually disappears on "take 5" and returns on call)
status: OPEN — David feature 2026-08-03
---
# WO-045 — "take 5" privacy pop-off

## What David wants
"When I say **'can you take 5'** eLo pops off the screen — I'm asking for a break and some privacy."
eLo should LEAVE the screen (not just settle to idle), stay gone, and return when David calls it back.

## The pieces already exist (grounded)
- `step_out` intent already maps from "taking a break" / "need a break" / "brb" / "heading out"
  (server.py `_SIGNAL_WORDS` 333–340) → returns `step_out` body directive (server.py:426).
- Hide mechanism exists: `hide_widget()` (server.py:3017) + `SetVisible(false)` (from INT7-OFFTOGGLE).
- Canned line "Come back when you need me." (server.py:776).
So this is WIRING what's there, not new systems.

## Fix
1. **Builder (eLo OS):** add "take 5" + privacy phrasings to the step_out map — "take 5", "give me a
   minute/sec", "some privacy", "step away", "leave me to it", "go away for a bit". These must emit a
   distinct **LEAVE/HIDE** command (pop off screen), NOT the plain idle/settle directive.
2. **UI/Avatar (Unity):** on the leave command → play a brief **pop-off-screen** exit, then hide the
   avatar (`SetVisible(false)`) so the screen is clear = real privacy.
3. **Return trigger:** eLo comes back when David calls it ("come back", "you there?", clicks the corner,
   or re-addresses it). Reappears with a small return-on animation.
4. Per ADR-Exec-001: eLo only says "stepping away / taking five" if it actually hides (verify-before-speak).

## Acceptance
1. "Can you take 5" → eLo pops off screen and the screen is clear. 2. It stays gone (privacy), not lurking idle. 3. "Come back" → it reappears.

---
## PRINCIPLE (David 2026-08-03) — presence WITH boundaries, not attention-demanding
David's framing: "Humans need privacy at times, just to be themselves. It's a need overall — otherwise
it's like having a dog needing attention all the time." So this is bigger than one command:
- **eLo grants space on request** ("take 5" → pop off, real privacy) — the explicit half (above).
- **eLo does not clamour for attention by default.** Presence should feel like a considerate
  companion who can be *quietly there or absent*, not one that constantly drifts, pings, or needs
  engagement. Withdrawing is part of good presence, not a failure of it.
- Returning is on DAVID's terms (he calls it back), not eLo re-inserting itself.

This belongs to the Presence domain (canonical **Vol XIII Presence Engine**) and the Social-Intelligence
**boundaries** theme (roadmap gap). Recommend a short presence-principle note in canon so every future
presence/idle behaviour is designed to respect space, not compete for attention. (Flagged to Architect;
David L3 on whether to formalise as a decision.)
