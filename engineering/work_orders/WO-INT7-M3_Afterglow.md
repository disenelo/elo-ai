---
id: INT7-M3
title: "One Brain visualiser — M3 Neural Afterglow (single change)"
status: READY
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: [INT7-M2 (DONE)]
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.6 (M3)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-27
---

# INT7-M3 — Neural Afterglow (One Brain visualiser, v-next change #3)

## 1. Objective (one change only)
When a faculty goes inactive, its vortex doesn't switch off cleanly. It leaves a faint
**phosphorescent wake** — a slow, graceful decay that reads as "was thinking" not "switched
off." The brain remembers it was used.

## 2. Exactly what to build
- **Trigger:** a faculty node transitions from **active → inactive** (energy drops below the
  active threshold, or `active` flag goes false).
- **Effect:** the node's motes (or its glow/colour) begin a **slow phosphorescent decay** —
  faint residual brightness/colour fades out over **2–5 seconds**. Eases out smoothly (not
  a linear cut or an instant snap).
- **Character:** reads as "afterglow" — warm, faint, trailing. Not a flash or a pulse; just
  the memory of activity slowly cooling.
- **M2 coexistence:** once the afterglow fully decays, the node returns to dormant state
  (M2 micro-shimmer resumes). The two don't fight — afterglow fades out, dormant noise
  fades in underneath.
- **Active state:** if the faculty reactivates mid-decay, the afterglow is immediately
  absorbed back into normal active behaviour (no visible conflict).

## 3. Signal contract
Reads per-system `energy` / `active` from `brain_state.json` (already emitted). Transition
is detected by watching `active` flip false (or `energy` cross threshold). Pure render — no
new state fields needed.

## 4. Constraints (MUST)
- One change only — afterglow only (M1, M2, colours, clustering, click-pin, labels, node
  size, anchors untouched).
- **Tiny memory cost** — per-node decay timer only; no particle history, no extra buffers.
  A single `float afterglowT` per node (0→1 normalised decay progress) is the budget.
- Decay duration: **2–5s** (tunable via an inspector float `afterglowDuration`, default 3s).
- Ease: smooth out (decelerate toward end) — not linear.
- **Background-safe:** at full afterglow (t=0) the residual must be clearly below normal
  active brightness; at t=1 (decayed) it must be indistinguishable from dormant.
- Lane: `EloBrainCluster` (Presence/Unity). Do NOT touch eLo OS (`~/elo-ai/`) — D-I.

## 5. Acceptance (visual review + build gate)
- [ ] Activate a faculty, then let it go idle — its vortex visibly fades over ~3s, not snaps.
- [ ] The fade reads as "was thinking" — warm, trailing, not flashing.
- [ ] Once fully decayed, M2 dormant shimmer resumes naturally.
- [ ] If the faculty reactivates mid-fade, no visual glitch.
- [ ] M1 respiration + M2 dormant shimmer both still run unchanged.
- [ ] Builds 0 compile errors; relaunch shows it live; diff is afterglow-only.

## 6. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review.
Baseline = M2 commit.

## 7. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect
verifies against §2/§5 → DONE → next is **C1 Data Packet Routing** (first computational
win — discrete quantized beads, not organic flow).
