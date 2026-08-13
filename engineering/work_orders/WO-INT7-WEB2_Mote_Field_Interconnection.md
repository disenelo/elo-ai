---
id: INT7-WEB2
title: "One Brain — mote-field interconnection: motes connect to each other AND to their state, wave-line style (matches Core→States)"
owner_seat: SEAT-ENG-004 (UI/Avatar) — Design lane
occupant: Design (Unity)
priority: P1
reason: "David 2026-08-01: the motes following each state should connect to each other and to the state — a deeper, more in-depth field. The line look should match the existing wave/curved lines that connect the Core to the States."
review_required: L1 → L3 (David approves the look — Designer previews first)
risk: low-med (additive rendering; must stay calm at rest, not clutter)
status: QUEUED — after INT7-WEB (same web family)
created: 2026-08-01
base_commit: 5d4427e
depends_on: INT7-WEB (state↔state mesh lands first)
couples: INT7-WEB, INT7-LL
---

# INT7-WEB2 — mote-field interconnection (the finer web, wave-line style)

**David's words:** *"The motes that are following the states — can they connect to each other and the
state, to illustrate a more in-depth field. I want the lines to look like the way the waves and lines are
connected with the Core to the States."*

## Intent
Right now each state has orbiting **motes** that read as separate particles. Give them **connective
lines**:
- **mote ↔ mote** within a state's cluster (near-neighbour links), and
- **mote ↔ its state node** (spokes to the centre of their cluster),

so the cluster looks like **one woven field**, not loose dots. **Match the existing Core→States line
aesthetic** — the same **wave / gently-curved filament** look and feel (not straight rigid lines), same
translucency family, MoodPalette-tinted, drifting softly.

## Distinct from INT7-WEB / relationship
- **INT7-WEB** = the coarse **state↔state / mode↔mode** gossamer mesh (between the big nodes).
- **INT7-WEB2** (this) = the **fine, intra-cluster** web at the **mote level** (motes to each other + to
  their state).
- Together they read as one continuous field: Core → States (existing waves) → state↔state (WEB) →
  mote field (WEB2). **INT7-LL** lightning can later travel any of these strands.

## Note — "breathe when thinking" lives on the CORE, not here (David 2026-08-02)
The thinking-breath was moved to **INT7-CORE** (the heart beats when eLo thinks). WEB2's motes + links
stay **steady** — David deliberately removed the random-pulsing look, so the field does not breathe.

## Constraints
- **Reuse the Core→States line renderer/style** — same wave curvature, width falloff, translucency — so
  the family is consistent (don't invent a new line look).
- **Calm at rest** — near-neighbour links + gentle drift only; must NOT turn the field into visual noise.
  Cap connections per mote (e.g. k-nearest few), fade with distance, low opacity.
- MoodPalette colour only; energy may subtly brighten a cluster's strands.
- Off the clean HR base `5d4427e`; sequence **after INT7-WEB** so the state-level web is settled first.

## Process (look gate)
1. **Designer previews the look first** (short clip / tight description: link density, curvature, opacity,
   per-mote cap) → **David approves the look** before full build/commit (avoid a revert).
2. On approval: additive build, one change, handback diff + short recording.

## Acceptance
1. Motes visibly connect to each other and to their state with **wave/curved filaments matching the
   Core→States style** — the cluster reads as one deep field.
2. **Calm at rest** — no clutter/noise; capped, distance-faded, low-opacity.
3. Consistent with INT7-WEB (same family, different scale); MoodPalette only; M1–M6/C1 untouched.
4. David signs off the look → DONE.
