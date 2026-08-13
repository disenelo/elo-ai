---
id: GM-1
title: "eLo's Planet — Core Loop skeleton prototype"
status: SUPERSEDED — base movement already in; reality is at GM-2 (rig swap in progress). See board Game stream + GM-0 blocker.
target_agent: Game Designer/Builder (Unity)
priority: P1
owner: ""
depends_on: []
spec_refs:
  - docs/architecture/_refs/game/eLo_Planet_Game_Technical_Specification_v4.md (§19.2 build order, §20 roadmap)
lane: eLo-Planet game (separate Unity project — NOT eLo OS, NOT DesktopBuddy)
repo_path: /Users/Disenelo/eLo-Planet  (git github.com/disenelo/eLo-Planet · main · Unity 6000.3.6f1 · URP · New Input System · CharacterController-only)
tracker: ~/Documents/DISENELO/memory/projects/eLo-Planet_Tracker.md (+ eLo-Planet_Handover.md 2026-06-29)
created: 2026-07-27
---

> **RECONCILED 2026-07-27 (Architect):** the Game agent's relay shows base movement (WASD, camera)
> is already in and the eLo_v2 rig is being migrated into `Assets/Scene.unity` — i.e. work is at
> **GM-2**, not the pre-rig skeleton this WO describes. GM-1 is therefore **superseded/folded**. The
> immediate item is **GM-0** (resolve the two-eLos-in-scene blocker) → then GM-2 continues.

# WO-GM1 — Core Loop skeleton prototype (eLo's Planet)

## 1. Objective
Get a **playable traversal prototype** of the invasion Core Loop running **with zero animation
dependency** — the spec's skeleton-first approach (§19.2), so progress isn't blocked on the pending
character animations (the current #1 blocker per §19.1).

## 2. Exactly what to build (§19.2 Step 1)
- A **placeholder object** (cube/capsule) that moves through the existing **Tube Stage**.
- **Camera rig:** side-scrolling camera + the **depth-plane camera blends** (the core mechanic, §7).
- **Basic movement:** left / right, jump, land.
- **Depth-plane shifting** tested with the placeholder.
- Confirm **stage geometry, collision, and camera feel** — all with the placeholder, no rig.

## 3. Why this first
Animations are the current blocker (§19.1). Skeleton-first decouples traversal/camera/collision from
the rig, so the Core Loop is testable now; the eLo rigged model swaps in later (GM-2) with animations
attached as they land.

## 4. Constraints (MUST — Change Control D-M)
- **One coherent prototype, to spec, then WAIT for review** — no scope creep into companions/weapons/UI.
- Lane = the eLo-Planet Unity project only. Do **not** touch eLo OS (`~/elo-ai/`) or the DesktopBuddy repo.
- Build against the **v4 spec** (pinned: `docs/architecture/_refs/game/`), not chat.

## 5. Acceptance (David visual review + build gate)
- [ ] Placeholder moves L/R, jumps, lands in the Tube Stage.
- [ ] Side-scroll camera + depth-plane blend read correctly; depth-plane shift works.
- [ ] Collision + stage geometry confirmed; camera feel acceptable to David's eye.
- [ ] Builds/plays with 0 errors; no rig/animation dependency.

## 6. Handback
Short clip/screens + commit hash → `COMPLETION_LOG.md`. David reviews → DONE → **GM-2** (swap in eLo
rigged model + attach run/jump/idle animations as completed).

## 7. Roadmap context (§20 — the "tracker")
Phase: **Core Loop (Now–M2)** → then Companion AI → Prologue Arc → Full Invasion Stages → Upgrade →
Co-op → Polish → Racing → Launch. GM-* WOs follow this order, one phase-slice at a time.
