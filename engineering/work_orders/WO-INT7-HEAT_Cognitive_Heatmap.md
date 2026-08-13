---
id: INT7-HEAT
title: "One Brain — live cognitive heat-map layer (observability): per-vortex brightness/colour/pulse + time-decay whole-brain heat field"
owner_seat: SEAT-ENG-004 (UI/Avatar, Design) + SEAT-ENG-001 (Builder — emit missing signals)
occupant: Design (render) + Builder (data)
priority: P2
reason: "David 2026-08-01: turn the One Brain into a real-time cognitive observability tool — a live heat map where each faculty glows independently and a translucent, time-decaying whole-brain heat field shows what eLo has been thinking about. Transforms the visualiser from decorative effect into a debugging/observability instrument, true to the One Brain philosophy."
review_required: L1 → L3 (David approves the look — Designer previews)
risk: low-med (additive render + a few new emitted fields; no kernel change)
status: QUEUED — after the field weave + INT7-QV (needs consistent vortices to read against)
created: 2026-08-01
base_commit: 5d4427e
depends_on: INT7-WEB/WEB2 (field), INT7-QV (vortex consistency)
couples: M5 (memory pulses), C1/M4 (thought flow), M6 (valence)
---

# INT7-HEAT — live cognitive heat-map / observability layer

**David's brief (verbatim intent):** a live heat map on several layers — activity intensity, emotional
valence, confidence, memory access, thought flow — over the nine vortices, plus a translucent
whole-brain heat field that time-decays so you can *see what eLo has been thinking about*.

## The nine vortices (each glows independently)
Intent (core) · Attention · Memory · Emotion · Vision · Motion · Body · Voice · Expression.

### Three simultaneous properties per vortex
| Property     | Represents                         | Data source |
|--------------|------------------------------------|-------------|
| **Brightness** | current activity / load          | `systems[x].energy` (exists) |
| **Colour**     | emotional tone / state           | `systems[x].valence` + MoodPalette (exists) |
| **Pulse speed**| processing urgency / frequency   | **NEW** `systems[x].rate` (Builder to emit) |

## The layers
1. **Activity intensity** — brighter vortex = more processing/attention (brightness ← energy).
2. **Emotional valence** — cool→warm colour shift = emotional state, not activity (colour ← valence, MoodPalette).
3. **Confidence** — opacity/saturation = how certain eLo is (**NEW** `systems[x].confidence` 0–1, Builder to emit).
4. **Memory access** — brief pulses from Memory → the requesting faculty. **Reuse M5 memory-echo / a
   bus bead** — do NOT build a new pulse system; extend M5/C1 to carry the source→target.
5. **Thought flow** — animated streams of messages across the **Faculty Bus**. **Reuse C1/M4** (data-packet
   routing / cascade) riding the web strands — compose, don't duplicate.

## The whole-brain heat field (the new capstone)
- A **translucent heat layer over the fluid sim**, **generated from the energy each vortex emits** (not
  painted directly): each vortex radiates into nearby space; overlapping radiation forms **hot spots**
  where multiple systems interact → organic, constantly-shifting field.
- **Time-decay — LIVE SLIDER (David 2026-08-01):** activity fades slowly instead of vanishing. The decay
  window is a **Designer-exposed slider, tunable live while running** (range ~5–60s, default ~20s), so
  David can dial "what eLo's been thinking about over the last N seconds" in real time during debugging.
  This is the observability win.
- Calm at rest — a quiet field with no activity should read near-neutral, not noisy.

## Data contract (Builder emits; Design renders)
- **Exists in `brain_state.json`:** `systems[x].energy`, `.valence`, `.active`, `.label`.
- **NEW fields Builder adds (additive, behind the same writer):**
  - `systems[x].rate` — processing urgency/frequency 0–1 → pulse speed.
  - `systems[x].confidence` — 0–1 → opacity/saturation.
  - optional `systems[x].requested_by` / memory access source→target for the pulse (or reuse M5 trigger).
- Design renders the heat field + time-decay purely from these; **no kernel change** (LAW-017 additive).

## Acceptance
1. Each of the 9 vortices independently shows brightness (energy), colour (valence), pulse speed (rate).
2. Confidence reads as opacity/saturation; low-confidence faculties look "uncertain".
3. Memory access + thought flow use the EXISTING M5 / C1 / M4 layers (no duplicate systems).
4. A translucent whole-brain heat field emerges from vortex energy with **hot spots** at interactions,
   and time-decays via a **live Designer slider** (~5–60s, default ~20s) so recent cognitive focus is
   visible at a glance and David can tune the window while debugging.
5. Calm at rest; MoodPalette-consistent; reuses `EloBrainCluster`; David signs off the look.
6. Handback: Builder diff (new emitted fields + test) · Design diff + a short recording showing a
   memory-heavy vs emotion-heavy moment reading differently on the heat field.

## Notes
- Capstone observability layer — sequence **after** the field weave (WEB/WEB2) + **INT7-QV** (consistent
  vortices to read against). Compose M5/C1/M4/M6; the genuinely new parts are the 3rd vortex property
  (pulse/rate), confidence channel, and the **time-decay whole-brain heat field**.
- 🟠 DAVID — the look is your call; it's also a real dev tool, so prioritise legibility over spectacle.
