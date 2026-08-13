---
id: INT7-OFFTOGGLE
title: "Settings — 'turn Brain visualiser off' toggle doesn't hide the brain (still renders when off)"
owner_seat: SEAT-ENG-004 (UI/Avatar, Design)
occupant: Design (Unity)
priority: P2
reason: "David 2026-08-02: there's a Settings option to turn the Brain visualiser OFF, but toggling it off still shows the brain. The toggle isn't actually hiding/disabling the render."
review_required: L1 → L3 (David toggles it live)
risk: low (UI toggle wiring; no cognition/kernel change)
status: READY
created: 2026-08-02
---

# INT7-OFFTOGGLE — Brain visualiser OFF toggle doesn't hide it

**David's words:** *"When I select the option to turn Brain visualiser off, it still shows the brain
(this is in the settings)."*

## Task
The Settings toggle for the Brain visualiser must actually **hide/disable the render** when off.
- Find the Settings toggle → confirm it's wired to the `EloBrainCluster` visibility (and/or the
  `show_one_brain` flag in `brain_state.json`).
- When OFF: the whole One Brain (cluster, motes, links, glow, voice-wave, all layers) is **hidden and
  stops rendering/updating** — not just dimmed. When ON: it comes back cleanly.
- Persist the setting (survives restart) so "off" stays off.
- Check nothing else force-re-enables it (e.g. eLo OS writing `show_one_brain:true` each turn overriding
  the user's OFF choice — the user toggle should win).

## Acceptance
1. Settings → Brain visualiser OFF → the brain disappears completely (no residual render/motes/links).
2. Toggle ON → it returns cleanly.
3. Setting persists across restart; eLo OS state updates don't override the user's OFF choice.
4. David toggles it live → confirms → DONE.
