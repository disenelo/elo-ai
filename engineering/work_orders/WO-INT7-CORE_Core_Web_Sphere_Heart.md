---
id: INT7-CORE
title: "One Brain — core web-sphere 'heart': add a small rotating mote-sphere + web links AT the core (core setup unchanged)"
owner_seat: SEAT-ENG-004 (UI/Avatar, Design) — Design lane
occupant: Design (Unity)
priority: P1
reason: "David 2026-08-01: make the core read like a web-sphere — WITHOUT removing the existing core setup. Add rotating motes + web links that orbit the core, sitting at the core like a 'heart', smaller in scale than the core→state section, and tweakable."
review_required: L1 → L3 (David approves the look — Designer previews + exposes tweak sliders)
risk: low-med (additive nucleus at core; must not alter the existing core glow/vortex)
status: QUEUED — Design One-Brain lane (weave family; reuses WEB/WEB2 mote + web-line renderer)
created: 2026-08-01
base_commit: 5d4427e
couples: INT7-WEB / INT7-WEB2 (same mote + wave-line renderer), M1 (breath)
---

# INT7-CORE — the core web-sphere / "heart"

**David's words:** *"I want the core to be like a web sphere (not to remove the core setup) — just adding
the motes that rotate and web links, that rotate around the core, smaller than the core-to-state section,
sitting at the core like a heart which we can tweak."*

## Intent
Keep the **existing core exactly as it is** (its glow / vortex / Intent identity — unchanged). **Add**, at
the core, a compact **web-sphere nucleus**:
- a small cluster of **motes that orbit/rotate around the core**,
- **interconnected with web links** (reuse the WEB/WEB2 **wave/curved-filament** style),
- **scaled smaller** than the core→state section — a tight nucleus sitting *at* the centre,
- reading like a **"heart"** — a dense little rotating, interconnected sphere at the middle of the brain.

## Behaviour
- **Rotates around the core** (gentle continuous spin; can differ in axis/speed from the outer field).
- Reuses the **same mote + wave-line renderer** as the weave (WEB/WEB2) so it's one visual family, just
  smaller/tighter at the core.
- **BEATS WHEN eLo IS THINKING (David 2026-08-02):** the heart's defining behaviour — the nucleus
  **breathes/beats faster when eLo is processing/thinking**, calm/slow at rest. Gated on a thinking
  signal (rising `cluster_energy` / a `thinking` flag; Builder emits one if absent). This is where the
  "thinking breath" lives — the **motes elsewhere stay steady** (David's decision), so the *heart* is what
  quickens. Reuse M1 respiration timing, scaled to a heart-beat. Beat amount is tweakable (slider).
- **Takes the CORE's own colour (David 2026-08-01)** — the heart inherits the core's current hue (same
  colour as the core, not a new one). It's a way to **highlight the centre** — the nucleus reads as a
  denser, brighter concentration of the core itself, reinforcing "this is the middle."
- **Calm at rest**; MoodPalette-consistent; no founder-core hue.

## Tweakable (Designer exposes — David dials the heart)
Expose live params/sliders: **radius/scale** (relative to core), **mote count**, **web-link density**,
**rotation speed/axis**, **beat amount** (coupling to core energy), **opacity**. David tunes the heart to
taste — "which we can tweak."

## Constraints
- **Do NOT remove or restyle the existing core** — this is purely additive on top of it.
- Smaller than the core→state links; must not compete with the outer weave — reads as the *centre*.
- Off clean HR base `5d4427e`; sits in the weave family (reuse WEB/WEB2 strands renderer).

## Process (look gate)
1. Designer builds it + **exposes the tweak sliders**, brings a short preview → **David approves the look
   + dials the heart** (L3) before commit.
2. Additive build, one change, handback diff + short recording (core unchanged, heart added).

## Acceptance
1. Existing core is visually unchanged; a small rotating **web-sphere of motes + links** now sits at the
   core like a heart, smaller than the core→state section.
2. Rotates; reuses the weave's mote + wave-line style (one family).
3. Tweak sliders work live (radius, count, density, spin, beat, opacity).
4. Calm at rest, MoodPalette-consistent; David signs off the tuned look → DONE.
