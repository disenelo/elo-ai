# 049-A — Moveset REFERENCE Contract (DRAFT rev.2)
**The desktop presence animations are a strong REFERENCE for the game; the game MATCHES the kinds of movement — it does NOT match identically.**

> Filed by **Game seat (SEAT-ENG-005)** 2026-08-05, per David: *"draft the contract and relay to Architecture; flag the risky PlayerController issue."* rev.2 corrects scope per David: *"the share is how the desktop-presence animations are a strong reference for the game and match the different kinds of movement, based on code or mixing animations — matching it identically would be a big risk."* **No code changed.** Review: L3 (David — the feel). Home: Vol XIII evolution + Spatial Faculty (WO-049).

---

## 0. What the share IS / ISN'T (David's principle)
- **IS:** desktop presence = a **reference library** of movement *kinds* and *feel*. The game **rebuilds each to match**, using its own **CODE** (procedural, ArmWave-style) or by **MIXING / blending animations** (blend trees, layers). The shared thing is the **movement vocabulary + feel** — not the assets.
- **ISN'T (⚠️ the big risks):**
  1. **Identical asset/rig sharing** — literally binding both embodiments to the same baked clips + exact bone names. Silent breakage (we already hit `c_arm_fk` missing + a head-bone mis-reference this migration) and cross-project coupling. **David: "match it identically would be a big risk."**
  2. **Porting the driver** — the game `PlayerController` (physics/input) onto the desktop, or vice-versa (see §3).

> One movement identity = the **same feel/vocabulary reached independently per body**, not one shared asset stack. "One planner, three embodiments" — planner/vocabulary shared, **implementations diverge on purpose.**

---

## 1. The shared VOCABULARY (the reference language), matched per-embodiment
Movement-Grammar verbs are the shared *language* (WO-049 CA). Each embodiment realises them its own way; the desktop version is the **reference**, the game **matches** it.

| Verb | Desktop reference | Game's match method (code / mix — its own build) |
|---|---|---|
| **WAVE** | `ArmWave.cs` (procedural raise+swing) | ✅ **code** — ported procedurally, body-local so it self-adapts. *The model example of "match, not clone."* |
| APPROACH | desktop walk/run nav | game `Walk`/`Run` + blend (own locomotion) — ⚠️ `Run` not firing yet (GM-2b) |
| LEAP | desktop jump/wall-jump | game `LongJump` + arc code / blend |
| PERCH · BALANCE · CLIMB · HANG · SLIDE · PEEK | desktop parkour (WO-049) | author to match the reference feel — code or new clips, game-side |
| REST / OBSERVE | desktop idle/meditate | game `Idle` / `Calm` states |
| FIRE (modifier) | (game-origin) | `GunFire-Run` / `Gun-Jump-Fire` — flows the OTHER way (game → desktop reference) |

Matching is **two-way as reference**: mostly desktop→game (this WO), but game-origin moves (gun-fire) can reference back to the desktop. Neither is the master asset.

---

## 2. HOW to match (sanctioned methods) — and what to avoid
- ✅ **Code (procedural):** additive, body-local, bone-driven (the ArmWave pattern). Robust across rig/orientation differences (handles the game's `baseX=270` automatically). **Preferred for gestures.**
- ✅ **Mixing animations:** blend trees / masked layers / cross-fades in the game's *own* controller to reproduce the reference feel. (Already how run↔gun-fire is built.)
- ⚠️ **Avoid:** wiring both embodiments to the *same* baked clip assets + identical rig-binding as the coupling mechanism. Reference the feel; don't share the asset as a hard dependency.

**Bone-name note (scoped, not a project-wide contract):** *when a specific CODE gesture is copied* (e.g. ArmWave), it binds bones by name and must **fail/log loudly** if a bone is absent — never silent no-op. That's per-gesture validation on the porting path, NOT a mandate that the two rigs stay identical.

---

## 3. THE DRIVER BOUNDARY — do NOT port (⚠️ the flagged PlayerController risk)
The game `PlayerController` / Animator state-machine / New-Input loop must **not** move to the desktop. It is coupled to **CharacterController physics** (gravity, `CC.Move`, 3D collision), **player input** (Shift/A/D/Space), and **params from that loop** (`IsSprinting`/`Speed`/`IsGrounded`/`Armed`). The desktop has **none** of these — it's screen-space windows, AI/goal-driven. Porting it = re-architecture, propagates game bugs (Run not firing), and is the *"animation hack that fakes awareness"* WO-049 forbids. Desktop driver = **Nav Planner / Spatial Faculty (Track B)**, requesting **verbs**; the game driver stays the game's. Each body actuates the shared vocabulary itself.

---

## 4. SEQUENCING
1. **GM-2 lands first** — don't hold up the desktop's *reference*, but the game's own moves (esp. `Run`, GM-2b) must work before the game is a clean reference target either direction.
2. Buildable now: this **reference contract** + the **code-gesture pattern** (ArmWave proves it).
3. New verbs (CLIMB/PERCH/wall-jump…) authored per body to match the reference — not shared as one asset.

---

## 5. RELAY TO ARCHITECTURE — decisions requested
- ✅ Scope corrected to **reference + independent match** (code or mixing), per David — **not** identical asset/rig sharing.
- ⚠️ **Two risks flagged:** (1) **PlayerController port** across embodiments (§3); (2) **identical asset/rig coupling** (§0/§2) — David: *"match it identically would be a big risk."*
- ❓ **Architect to ratify:** (a) the reference-not-clone model as canonical; (b) the verb vocabulary as the shared layer (assets stay per-body); (c) GM-2-first sequencing; (d) confirm home = Vol XIII evolution + Spatial Faculty.
