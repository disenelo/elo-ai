---
id: INT7-WEB
title: "One Brain visualiser — persistent spider-web links (living-organism web)"
status: READY → DISPATCHED (Design)
target_agent: UI/Avatar (Design)
priority: P2
depends_on: []
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.7 (spider-web webs · data links ride them)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-31
---

# INT7-WEB — Persistent spider-web links (One Brain visualiser)

Makes the **spider-web** David asked for actually *visible at rest*. Today the web is a routing substrate —
it only shows when C1 beads / M4 cascades travel it. David wants the **floating, living-organism web**
between the states/motes to be a persistent visual (§6.7).

## 1. Objective (one change only)
Render **faint, persistent spider-web filaments** between states/motes (and around the core) that **float
and drift like a living organism** — visible even when nothing is firing. The C1/M4 beads then ride *these*
visible filaments (they already ride the substrate; now the substrate is seen).

## 2. Exactly what to build
- **Web filaments:** thin, faint lines connecting nearby motes/states + state→core, forming an organic
  connectome web (not a rigid frame). Low opacity so it reads as gossamer, not solid.
- **Drift:** the web **floats/sways gently** (organic, alive) — subtle motion, not static.
- **Rides:** confirm C1 beads + M4 cascade travel *on* these now-visible filaments (§6.7 — the web is the
  routing substrate).
- Organic at rest — the **crystalline/geodesic** condensation is a *separate* later behaviour (C2), so keep
  this one soft/floating, not a rigid lattice.

## 3. Constraints (MUST)
- **One change only** — the persistent web, nothing else. Motion (M1–M6/C1), colours (MoodPalette),
  clustering, labels, node size, anchors **untouched**.
- **Background-safe** — faint + gentle; must not read as "activity" or distract; low perf cost.
- Colours from MoodPalette / the blue web-sphere language (§6.7) — no new hues.
- Lane: `EloBrainCluster` (Presence/Unity). Do NOT touch eLo OS (`~/elo-ai/`) — D-I.

## 4. Acceptance (visual review)
- [ ] A faint, floating spider-web of filaments is visible between motes/states at rest.
- [ ] It drifts gently (alive), reads as gossamer not solid, doesn't distract; framerate stable.
- [ ] C1 beads / M4 cascade ride the visible filaments; M1–M6 unchanged.
- [ ] Builds 0 errors; relaunch shows it live; diff is web-only.

## 5. Handback
Commit + screenshot → `COMPLETION_LOG.md`. David visual-reviews → DONE. (C2 Geodesic condensation — the
web crystallising at high `cluster_energy` — remains the later motion-queue item.)
