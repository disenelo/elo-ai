---
id: WO-058
title: "eLo desktop VFX layer — plug David's existing snow / meditation-glow / rain VFX into the UI, STATE-DRIVEN."
owner_seat: SEAT-ENG-004 (UI/Avatar Design)
priority: P3 — PARKED, post-Presentable v1 (polish, not core)
status: CAPTURED (David 2026-08-05) — assets already exist
---
# WO-058 — desktop VFX layer

David already built these VFX (ready to plug into the UI): **snow · glowing spots (meditation) · rain.**
This WO is integration + wiring, not new asset creation.

## The rule (so VFX means something, not decoration)
Per Single Cognitive Truth + Embodied Truth: **VFX reflects eLo's REAL state, never fires at random.**
- **Meditation glow** → plays when eLo is ACTUALLY meditating (Presence Engine / meditate state), at his
  location. Ties the existing meditate behaviour.
- **Snow / rain** → atmosphere driven by real state — this is the "weather-without-weather" / emotional-
  physics thread already in WO-049: desktop mood/climate, or real weather when a location is set (WO-030),
  or eLo's emotional state. Read real state, never fabricated.
- One VFX controller reads the same cognitive state everything else reads (the Moment) — not a parallel
  random-VFX driver (Check-Before-Build: extend the presence/state layer, don't bolt on a separate system).

## Scope
Wire David's existing VFX prefabs to state triggers in DesktopBuddy; expose intensity for L3 dial.
Parked until Presentable v1 ships — it's the "make it look cool" polish layer on top of a coherent eLo.

## Platform-bounded VFX + surface reactions (David 2026-08-05)
- **Bound the VFX to the ShadowCatcher size** — effects stay within eLo's platform/landing footprint,
  not spilling across the whole screen. When eLo lands on a platform (window/surface), the VFX region
  matches that platform's ShadowCatcher extent.
- **Surface reacts to the weather VFX:** rain → splatter on the platform surface; snow → builds up /
  accumulates on the platform over time. Ties the VFX to the REAL surface eLo occupies (Situated —
  the effect is on the ground he's actually on, scaled to it).
- Scale + accumulation are state/time-driven off the same Moment (heavier mood/weather = more), never random.
