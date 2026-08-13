---
id: INT-9
title: "3D file viewer — enable the GLB/GLTF runtime loader (drop a 3D model → eLo shows it)"
owner_seat: SEAT-ENG-004 (UI/Avatar, Unity)
occupant: Game/UI (Unity)
priority: P2
reason: "David 2026-08-03: the 3D file view was meant to be implemented. It's ~90% built and just gated on a Unity scripting define."
review_required: L1 → L3 (David drops a model + sees it)
risk: low (project-settings + activating an existing stub)
status: READY — Unity-side (5-min settings flip + verify)
created: 2026-08-03
---
# INT-9 — enable the 3D file viewer

## State (grounded)
- **Python: done.** `desktop/file_drop_handler.py` routes .glb/.obj/.fbx/.stl/.usdz → writes `hud_model` path to blender_state + "opening in the viewer".
- **Unity viewer: built but gated.** `Assets/Scripts/EloHudModel.cs` reads `hud_model` and is meant to display the model — but the real loading is behind `#if ELO_GLTFAST`, and the define isn't set, so it just logs a warning.
- **Loader package: appears PRESENT** — `com.unity.cloud.gltfast` is in the project's PackageCache already.

## Task (small)
1. Confirm `com.unity.cloud.gltfast` is a project dependency (Package Manager). If present, no install needed.
2. Add scripting define **`ELO_GLTFAST`** (Project Settings → Player → Scripting Define Symbols).
3. Verify the `#if ELO_GLTFAST` path in `EloHudModel.cs` compiles + loads a .glb at runtime; fix any API drift vs the installed gltfast version.
4. End-to-end: drop a .glb on eLo → `hud_model` written → viewer displays it. Handle .obj/.fbx/.stl (gltfast is glTF-only; for others either convert or show Quick Look — keep the graceful fallback).

## Acceptance
1. Drop a .glb on eLo → it renders in the HUD viewer (not just a log warning).
2. Non-glTF (.obj/.stl) → graceful fallback (Quick Look / message), no crash.
3. David drops a model and sees it → DONE.

## Notes
- Unity-environment-bound (scripting define + runtime test) — needs the Game/UI agent or David in Unity ~5 min. Pairs with INT-8 (drag-drop). The whole path exists; this just switches the loader on.
