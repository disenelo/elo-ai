---
id: INT7-LBL
title: "One Brain visualiser — Label behaviour (single change)"
status: READY
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: []
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.5 #1 (FINAL label rule)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-27
---

# INT7-LBL — Label behaviour (One Brain visualiser, single change)

## 1. Objective (one change only)
Clean up the labels: **no label text on zoom**; info appears **only on interacting with a state**.

## 2. Exactly what to build (David's final rule)
- **Zoom in → NO label text.** No floating per-node names at any zoom level; the cluster reads clean.
- **Hover OR click a state → reveal that state's info readout** (`_tip`): system name + feeling
  sentence + energy% (from `brain_state.systems[*].label` / `detail`).
- **Move away / click empty → hide** the readout. Nothing persistent.
- Only the *interacted* state shows info; others stay label-free.

## 3. Constraints (MUST)
- One change only — label behaviour, nothing else (colours, motion, clustering, click-pin isolate,
  node size, anchors all untouched).
- Background-safe; readout is legible but unobtrusive; overlay stays click-through where it isn't the target.
- Lane: `EloBrainCluster` (Presence/Unity). Do **not** touch eLo OS (`~/elo-ai/`) — D-I.

## 4. Acceptance (visual review + build gate)
- [ ] Zoomed in, no names/labels are shown anywhere by default.
- [ ] Hover a state → its info readout appears; move off → it hides.
- [ ] Click a state → its info readout appears (and existing click-pin isolate still works); click empty → hides.
- [ ] No other state shows text while one is targeted.
- [ ] Builds 0 compile errors; relaunch shows it live; diff is label-only.

## 5. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review. Baseline clean.

## 6. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect verifies against §2/§4 → DONE.
