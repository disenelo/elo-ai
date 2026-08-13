---
id: INT7-M1
title: "One Brain visualiser — M1 Neural Respiration (single change)"
status: READY
target_agent: UI/Avatar (Design/visual agent)
priority: P2
owner: ""
depends_on: []
blocks: []
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.6 (M1)
  - DISENELO-eLoDesktopBuddy/ONE_BRAIN_QUANTUM_SPEC.md (Motion model)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I: Builder does not touch this repo)
created: 2026-07-27
---

# INT7-M1 — Neural Respiration (One Brain visualiser, v-next change #1)

## 1. Objective (one change only)
Make the whole One Brain field perform a subtle **density inhale/exhale** — the "living
respiration" of the brain. This is the first v-next motion behaviour and the proof of the
one-change-build-wait discipline.

## 2. Exactly what to build
- The **space/density between vortices breathes** — a slow contract → hold → expand → rest.
  **NOT** node scale, **NOT** camera zoom, **NOT** anchor movement. The vortices themselves
  barely move; the field density between them oscillates.
- **Driven by `brain_state.json → cluster_energy`:**
  - low `cluster_energy` → **12–18 second** cycle;
  - high `cluster_energy` → **4–6 second** cycle;
  - interpolate the period smoothly between those bounds as `cluster_energy` varies.
- Amplitude tiny (background-safe): a gentle density modulation, never distracting.

## 3. Signal contract
Reads only `cluster_energy` from `brain_state.json` (already emitted by
`blender_bridge/brain_state_writer.py`, schema `brain_state/v1`). Pure render — no new state.

## 4. Constraints (MUST)
- Background-safe: subtle; no darting; no pop.
- Do **not** change: node anchors, MoodPalette colours, clustering behaviour, click-to-pin, labels.
- One change only — respiration and nothing else this pass.
- Lane: `EloBrainCluster` in the Presence/Unity repo. **Do not touch eLo OS (`~/elo-ai/`)** (D-I).

## 5. Reference (David fed these — pin them so they persist)
Visual language ref per `ONE_BRAIN_QUANTUM_SPEC.md`: JARVIS/Ultron holographic-mind frames
(David's `~/Documents` screenshots). **Action:** if those reference images aren't already in
the Presence repo, save them to a `DISENELO-eLoDesktopBuddy/refs/one_brain/` folder and cite
them here — so the context David provided is durable, not chat-only.

## 6. Acceptance (visual review + build gate)
- [ ] At low `cluster_energy`, the field breathes on a ~12–18s cycle; at high, ~4–6s; smooth between.
- [ ] Only inter-node **density** breathes — anchors, scale, zoom, colours unchanged.
- [ ] Background-safe (David eyeballs: not distracting).
- [ ] Builds with **0 compile errors**; relaunch shows it live.
- [ ] Nothing else changed this pass (diff is respiration-only).

## 7. Build discipline (David's rule)
**One change · exactly to spec · build (0 errors) · relaunch · then WAIT for review.** No other
edits in this pass. Presence baseline is clean at `466a4e1`.

## 8. Handback
Commit hash + one-line note + "before/after" description → post to `COMPLETION_LOG.md`.
David visual-reviews; Architect verifies against §2/§6 → then DONE. Next change (M2 Dormant
Noise) only after this one is approved.
