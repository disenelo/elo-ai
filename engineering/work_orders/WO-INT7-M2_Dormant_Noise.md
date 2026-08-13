---
id: INT7-M2
title: "One Brain visualiser — M2 Dormant Noise (single change)"
status: READY
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: [INT7-M1 (DONE)]
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.6 (M2)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-27
---

# INT7-M2 — Dormant Noise (One Brain visualiser, v-next change #2)

## 1. Objective (one change only)
The brain is **never fully still.** When no system is active, inactive vortices show
microscopic stochastic flicker — quantum noise — so the field feels alive even at rest.

## 2. Exactly what to build
- **Trigger:** a system is **inactive** (low/zero `energy`, and overall calm — no active systems).
- **Motion:** that vortex's motes get tiny **stochastic perturbations** — single motes flicker,
  micro-jitter in position/brightness. Brownian, sub-threshold.
- **Amplitude:** **below the M1 respiration level** — barely perceptible; "enough to feel alive,
  not enough to distract." Active systems are unaffected (their own motion dominates).
- Layers *on top of* M1 respiration — both coexist (M1 = whole-field breathing; M2 = per-inactive-node flicker).

## 3. Signal contract
Reads per-system `energy`/`active` from `brain_state.json` (already emitted). Pure render, no new state.

## 4. Constraints (MUST)
- One change only — dormant noise, nothing else (M1, colours, clustering, click-pin, labels,
  node size, anchors untouched).
- **Background-safe:** amplitude strictly below M1; must not read as "activity" (that's the synapse
  behaviours later) — this is *idle shimmer*, not firing.
- Only **inactive** vortices flicker; an active system overrides it.
- Lane: `EloBrainCluster` (Presence/Unity). Do NOT touch eLo OS (`~/elo-ai/`) — D-I.

## 5. Acceptance (visual review + build gate)
- [ ] With eLo idle (no active systems), inactive vortices show faint micro-flicker.
- [ ] Flicker amplitude is clearly below the M1 breathing; not distracting.
- [ ] An active system shows its own behaviour, not the dormant shimmer.
- [ ] M1 respiration still works unchanged (both coexist).
- [ ] Builds 0 compile errors; relaunch shows it live; diff is dormant-noise-only.

## 6. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review. Baseline = M1 commit.

## 7. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect verifies against
§2/§5 → DONE → next is **M3 Afterglow**.
