---
id: INT7-LL
title: "One Brain — 'lightning-liquid' show: energy travels mode↔mode web as branching lightning with liquid flow"
owner_seat: SEAT-ENG-004 (UI/Avatar) — Design lane
occupant: UI/Avatar (Design)
priority: P1
reason: "David 2026-08-01: add a 'lightning liquid show' between the modes — energy that arcs like lightning but flows/moves like liquid, travelling the web/spider links between the mode nodes."
review_required: L1 → L3 (David visual sign-off) — Designer proposes look FIRST
risk: low-med (additive visual; must stay calm at rest, only 'shows' on activity)
status: QUEUED — after INT7-WEB
created: 2026-08-01
base_commit: 5d4427e
depends_on: INT7-WEB (rides its strands)
couples: INT7-WEB
---

# INT7-LL — "lightning-liquid" show between modes

**David's words:** *"Web Links and Spider links between modes and lightning liquid show needs to be
added."*

## Intent (Architect interpretation — Designer refines, David approves the look)
On the mode↔mode **web strands** (INT7-WEB), energy travels as a **"lightning-liquid"** effect:
- **Lightning** — branching, forked, bright, crackling arcs that jump between mode nodes.
- **Liquid** — but the motion is **smooth, flowing, molten/viscous**, not jittery/strobing — it *pours*
  along the strands rather than snapping.
- **"Show"** — this is a **peak-activity moment**, not constant: it fires when energy is high (strong
  cognition / cross-mode activity), then subsides. At rest the field stays calm (M1/M2 only).

Think: the web comes alive with flowing electric light between modes when eLo is really thinking —
JARVIS/living-organism energy (canon §6.7), MoodPalette-tinted.

## Constraints
- **Rides INT7-WEB strands** (mode↔mode) — do not invent new geometry; build on the web.
- **Calm at rest** — must not overpower the resting look; energy-gated (fires on rising activity, fades).
- **MoodPalette colour only** — no new hue; brightness/flow carries the drama.
- Distinct from C1 (single discrete bead) and M4 (hop cascade) — LL is the flowing lightning *show*, a
  richer peak-energy layer. Coexists with them.
- Off the clean HR base `5d4427e`; sequence AFTER RING-CLEANUP and WEB.

## Process (reserved gate)
1. **Designer proposes the look first** — a short preview/clip or tight description of the lightning-liquid
   behaviour (branch density, flow speed, trigger threshold, decay) → **David visual-approves** before any
   full build/commit. (Avoids another revert like the first WEB pass.)
2. On approval: build additive, one change, handback diff + short recording.

## Acceptance
1. On high activity, energy visibly **arcs (lightning) and flows (liquid)** along the mode↔mode web.
2. At rest it's **quiet** — no constant lightning; calm field preserved.
3. MoodPalette-only; coexists with M1–M6/C1 without breaking them.
4. David signs off the look → DONE.
