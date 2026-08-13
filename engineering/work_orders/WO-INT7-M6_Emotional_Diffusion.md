---
id: INT7-M6
title: "One Brain visualiser — M6 Emotional Diffusion (single change)"
status: READY → DISPATCHED (Design)
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: [INT7-M5 (DONE ✅ David)]
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.6 (M6)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-31
---

# INT7-M6 — Emotional Diffusion (One Brain visualiser, v-next change #7)

A **Homeostasis-layer** behaviour (the organism's global state), where M1–M5 were node/signal behaviours.
On a **valence change**, mood **diffuses through the whole field like dye in water** — the emotional
tone spreading, not a single node firing.

## 1. Objective (one change only)
When eLo's **valence** shifts, the mood colour **diffuses across the field**: **positive valence softens
and spreads outward**; **negative valence contracts inward**. The field's turbulence itself changes with it.

## 2. Exactly what to build
- **Trigger:** a change in **valence** (from `brain_state.json` — the mood/valence signal already emitted).
- **Motion:** the current MoodPalette colour **diffuses like dye** across the whole cluster/field over a
  short spread — a global tint-shift, not a per-node pulse.
  - **Positive valence → soften + spread outward** (the field opens, warms, expands gently).
  - **Negative valence → contract inward** (the field draws in, tightens).
- **Turbulence couples to it:** the underlying vortex turbulence eases (positive) or tightens (negative)
  with the diffusion — the *medium* changes, not just the colour.
- Global and slow — a wash over the field, beneath the faster node behaviours.

## 3. Signal contract
Reads **valence** (and mood) from `brain_state.json` (already emitted). Pure render, no new state.
**Colours strictly from the MoodPalette** (absolute colour rule) — this behaviour is *only* a
diffusion of the existing mood colour; introduce no new hues.

## 4. Constraints (MUST)
- **One change only** — emotional diffusion, nothing else. M1 respiration · M2 dormant noise · M3
  afterglow · C1 routing · M4 cascade · M5 memory echo · clustering · click-pin · labels · node size ·
  anchors all **untouched**. M6 layers on top (whole-field wash) and coexists.
- **MoodPalette only** — the diffusing colour is the current mood colour; no invented colour. (Canon: all
  One Brain colour comes from the eLo OS MoodPalette.)
- **Global + slow** — a homeostatic wash, clearly gentler/slower than the node/signal motions; must not
  read as "activity."
- Directionality is correct: **positive = outward/soften, negative = inward/contract.**
- Lane: `EloBrainCluster` (Presence/Unity). Do **NOT** touch eLo OS (`~/elo-ai/`) — D-I.

## 5. Acceptance (visual review + build gate)
- [ ] A positive valence shift makes the mood colour **soften + spread outward**; turbulence eases.
- [ ] A negative valence shift makes it **contract inward**; turbulence tightens.
- [ ] The diffusing colour is a MoodPalette colour — no new hue introduced.
- [ ] Global + slow — reads as the field's *mood*, not a firing; M1–M5 still work unchanged (all coexist).
- [ ] Builds 0 compile errors; relaunch shows it live; diff is emotional-diffusion-only.

## 6. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review.
Baseline = the M5 commit (`8435146`).

## 7. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect verifies against
§2/§5 → DONE → next in the queue is **C3 Clock-Pulse Sync Wave** (min-interval gated).
