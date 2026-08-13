---
id: INT7-HR
title: "One Brain visualiser — High-res glow sprite + tighter falloff (single change)"
status: READY → DISPATCHED (Design)
target_agent: UI/Avatar (Design)
priority: P2
depends_on: []
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.5 #4 (fidelity refinement — reverted, redo)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-31
---

# INT7-HR — High-res glow sprite (One Brain visualiser)

Re-does the **fidelity** refinement that was reverted in the bad build (§6.5 #4). David: the current look
is too soft/low-res — wants it **sharper / higher-res**.

## 1. Objective (one change only)
Sharpen the brain's look: **higher-resolution glow sprite + tighter falloff** — crisper motes/nodes, less
blur, cleaner edges. Same colours (MoodPalette), same everything else — just resolution/fidelity.

## 2. Exactly what to build
- Replace/upscale the glow sprite to a **higher-res texture**; tighten the falloff so motes read as sharp
  points of light, not soft blobs.
- Applies to motes + nodes; keep the overall glow *language* (just crisper).

## 3. Constraints (MUST)
- **One change only** — fidelity/sprite, nothing else. Motion (M1–M6/C1), colours (MoodPalette),
  clustering, labels, node size, anchors all **untouched**.
- Colours strictly MoodPalette. No new hues.
- Watch performance — higher-res sprite must not tank framerate; keep it bg-safe.
- Lane: `EloBrainCluster` (Presence/Unity). Do NOT touch eLo OS (`~/elo-ai/`) — D-I.

## 4. Acceptance (visual review)
- [ ] Motes/nodes read **sharper / higher-res**, less blurry, tighter falloff.
- [ ] Colours + motion + layout unchanged; framerate stable.
- [ ] Builds 0 errors; relaunch shows it live; diff is sprite/fidelity-only.

## 5. Handback
Commit + before/after screenshot → `COMPLETION_LOG.md`. David visual-reviews → DONE.
