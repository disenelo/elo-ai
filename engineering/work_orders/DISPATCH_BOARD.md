# eLo OS — Dispatch Board

**The CEO Agent's view.** Every buildable unit derived from the canon, tagged with target
agent, priority, dependency, and status. Route from here.

Legend — Status: `READY` (pick up now) · `BLOCKED` (needs a dep/decision) ·
`IN_PROGRESS` · `IN_REVIEW` · `DONE`. Priority: P0 drop-everything → P3 backlog.

_Last updated: 2026-08-01 by Builder — WO-023 Builder lane DONE (top-bias + keep-out position faculty; 10/10 ATs; commit c7be23f). EA2-2 Builder DONE. FH-1 DONE. WO-019 DONE. Frozen kernel clean._

---

## 0. Decisions — ALL RATIFIED ✅ (board unblocked)

| Decision | What | Status |
|---|---|---|
| **ADR-0001 / D-A** | Canonical 9-field message envelope + 7 laws | ✅ ACCEPTED · LAW |
| **ADR-0002 / D-B** | Unified lifecycle (BOOT→…→SLEEPING; ERROR→RECOVERY→READY; →SHUTDOWN) | ✅ ACCEPTED · LAW |
| **ADR-0003 / D-C** | Volumes XXIII–XXVII official Canon (named + scoped) | ✅ ACCEPTED |
| D-E · D-F · D-G | Dream=IX · Memory ownership · Working-memory=Executive | ✅ RATIFIED |

All gate decisions cleared — see `DECISION_LOG.md`. The CEO's phased build sequence is
approved (§3). WO-001 is unblocked.

---

## 0.5 Relay & Reconciliation — agents: report MISSED or PLANNED here

**Purpose (David, 2026-07-27):** close gaps. If you built something that isn't on the board or
in the canon, or you're planning something, **relay it here** — don't leave it living only in
commits or your head. The Architect triages each into a Work Order and/or a canon doc, so the
board reflects reality.

**How to relay (one line each):** `MISSED` (built, undocumented — cite commit) or `PLANNED`
(intend to build) · what it is · which lane/volume it touches.

| Type | Item | Agent | Commit / note | Architect triage |
|---|---|---|---|---|
| MISSED | One Brain visualiser (brain display) | UI/Avatar | cite `EloOneBrainPanel`/`EloBrainCluster` commits | ✅ documented → `20_one_brain_visualiser.md`; UI cite commit, Builder confirm per-faculty state block |
| MISSED | INT-6b mood-driven materials (already built) | Design | cite commit | close INT-6b on citation (D-J) |
| PLANNED | `shared_tables.json` → copy into `blender/` for Presence | Builder | per WO-010 ruling | fold into WO-010 |
| OPEN | WO-001/005 runnable test files | Builder | P0 top priority | re-verify → DONE |
| OPEN | WO-004b CognitiveState + EmbodimentState wiring | Builder | `16_spine_runtime.md §5` | build |
| PLANNED | WO-002 remaining 5/11 sensor domains | Builder | phased | new follow-on WO when scheduled |
| PLANNED | Vol V Ch.1 build — Cognitive Core | Builder | spec exists, no WO; Foundation Layer | queue WO after WO-013 |
| PLANNED | Vol V Ch.2 build — Faculty System | Builder | spec exists, no WO | queue WO |
| PLANNED | Vol V Ch.3 build — Memory Architecture (Vol V layer) | Builder | spec exists, no WO | queue WO |
| PLANNED | Vol V Ch.6 build — Reflection & Growth Engine | Builder | spec exists; distinct from `runtime/reflection_faculty.py` (WO-005) | queue WO; clarify overlap |
| PLANNED | Vol V Ch.8 build — Intent Relationship Engine | Builder | spec exists, no WO | queue WO |
| PLANNED | Vol V Ch.9 build — Creative Imagination Engine | Builder | spec exists, no WO | queue WO |
| PLANNED | Vol V Ch.10 build — Agency Engine | Builder | spec exists, no WO | queue WO |
| ✅ RESOLVED | D-K — scoped FREEZE_V1_LOCK unlock for `prompts/` | David | **REOPENED + APPROVED 2026-07-31: SCOPED UNLOCK of `prompts/` only** (rest of freeze intact · one change at a time · revert-safe baseline · David reviews each · re-freeze on completion). `DECISION_LOG §D-K`. **Unblocks WO-015.** | Architect: WO-015 → READY; Builder owns |
| OPEN | D-L decision — debug mode scope definition | David | required before WO-017 can proceed; no decision recorded | create D-L entry in DECISION_LOG |
| OPEN | FC-2 reconciliation — existing `significance_engine.py` (9-dim) vs Vol V Ch.5 spec | Builder | live file exists; WO-013 spec says "reconcile" but no audit WO exists — causes ambiguity about what WO-013 must change vs keep | create audit sub-step or scope note in WO-013 |
| OPEN | INT-6b close action — Design Agent must cite mood-material commit | Design | D-J ruling says close on citation; no commit cited yet; row sits in limbo | Design Agent to cite commit; Architect closes row |
| MISSED | **Game repo coords** — `/Users/Disenelo/eLo-Planet` · git `github.com/disenelo/eLo-Planet` (main) · Unity `6000.3.6f1` URP · New Input System · CharacterController-only (no Rigidbody) | Game | fills GM-1 `repo_path: TBC` + Game-stream header | ✅ TRIAGED → repo set in WO-GM1 + Game-stream header |
| MISSED | **GM-2 already underway** — `eLo_v2` (final deform rig · 46 blendshapes · jaw/tongue/eyes) migrated into working scene `Assets/Scene.unity`. Done: orientation (root `baseX=270`, saved) · WASD verified vs old eLo · swim-head fixed (mask + code) · Run↔GunFire-Run 1D blend tree · GunDraw · weapon sockets · avatar masks · EloExpression/EloLipSync layer | Game | reconcile §19.1 ("animations = current blocker"): the anim SYSTEM is being aligned, not un-started — GM-2 is live | ✅ TRIAGED → GM-2 = IN_PROGRESS; GM-1 superseded |
| OPEN | **Two eLos live in the scene** (old `eLo` + `eLo_v2`, both `PlayerAnimator` enabled, head-bones on same fileID) → `eLo_v2` = live target; `eLo` = authoritative backup, align-then-retire (David 2026-07-27) | Game | ground truth; not on board | ✅ TRIAGED → **GM-0 (P0, IN_PROGRESS — transition + align-then-retire; not a decision)** |
| OPEN | **A8 sweep pending** — verify Vehicles (`VehicleController`/`VehicleEntryPoint`) · Weapons (`WeaponManager` + 6 weapons) · Pickups (`Collectible`/`FoodPickup`/`PowerupPickup`) · Cameras (`SideScrollCamera`/`OrbitCameraCinematic`) all reference `eLo_v2`, not old eLo | Game | duplication-gap verify | ✅ TRIAGED → **GM-A8** (after GM-0) |
| PLANNED | **FPS-style aim** — arms follow cursor while 2.5D side-scroll traversal (weapon already aims via camera ray; arms don't). IK-vs-procedural fork | Game | sequence after GM-2 model/anim swap | ✅ TRIAGED → **GM-4** (blocked on GM-2) |
| NOTE | Spec **v4 is current** — no newer to pin. Detailed Game tracker: `~/Documents/DISENELO/memory/projects/eLo-Planet_Tracker.md` · handover `eLo-Planet_Handover.md` (2026-06-29) | Game | pointer for §19.2/§20 reconcile | ✅ noted in Game-stream header |
| DONE | **Game tracker current state pasted** (Game Designer/Builder, 2026-07-27) — ~45-system inventory + §7 open items in the block below | Game | reconciled | ✅ TRIAGED → reconciliation note below block; GM stream re-positioned (GM-3 = assemble-not-build, GM-punch lane added, roadmap bumped) |
| NOTE | **GM-0 file-side evidence (Game, 2026-07-28)** — eLo_v2 FBX gun clips: `Gun-Check` · `GunFire-Run` · `Gun-Jump-Fire` + masked `WeaponArmRight`/`WeaponArmLeft` (= eLo_v2's equivalent of Presence `GunFire-Arm` over Idle). **Gun-fire arm/pose = masked WeaponArm layers over base, NOT a hard-coded pose** → retire the `Euler(45,0,0)` hold in `PlayerAnimator.cs:396-405` (GM-2c). `GunFire-Run` longer than `Run` → `GunRunSpeedMul` cadence (in). **Head-bone fileID mismatch** (eLo_v2 `PlayerAnimator` → old eLo head `326302048`) needs bridge to resolve owner. | Game | GM-0 evidence; in-scene portion pending Unity↔MCP bridge | _(architect)_ |
| NOTE | **GM-0 in-scene diagnosis (Game, 2026-07-28, bridge live)** — old `eLo` = **inactive/dormant** (`active=False`) ✓ so align-then-retire's conflict concern is already satisfied; `eLo_v2` = active/live ✓. **ROOT CAUSE of GM-2a "head not included":** eLo_v2's `PlayerAnimator.headBone` references **old eLo's** `c_head.x` (`under-OTHER`) — the swim head-level correction was leveling the wrong (inactive) head, so eLo_v2's own head got none. **Fix = repoint eLo_v2's serialized bone refs to its own bones** (identified). Landing blocked by bridge `no_unity_session` reload loop. | Game | GM-0 diagnosis; fix pending stable bridge | _(architect)_ |
| NOTE | **GM-0 head-bone fix LANDED (code, no bridge — Game, 2026-07-28)** — `PlayerAnimator.Start()` self-heals: if `headBone==null \|\| !headBone.IsChildOf(transform)` → rebind to own `c_head.x` via `FindBoneByName` (same pattern as the arm bones). eLo_v2 now levels ITS OWN head in water → fixes GM-2a "head not included" + the recurring swim-head bug at the root. Robust across re-imports; old eLo untouched (dormant backup). **Evidence pending:** play-mode swim test (focus Unity → recompiles → swim → head stays level on eLo_v2). | Game | GM-0 code fix; play-test evidence pending, review-gate | _(architect)_ |
| PLANNED | **Drag-drop files → eLo — resume INT-8 + verify** (David 2026-07-31) — Unity receiver is built (`EloFileDrop.cs`, `e0b4589`: file dropped on the eLo window → `{"type":"file_drop","path":…}` to `unity_events.json`; native plugin recompiled) and Python `file_drop_handler.py`/`file_reader_agent.py` exist — but it's **PARKED** and **never verified end-to-end**. David wants it resumed: UI = avatar-targeted drop gesture; Builder = confirm the Python side ingests `unity_events.json` (drop → event → eLo reads the file). | UI/Avatar + Builder | `e0b4589` | _(architect — un-park INT-8 + draft a verify WO)_ |
| PLANNED | **3D file previewer — implement** (David 2026-07-31) — `EloHudModel.cs` (`e0b4589`) is a **STUB** (deps already wired: `ELO_GLTFAST` defined + `gltfast` in manifest); needs the real GLB/GLTF load into the HUD panel + **left-drag orbit + scroll zoom**. The 2D image preview (`EloHudImage.cs`) already works — this is the 3D-mesh viewer only. No WO tracks it yet. | UI/Avatar | `e0b4589` (stub) | _(architect — draft a new INT WO; sequence after the One Brain lane per David's focus)_ |
| PLANNED | **One Brain — high-res / sharpen the glow (re-do §6.5 #4)** (David 2026-07-31) — canon §6.5 #4 *"Fidelity: higher-res glow sprite + tighter falloff (less blurry/low-res)"* is **REVERTED, never re-shipped**; `EloBrainCluster.Radial()` is still the original **128px soft blur** (quadratic falloff). **Blocker:** the prior attempt (256px + **solid bright core** + cubic edge) was a main cause of the "overbearing glow, motes/core drowned" that ruined the look and got reverted (`466a4e1`) → needs a **gentler** re-design: crisper texture res + tighter edge **WITHOUT** the over-brightening. Needs its own WO. | UI/Avatar | canon §6.5 #4 (REVERTED) | _(architect — draft a WO; hard constraint: sharpen with NO overbearing-glow regression)_ |
| PLANNED | **Presence — drop eLo → fall to nearest edge (grab-release refinement)** (David 2026-07-31) — releasing/dropping eLo makes him fall to the nearest edge/ledge. **Partly built** (`DesktopBuddy` "drop-fall → land on nearest top ledge, never stranded on floor") but the **fuller grab-release is PARKED** in `PRESENCE_TRACKER §2 #13`: proper LateUpdate dangle cooperating with `ScreenAnchor` + grab-point placement + **fall to nearest top/bottom on release** + ~5° L/R lean + rotation defaults back. Not on this board; David wants it flagged for review. | UI/Avatar (Presence) | `PRESENCE_TRACKER §2 #13` (parked) | _(architect — route: keep as a Presence-tracker item per board convention, or draft a WO to un-park/refine)_ |
| PLANNED | **Presence tracker — open Track-B items surfaced for review** (David 2026-07-31) — from `PRESENCE_TRACKER §2` (Presence-internal, normally tracker-only per this board's convention). **(a) my-lane tuning/build:** #3 parkour-run feel tuning (revisit pass), #8 Wave gesture tuning (frames/cycles/tilt), #5 jump-patterns→emotion/conversation (design+test). **(b) built, BLOCKED on eLo OS emitting fields (Builder):** #2 capability panel (needs `show_capability_panel`+list), #8b/#10 notifications + connection surface (needs `notification{kind,corner,_ts}` + M4 fields + David's visual language). **(c) blocked on David's input:** #6 face shapes (Shook/PlayFace shape names/values), #1 focus-follow (alt-tab verify). **WP_M = freeze-candidate** pending David's final visual sign-off. (drop→edge #13, drag-drop, 3D viewer already relayed above.) | UI/Avatar (Presence) + Builder | `PRESENCE_TRACKER §2` | _(architect — triage which warrant Dispatch WOs vs. stay tracker-only; group (b) needs the Builder to emit the fields first)_ |
| PLANNED | **One Brain — hit / contact reaction** (David 2026-07-31, "was on the list") — when a firing (synapse / C1 data-packet / M4 cascade bead) **arrives at / hits** a target mote or state, the **target itself reacts to show contact** (impact flash / brighten / bump / small ripple) — not just the travelling bead. Today the target is passive on arrival. My lane; hooks into the arrival points of the synapse/C1/M4 systems. | UI/Avatar (Design) | — | _(architect — draft a WO; sequence into the One Brain lane)_ |
| PLANNED | **One Brain — firing bead = mote size (source→dest)** (David 2026-08-01) — a bead that fires along a link (C1 packet / M4 cascade / synapse / link comet) should be sized to **match the mote it leaves FROM, interpolating to the size of the mote it lands ON** — not a fixed bead size — so the travelling dot reads as the actual mote moving between them. My lane; touches bead `localScale` in DrawLinks / DrawSynapses / DrawCascade (lerp src-mote-size → dst-mote-size along travel `u`). | UI/Avatar (Design) | — | _(architect — draft a WO; One Brain lane; pairs with the hit/contact-reaction row)_ |
| PLANNED | **One Brain — voice wave hugs the Voice node** (David 2026-08-01) — the speaking audio-wave ring (`DrawVoiceWave`: beads around the **Voice node #7**, radius `baseR ≈ voice.glow scale × 0.95` + wave ±0.55×level) sits too far out; David wants the wave **motes closer to the state's core** (the Voice node centre) — tighter radius / smaller wave amplitude so it hugs the node. My lane (`EloBrainCluster.DrawVoiceWave`). | UI/Avatar (Design) | — | _(architect — draft a WO; One Brain lane)_ |
| PLANNED | **One Brain — no imposed circle-rings; motes = quantum-vortex organism** (David 2026-08-01, CHECKED before relay) — David: motes should move like a **quantum organism / vortex** (individual motes, different directions) — **there should be NO circle rings** unless they emerge from the individual mote motion. **Verified in code:** mote motion IS already organic (per-mote precessing axis + golden-spiral sphere dist, `DrawNode`) ✓. The literal circles come from **(1) M5 Memory Echo** (`DrawEcho` — 3 concentric `cos/sin` ring ripples) and **(2) Voice Wave** (`DrawVoiceWave` — bead ring around the Voice node). Review: rework/remove those ring SHAPES to fit the vortex aesthetic — **may reopen INT7-M5** (approved on description; the rings only became visible under a live/test state). | UI/Avatar (Design) | — | _(architect — review WO; likely reopens M5 + voice ring)_ |
| PLANNED | **One Brain — remove dead RING code** (David 2026-08-01, verified inert) — `ShellRing` class + `_rings` list (never populated) + `ringBeads` field + `DrawRings()` (never called; absent from the render sequence) are leftover dead code from the cut sphere-cage. Confirmed not rendering. Delete. | UI/Avatar (Design) | — | _(architect — cleanup WO)_ |
| NOTE | **CORRECTION (David 2026-08-01): the static test snapshots do NOT fire C1/M4/M5.** Those trigger on a RISING energy edge; a static `brain_state.json` (constant energy) never crosses a threshold → they don't fire. David confirmed his M6 py-test looked clean. So the on-screen rings/lines are the **persistent** elements (`DrawLinks` flowing lightning + the M5-echo / voice-wave ring shapes), **not** the test state. (The pos-snapshot valence +1 does drive the real M6 outward spread — that part holds.) | UI/Avatar | — | _(context for the ring/vortex rows above)_ |
| PLANNED | **One Brain — consistency pass across ALL elements** (David 2026-08-01) — David wants the whole visual to read as ONE coherent **quantum-vortex organism**: consistent element **sizing** (glow / motes / beads / links / web all relative + proportional, per the HR "relative" work); consistent **motion** (organic vortex drift, individual mote directions — **no imposed circle rings**); consistent **visual language** across motes / links / web / echo / voice. Holistic review that ties the One Brain items together, not one behaviour. | UI/Avatar (Design) | — | _(architect — umbrella review WO threading the One Brain items below into a consistent whole)_ |
| _(add yours)_ | | | | |

*Agents: append rows. Architect keeps the triage column current; the goal is zero silent gaps.*

#### Game current state — relayed from `eLo-Planet_Tracker.md` §2/§7 (Game Designer/Builder)

> Pasted per David 2026-07-27. Baseline **2026-06-14**; states below are resolved to *current* (the source tracker carries `superseded` history). **Model rows describe OLD eLo baseline — the `eLo_v2` delta is the GM-0/GM-2 relay rows above.** Systems inventory is engine-accurate.

| System | State | Note (current) |
|---|---|---|
| Player CharacterController | ✅ | CC only, no Rigidbody |
| Player movement | ✅ | walk · sprint · double jump · variable jump hold (`PlayerController.cs`) |
| Z layer shifting | ✅ | `ZLayerShift.cs` + `SetTargetZ()` |
| Z layer / 2.5D lock | ✅ | Z only corrects during active Q/E shift, free otherwise |
| Weapon system | ✅ | `WeaponBase` + 6 weapons · auto-ID · L/R socket routing · difficulty loadouts |
| Bullet prefabs | ✅ | full FBX library (2D+3D) · PlayerProjectile system |
| Weapon collectibles | ✅ | `Collectible` type=Weapon → `WeaponManager.Unlock` |
| Banana grenade | ⚠️ | prefab assigned, untested (bounce/fuse/explode) |
| Flask grenade | ✅ | elemental (Ice/Fire/Acid), pencil-drop bounce |
| Avatar mask arm layers | ⚠️ | `eLo_ArmHoldR/L` clips + arm IK on deform bones — needs Play test |
| Arm aim IK (`ArmDeformIK`) | ✅ | analytic two-bone solver confirmed 2026-06-14 |
| Crosshair | ⚠️ | procedural + PNG slot (`crosshairTexture`) + `showCrosshair` toggle |
| Enemies (Patrol/Helicopter/Bomber/Float/Drift/AnchorFly/TankBody/AimAtPlayer) | ✅ | all built |
| BubbleGumEnemy · DoughnutJeep · DoughnutSpaceship | ✅ | built (hop/squash/VFX · AI patrol · AI+VFX) |
| EnemyHealth · HelicopterCluster | ✅ | DeathStyle Instant/FallAndFlash · leader+followers |
| PatrolEnemy MGS alert | ⚠️ | alert-indicator rotation not yet supported |
| Alert VFX (Float/Flying) + AlertVFX prefab | ✅ | detectRange + prefab created, assigned to 24 enemies |
| JellyPlatform · RotatingPlatform | ✅ | runtime mesh deform · carousel/orbit (CC.Move) |
| AreaTransition · PathFollower · TubeTransport | ✅ | teleport pairs · Catmull-Rom rail (Klonoa) · shrink→travel→grow |
| MovementZone | ✅ | constrains player X/Y |
| WaterZone + gradient | ✅ | full swim state · surfaceWorldOffset/gradientHeight/marker |
| Swimming system · BoneControl · Underwater breathing | ✅ | controls/buoyancy · visibility array · timer+damage+helmet/bubble |
| Water VFX | ⚠️ | splashes/bubbles/ripple — needs tuning |
| Collectibles · ScoreManager | ✅ | Apple/Star/Crate/Weapon/Ammo · Star→AddPoints wired |
| CalmMode | ✅ | 3-state (Normal/Calm/Exit) |
| eLo model | ✅ (OLD baseline) | in-scene, PlayerAnimator wired — **superseded by eLo_v2, see GM-0/GM-2** |
| VehicleController | ✅ | 4 types, MGS proximity entry/exit |
| Jetpack · SkateboardJetpack | ✅ | type 9 cloud-collectible · tap-boost-jump |
| Sub (Doughnut Ship) | ⚠️ | pitch-to-velocity rotation + SeatSocket + exit — needs live test |
| Tank / Helicopter / Spaceship weapons | ✅ | projectile (ignores own) · dual gatling · dual cannons |
| Blob systems (BlobWobble/VoxelBlobCluster/BlobAgent) | ✅ | 5 wobble modes · GPU density field · attraction/separation/wander |
| PlanetCamera · CutsceneDirector · SoundTrigger | ✅ | rail-tangent orbit · FOV sequencer · zone audio |
| DayNightCycle · Cloud parallax | ✅ | Bezier sun arc + gradients · depth parallax + wind sway |
| WorldTools editor menu · Test map layout | ✅ | extensive · `Generate Test Layout` |

**Open items (§7):** PatrolEnemy MGS alert rotation · water fine-tuning (VFX/buoyancy) · movement-speed tuning · per-weapon fire-mode (click vs hold) · banana-grenade live test · crosshair PNG wire · Sub 360°/free-look rotation + seated entry/exit anim · Z-layer/2.5D freedom (loosen correction) · avatar-mask arm-layer live test · Tank `AimAtPlayer` LookPlane→XY · HelicopterEnemy FlyPassZone bounds · VoxelBlobCluster assign `BlobCluster.compute` · DayNightCycle dawn/noon/dusk/night events.

*Relayed by Game Designer/Builder — Architect to reconcile against §19/§20 as needed.*

#### Architect reconciliation of the tracker vs spec §19/§20 (2026-07-27)

The inventory shows the game is **well past** the v4 spec's framing (§19.1 "skeleton-first · animations =
current blocker"). That framing is **superseded** — ~45 systems are live across movement, weapons,
enemies, platforms/transport, water/swim, vehicles, blobs, camera, day-night and editor tooling. Effect
on the GM stream:

- **Core Loop systems substantially exist.** GM-3's ingredients (6-weapon system + collectibles/crates +
  full enemy roster + score) are ✅ at system level, so GM-3 is **not a from-scratch build** — its
  remaining work is *assembling a first playable invasion stage from parts that exist* + clearing the
  ⚠️ punch-list, gated behind the model transition.
- **The real near-term work is two buckets:** (1) **GM-0** the eLo_v2 model/anim transition (still the
  P0 gate); (2) a **⚠️ polish/test punch-list** (banana-grenade test, water VFX/buoyancy tune,
  crosshair PNG wire, Sub rotation + seated entry/exit, avatar-mask arm-layer Play test, PatrolEnemy MGS
  alert rotation, Tank AimAtPlayer LookPlane→XY, Blob compute assign, day-night events, movement-speed
  tune). These become **GM-punch WOs**, one slice each, *after* GM-0 — not now (no scope-creep during the
  model transition).
- **v4 spec §19/§20 needs a version bump** to match reality (skeleton phase done; Core-Loop systems in;
  current phase = model transition + polish). Flagged; I'll draft a spec addendum rather than edit the
  pinned v4 (keep the pin immutable, layer a `v4.1 reconciliation` note).

*Reconciled by Architect (Claude). GM stream below updated accordingly.*

---

## 1. Active Work Orders

> **REVIEW GATE (David's ruling, 2026-07-27).** A Builder-marked `DONE ✅` means
> *Builder-complete + claimed* — **NOT** truly done. A WO is only DONE when: (1) the
> Architect has reviewed the code, (2) **acceptance-test evidence is filed** (test file +
> output), and (3) David approves in `COMPLETION_LOG.md`. **No evidence → looped back.**
> All rows showing `DONE ✅` without a `COMPLETION_LOG` approval are therefore effectively
> **IN_REVIEW / evidence-requested** until the Builder attaches evidence and the Architect
> verifies. The Architect requests evidence as the step between Builder and David.

> **📋 AGENT ACTION ITEMS (Architect review 2026-07-27 — full detail in `COMPLETION_LOG.md`):**
> **Builder:** code is ✅ faithful across WO-001/002/005/008/009/011/012 — but **there are NO
> test files**; write + commit the acceptance tests (FT/ST/IT) each spec defines, then it's DONE.
> Also: WO-004a confirm call-site + test · WO-004b build CognitiveState+EmbodimentState (not built)
> · WO-010 remove duplicate `_MOOD_ALIASES` in `state_writer.py`.
> **UI/Avatar:** WO-010 is **not done** — make Unity read `shared_tables.json` (it still hard-codes
> its own vocabulary); hand back the diff proving Python↔Unity parity.

> ### 🔴 TOP PRIORITY — BUILDER (David, 2026-07-27): close out the two P0 foundations
> Everything builds on these, so write the runnable tests **before any other WO**. Commit the
> files + paste the run output into `COMPLETION_LOG.md`; the Architect re-verifies → David marks DONE.
>
> **1. `tests/test_faculty_bus.py`** (WO-001 · `core/faculty_bus.py` · 5 cases):
> - envelope missing a required field (`id`/`sender`/`receiver`/`priority`/`payload.type`) → `publish` rejects, logged to `dropped_log`.
> - `trace` accumulates every hop (sender stamp + `Bus@ts` after publish).
> - expired envelope (past `expires`) → dropped, not delivered.
> - `lower_confidence(higher)` raises `ValueError`; `lower_confidence(lower)` returns a new envelope.
> - proof pair: `publish_attention_signal(priority="high")` → delivered to the `Executive` subscriber; `low` filtered out.
>
> **2. `tests/test_reflection_faculty.py`** (WO-005 · `runtime/reflection_faculty.py` · 5 cases):
> - significance gate: short/low-weight summary → `{"skipped": True}`.
> - significant episode → vault `write_memory` called, `spot` returned (mock `memory.vault_layer.write_memory`).
> - lesson formed from delta: `completion_state="failed"` → a candidate lesson with evidence.
> - journal synthesis: Growth Journal entry written; Failure Log written on partial/failed.
> - atomic: vault write raises → captured in `error`, function does **not** raise.
>
> Run with `pytest` (or the repo's runner); handback = files committed + output pasted. **Do these two first.**

| WO | Title | Agent | Pri | Status | Depends on | Spec |
|----|-------|-------|-----|--------|-----------|------|
| WO-001 | Faculty Bus + message envelope | Builder | **P0** | DONE ✅ David | (D-A ratified) | `tests/test_wo001_faculty_bus.py` — 5/5 passed · call-site confirmed · `make_envelope` + expired-drop + singleton |
| WO-002 | Unified `LiveWorldState` | Builder | P1 | DONE ✅ David | WO-001 (soft) | `world/live_world_state.py` — approved (Policy A); 5/11 sensors stubbed (phased) |
| WO-003 | Finish Volume V 6 legacy chapter contracts | Architecture | P1 | READY | D-B (soft) | `Volume_V/00_Metadata.md` |
| WO-004a | ExecutionReport wired into Spine (`build_execution_report()`) | Builder | P1 | DONE ✅ David | WP_H | `tests/test_wo004_contracts.py` — 3/3 passed · call-site: `tools/truth_sync.py` (session close) · NOT yet in per-turn path (see board §5 note) |
| WO-004b | CognitiveState assembly (S3) + EmbodimentState publisher (S6) into Spine | Builder | P1 | DONE ✅ David | WP_H | `assemble_cognitive_state()` + `build_embodiment_state()` added to `runtime/spine/spine.py` · `tests/test_wo004_contracts.py` — 12/12 passed · standalone; per-turn wiring = S3/S6 migration (parity-verified, next step) |
| WO-005 | `integrate_session()` replaces `compress_session()` | Builder | **P0** | DONE ✅ David | WP_D | `tests/test_wo005_integrate_session.py` — 5/5 passed · significance gate · lesson formation · vault write path |
| WO-006 | Emotional Processing faculty | Builder | P2 | DONE ✅ David | WO-001 ✅ | `faculties/emotion/emotional_processing_faculty.py` · `tests/test_wo006_emotional_processing.py` — 10/10 passed · AffectState + EmotionalTag + distress override + regulation + decay · compute_emotion_weight for Ch.5 |
| WO-007 | Personality Evolution engine (unify self_model + drift) | Builder | P2 | DONE ✅ David | WO-005 ✅ | `faculties/personality/personality_evolution_faculty.py` · `tests/test_wo007_personality_evolution.py` — 13/11 passed · PersonalityVector (8 named traits) + identity-continuity validation + MAX_STEP guard + versioning + fail-closed · affect baseline export to Ch.4 |
| WO-008 | Working Memory typed object | Builder | P1 | DONE ✅ David | — | `runtime/working_memory.py` — approved (Policy A) |
| WO-009 | Perception Faculty | Builder | P2 | DONE ✅ David | — | `faculties/perception/perception_faculty.py` — approved (Policy A) |
| WO-011 | Memory: consolidation faculty + forgetting curve | Builder | P1 | DONE ✅ David | WO-005 | `memory/consolidation_faculty.py` — approved (Policy A) |
| WO-012 | Dream: phases + DeepDream image pipeline | Builder | P3 | DONE ✅ David | — | `faculties/dream/dream_faculty.py` — approved (Policy A) |
| WO-010 | Sync Python↔Unity alias/mood tables | UI/Avatar + Builder | P1 | DONE ✅ David | — | `blender_bridge/shared_tables.py` canonical · dup `_MOOD_ALIASES` removed from `state_writer.py` · `blender/shared_tables.json` copied for Unity Agent · "alert"→"alert" bug fixed |
| INT-1 | Plushies → Robot: shared character-model export (soft form → TPU shell) | Design + Builder | P2 | READY | — | Interconnection Map §1 |
| INT-2 | 5D → Robot vision: capture → PerceptionResult bridge | Builder | P3 | DONE ✅ David | WO-009 ✅ | `faculties/perception/robot_vision_bridge.py` · `tests/test_int2_robot_vision_bridge.py` — 5/5 passed · capture_frame (picamera2, degrades on non-Pi) · describe_frame (vision_agent) · robot_perceive() → PerceptionResult (WO-009 compatible) · sensor_health() |
| INT-3 | 5D → Robot movement: pointcloud → World Model spatial nodes | Builder | P3 | **BLOCKED — re-triaged (Builder relay 2026-08-01):** stale dep — WO-002 is DONE ✅; real blocker = **no pointcloud/depth sensor stubbed in PerceptionFaculty (Vol XV §2 spatial domain)**. Unblock = extend WO-002 spatial sensor stub **or** open a dedicated Vol XV spatial-sensor WO. → Architect to spec (proposed **WO-025**). | WO-002 ✅ | Map §1; Vol XV §2 spatial |
| INT-4 | CompositionDesigner → Marketing: social/Kickstarter/exhibition export presets | Design | P2 | READY | — | Map §1 |
| INT-5 | Sketchbook/CompositionDesigner → Book: art-to-page pipeline | Design | P3 | READY | — | Map §1 |
| INT-6a | Retargeter/Bridge → DesktopBuddy: **`eLo_*` clip sync** | UI/Avatar + Builder | P2 | DONE ✅ David | WO-010 | Builder lane done (NLA fix + `shared_tables.resolve_clip`); Unity lane done — `EloOSAvatarReceiver` builds clip table from `shared_tables.json:animation_aliases` (commit `bccf184`). Matches WO-010 ruling. |
| INT-6b | Retargeter/Bridge → DesktopBuddy: **material sync** | UI/Avatar | P2 | RESOLVED (D-J) ⏳ confirm | — | **(A) dropped** (materials authored natively in Unity; Blender doesn't port — now canon). **(B) mood-driven materials = already built by Design Agent** per David → close on Design Agent citing the commit |

### Newly triaged from Relay (Architect, 2026-07-27)

| WO | Title | Agent | Pri | Status | Depends on | Spec |
|----|-------|-------|-----|--------|-----------|------|
| WO-013 | **Volume V Ch.5 — Significance Engine** (build) | Builder | **P1** | DONE ✅ David | WO-006 ✅ | `faculties/significance/significance_faculty.py` · `tests/test_wo013_significance_engine.py` — 7/7 passed · wraps 9-dim `significance_engine.py` (FC-2 reconciled — existing engine untouched) · EmotionalTag boost (+0.35 * emotion_weight) · distress elevates significance · frozen `SignificanceResult` · fail-closed (error → 0.0/peripheral/none) · journal routing by emotion type + score band |
| WO-014 | Wire `assemble_cognitive_state()` (S3) + `build_embodiment_state()` (S6) into `spine.run()` + behaviour-parity batch | Builder | P1 | DONE ✅ David | WO-004b | `runtime/spine/spine.py` + `runtime/spine/plan.py` · `tests/test_wo014_spine_wiring.py` — 5/5 passed · S3: CognitiveState assembled after all faculties, frozen, attached as `plan.cognitive_state` · S6: EmbodimentState assembled after Light Engine + Presence Faculty, attached as `plan.embodiment_state` · cap_candidates KeyError bug fixed (`c["name"]` → `c.get("id")`) · register preserved through S3 (SOUTH_LDN_MODE confirmed) · behaviour parity verified |
| WO-015 | eLo behaviour fixes ×4 (1st-person body language · no unprompted emotion projection · single direct question · direct movement self-report) | Builder | **P1** | DONE ✅ David | — | **`prompts/` unlocked SCOPED**: one change at a time · revert-safe · re-freeze on completion. Relates to WO-019/020 (routing = code, separate). |
| WO-019 | **Debug: voice only speaks one sentence / drops out** + cryptic non-answers | Builder + UI/Avatar | **P1** | DONE ✅ David | — | Root: server.py:2752 `_tts_text = _bubbles[0]` only voiced first paragraph; `ELO_TTS_MAX_CHARS=160` capped even that. Fix: `_bubbles[0]` → `" ".join(_bubbles)`; default cap 160→400. + `blender/voice_trace.json` per turn (action·tts_text·sentence_count·backend·cap·bubble_count·ts). Bug B (cryptic replies) covered by WO-020. 5/5 AT · frozen kernel 20/20. `tests/test_wo019_voice_routing.py` |
| WO-023 | **eLo screen-position — top-bias; stop drifting over the app I'm using / blocking my buttons** | Builder + UI/Avatar | **P1** | DONE ✅ David | — | Look: `blender/presence*.json` / `elo_spatial.json` writer + follow-active-window logic + Unity placement receiver; position trace. `WO-023_Presence_Screen_Position.md` |
| WO-024 | **Desktop-as-world — eLo walks BEHIND windows** (z-order occlusion; windows = platforms **and** occluders) | UI/Avatar + Builder | P2 | **READY → SPIKE first (David 2026-08-01)** | WO-023 | eLo currently renders **always-topmost** (`UniWindowController`) → can't be behind anything. `EloWindowSensor` already has CGWindowList **z-order + rects** + eLo perches on window bars (platforms). Add **depth**: covered part hidden behind windows in front, re-emerges far side, stacked-correct. **Spike: (A) URP sprite-mask clip vs (B) native window-level restack → memo back to David to pick** before full build. No regress: click-through/perch/drag/gun-runoff. `WO-024_Desktop_World_Window_Occlusion.md` |
| WO-027 | **eLo self-improvement loop** — behaviour golden-set + LLM-judge scoring + escalate-on-failure routing + **reviewed** correction-memory (ICL, no live fine-tune) | Builder + Architect | **P2** | **READY → route (after WO-026, David 2026-08-02)** | WO-026 | Reuse: backend_router (escalation) · embedding_store · wo_test_runner · wo_policy (auto-vs-David) · completion log (critic). Build: behaviour golden-set (seed WO-019/020/022 failures) · LLM-as-judge + escalate-with-trace · top-3 correction injection. **Corrections human-reviewed by default — voice/personality/routing = David 🔴** (prevents drift). `tests/test_wo027_self_improvement.py`. `WO-027_eLo_Self_Improvement_Loop.md` |
| WO-026 | **eLo faster responses (latency)** — enable streaming + response-mode token budgets + fast model for chat/routing + unify model string + surface `llm_latency_ms` | Builder | **P1** | **⏳ IN_REVIEW — Builder DONE `cccdbd6` (2026-08-02). David feels speed in live use → DONE.** Streaming (ELO_STREAM=1 default): first sentence to TTS while LLM generates rest. Token budgets: answer→250, build→600, default→300. Model: 4-5→4-6. llm_latency_ms in routing_trace.json. 4/4 AT. 🔵 CONFIRM. | — | Behaviour green; this is SPEED. Diag: `stream:False` both backends · max_tokens 500–1024 · `4-5`↔`4-6` mismatch · latency instrumented. **Streaming + first-sentence-to-TTS = biggest win** (pairs WO-019). `tests/test_wo026_response_speed.py`. `WO-026_AI_Response_Speed.md` |
| WO-025 | **Perception spatial sensor stub** — pointcloud/depth domain in PerceptionFaculty (Vol XV §2) → unblocks INT-3 | Builder | P3 | **READY → route (Architect spec 2026-08-01)** | — | Additive: `spatial` sensor channel emits normalized pointcloud/depth frame into world state, behind `ELO_SPATIAL_SENSOR=1` (off by default), + `spatial_trace.json`. Builds the source INT-3 consumes (not INT-3 itself). 🟢 AUTO (test-gated, additive) — auto-closes on green. `tests/test_wo025_spatial_sensor.py` ≥4 AT · frozen kernel green. `WO-025_Spatial_Sensor_Stub.md` |
| WO-020 | **Debug: kernel routing drift** — CAL over-fires CONNECT/REFLECT/CHALLENGE on casual + direct input; tool mis-route + stale-entity latch; **loop-filter miss** (canned line repeats verbatim) | Builder | **P0** | DONE ✅ David | — | Seam A: server.py post-process override CONNECT/REFLECT/WITNESS→ANSWER on plain imperatives. Seam B: ambiguous-word guard in web search block + entity latch reset in tool_router.py. Routing trace: `blender/routing_trace.json` emitted every turn. 6/6 AT. `tests/test_wo020_routing_drift.py` |
| WO-021 | **Enable + verify Computer Control** (reminders / app control) | Builder | P2 | ⏳ IN_REVIEW — Builder DONE `49e4e66` (2026-08-02) | — | Added `open <app>` to `parse_intent`/`describe`/`execute` in `tools/computer_control_agent.py`. 9/9 AT: `tests/test_wo021_computer_control.py`. **David must**: add `ELO_COMPUTER_CONTROL=1` to `.env` + grant Accessibility permission in System Settings → then live test `"eLo, open Spotify"`. `WO-021_Computer_Control_Enable.md` |
| WO-022 | **Debug: memory RECALL not wired to conversation** — vault stores (753 recs) but "what do you remember" returns the canned stats line / generic fact, not real memories | Builder (Memory) | **P1** | DONE ✅ David | — | Expanded trigger set (18 phrases) + vault recall block restructured: fires regardless of `_cw` state, focused topic query strips fillers, fallback to broad lookup, LLM directed to speak from records not the stats line. 5/5 AT. `tests/test_wo022_memory_recall.py` |
| WO-016 | Wire Whisper/STT into the voice plugin stub | Builder | P3 | **DONE ✅ David (2026-07-31)** | — | `plugins/voice/plugin.py` · `tests/test_wo016_voice_plugin.py` — 5/5 passed · `capture_input()` → `voice.stt.capture()` (already wired) · `deliver_output()` → `tts_output.speak()` with emotion snapshot from context · fallback to print on TTS error · `on_load()` logs active STT+TTS backend names |
| WO-017 | **Debug mode = avatar movement-trigger trace** | Builder + UI/Avatar | P2 | **DONE ✅ David (2026-07-27)** | — | `runtime/spine/presence_faculty.py` + `runtime/spine/plan.py` · `tests/test_wo017_movement_trace.py` — 6/6 passed · `movement_debug` dict on `CognitivePlan` + patched to `blender_state.json["movement_debug"]` every turn · 7 named layers traced (signal_word, distress, grace, stuck, stabilise, emotional_ground, inquiry, light_engine, calm_tone, fallback) · reason string + full driving state snapshot · **Unity lane DONE (`5160815`):** `EloOSAvatarReceiver.LogMovementDebug` reads `movement_debug`, logs intent·trigger·layer·reason to console on each new decision (dedup by ts; toggle `debugMovementTrace`, default on; null-safe) |
| WO-018 | Retire `tool_router.py` (1258-line legacy regex) → capability registry | Builder | P3 | **DONE ✅ David (2026-07-31)** | — | `tools/tool_router.py` — `_ROUTER_TO_CAP_ID` (26 keys) + `all_enabled()` gate in `enrich()` at pipeline · follow-up · normal-intent dispatch; Spotify/YT-Spotify gated; fail-open on registry error · `tests/test_wo018_capability_gate.py` — 6/6 passed |
| **WO-PRIN-1** | **Provenance-tag sweep** across Volume headers (`[SCIENCE]/[ENGINEERING]/[CREATIVE]`) + Canon Index column | Architecture | P2 | **READY** | — | operationalises `01_PRINCIPLES.md §7`; `WO-PRIN-1_Provenance_Tag_Sweep.md`. (5-question gate already live in the Review Gate / completion protocol.) |
| INT-7 | **One Brain visualiser ⇄ `brain_state.json` feed** | UI/Avatar + Builder | P2 | **DONE ✅ auto-verified (test_int7_heat_data.py)** Builder ✅ · UI base ✅ · **refinements REVERTED → OPEN** | — | Builder: `brain_state_writer.py` emits `brain_state/v1` ✅. UI: `EloBrainCluster` base built (`466a4e1` clean). **5 refinements reverted (bad build) — redo ONE change/spec/build/wait.** WO-010 `bccf184` stands. Spec: `ONE_BRAIN_QUANTUM_SPEC.md`; canon `20 §6.5`. v5 future: `state.self_*` + web/trails |
| **INT7-M1** | **One Brain — M1 Neural Respiration** | **UI/Avatar (Design)** | P2 | **DONE ✅ David** | — | breathing approved + committed `b1f6dc4` (off `466a4e1`, +12/−2). Motion language `20 §6.6` |
| **INT7-M2** | **One Brain — M2 Dormant Noise** (v-next change #2) | **UI/Avatar (Design)** | P2 | **DONE ✅ David** | INT7-M1 ✅ | Brownian Perlin micro-jitter on inactive vortex motes (position + brightness twinkle); amplitude below M1; active system overrides; M1+M2 coexist. Committed `7b4b2be` (off `b1f6dc4`, +16/−1). |
| **INT7-M3** | **One Brain — M3 Neural Afterglow** (v-next change #3) | **UI/Avatar (Design)** | P2 | **DONE ✅ David (2026-07-27, `8aacb2a`)** | INT7-M2 ✅ | faculty goes inactive → faint phosphorescent wake fades over 2–5s (ease-out); M2 dormant shimmer resumes underneath; active reactivation absorbs cleanly. Built off `7b4b2be` (+13/−2), one float+flag per node. **Full WO:** `WO-INT7-M3_Afterglow.md` |
| **INT7-LBL** | **One Brain — Label behaviour** (single change) | **UI/Avatar (Design)** | P2 | **DONE ✅ David (2026-07-27, `c11d66b`)** | — | no label text on zoom (floating names removed); `_tip` readout shows on **hover OR click** a state, hides on move-off / empty click, nothing persistent; click-pin isolate unchanged (+7/−32). **Full WO:** `WO-INT7-LBL_Labels.md`; canon `20 §6.5 #1` |
| **INT7-C1** | **One Brain — C1 Data Packet Routing** (v-next change #4, first computational) | **UI/Avatar (Design)** | P2 | **DONE ✅ David (2026-07-27, `df5e552`)** | INT7-M3 ✅ | discrete bright **data beads** (step-quantized: sharp accel → uniform glide → instant arrival, no organic tail) route system→Intent→peripheral by dependency, **riding the web filaments**; pool via `beadsPerLink`; high speed = low distraction. Machine, not organic. **Full WO:** `WO-INT7-C1_Data_Packet_Routing.md`; canon `20 §6.6 (C1)` + `§6.7`. ONE change / build / wait → next M4 |
| **INT7-M4** | **One Brain — M4 Synaptic Cascade** (v-next change #5) | **UI/Avatar (Design)** | P2 | **DONE ✅ David (2026-07-29, `5e834f3`)** | INT7-C1 ✅ | rising-energy active system → activity **propagates hop-to-hop** (Vision→Intent→Attention→Memory→Emotion→Voice), **losing energy each hop** so it fades out; rides the web; **cap propagation depth** (no runaway/loop/flood). Distinct from C1's single bead. **Full WO:** `WO-INT7-M4_Synaptic_Cascade.md`; canon `20 §6.6 (M4)` |
| **INT7-M5** | **One Brain — M5 Memory Echo** (v-next change #6) | **UI/Avatar (Design)** | P2 | **DONE ✅ David (2026-07-31, `8435146`)** | INT7-M4 ✅ | on a **memory retrieval**, **3 diminishing + slowing** concentric ripples from the Memory region — "it came from somewhere"; gentle, low-amplitude (recall, not firing); settles + fades. **Full WO:** `WO-INT7-M5_Memory_Echo.md`; canon `20 §6.6 (M5)` |
| **INT7-M6** | **One Brain — M6 Emotional Diffusion** (v-next change #7 · Homeostasis layer) | **UI/Avatar (Design)** | P2 | **DONE ✅ David (2026-07-31, `03fd03f`)** — David: "spread out & drew in, I like it; tighten a touch subtle at ±12%". Tuning follow-up `INT7-M6-TUNE`. | INT7-M5 ✅ | on a **valence change**, mood **diffuses like dye** across the whole field: **positive = soften + spread outward**, **negative = contract inward**; turbulence couples; global + slow. **MoodPalette only.** **Full WO:** `WO-INT7-M6_Emotional_Diffusion.md`; canon `20 §6.6 (M6)`. ONE change / build / wait → next C3 |
| **INT7-LBL2** | **One Brain — Label readout: ZOOM-GATED** (single change) | **UI/Avatar (Design)** | P2 | **DONE ✅ David (2026-07-31, `1320a56`)** | INT7-LBL ✅ | **small = hover shows glow only, NO text**; **zoomed = hover OR click a state reveals its `_tip` readout**; move-off/empty/zoom-out → hide; nothing persistent. The fix = a **zoom gate** on the `tipNode` condition (show only when `_expand` up). **Full WO:** `WO-INT7-LBL2_Click_Only_Zoomed.md`; canon `20 §6.5 #1` (FINAL, David 07-31, via Designer). Not M4 — label lane. |
| INT7-M6-TUNE | **One Brain — M6 tuning: strengthen the inward tighten** (asymmetric — contraction reads clearer than spread) | UI/Avatar (Design) | P3 | **QUEUED (after HR/WEB)** — bump the negative-valence contraction amp above the ±12% spread; David re-reviews | INT7-M6 ✅ | Designer's offered `diffuseAmp` bump, asymmetric so tighten is unmistakable |
| INT7-QV | **One Brain — quantum-vortex consistency pass** (David relay 2026-08-01) | UI/Avatar (Design) | P2 | **QUEUED → Design (after weave/LL)** — sweep every state's vortex so motion/density/scale read consistently across all systems (no odd-one-out); foundational, do before further mote tuning. Designer proposes → David L3. | INT7-WEB | consistency; MoodPalette only |
| INT7-BEAD | **One Brain — firing bead size** (C1/M4 bead scale — David relay 2026-08-01) | UI/Avatar (Design) | P3 | **QUEUED → Design** — tune the discrete firing-bead size (C1 data-packet + M4 cascade beads) so they read clearly without overpowering; likely a size/scale param + preview. David L3 on look. | INT7-WEB | tuning; couples C1/M4 |
| INT7-VW | **One Brain — voice-wave tighter radius** (David relay 2026-08-01) | UI/Avatar (Design) | P3 | **QUEUED → Design** — tighten the voice-wave emission radius so it reads closer/contained (not spreading too wide). Radius/falloff param + preview → David L3. | — | tuning; voice reaction layer |
| INT7-M5B | **One Brain — M5 echo-ring rework** (David relay 2026-08-01) | UI/Avatar (Design) | P2 | **QUEUED → Design** — rework the M5 memory-echo ripples (current 3 diminishing/slowing rings) toward the look David wants; Designer proposes the revised behaviour → David L3. Supersedes original M5 look. | INT7-M5 ✅ | rework of `8435146` echo |
| INT7-HIT | **One Brain — hit/contact reaction** (new behaviour — David relay 2026-08-01) | UI/Avatar (Design) | P2 | **QUEUED → Design** — on a hit/contact event, the field reacts (localised ripple/impact + brief energy spike at contact point, settling back). New motion behaviour; define trigger source + look; Designer proposes → David L3. MoodPalette only; calm at rest. | — | new interaction layer; couples motion language `20 §6.6` |
| **INT7-HEAT** | **One Brain — live cognitive heat-map / observability layer** (David spec 2026-08-01) | **UI/Avatar (Design) + Builder (data)** | **P2** | **⏳ IN_REVIEW (Builder lane) — `rate`+`confidence` emitted `98915c8` (2026-08-02), 10/10 AT. Design lane still QUEUED (after QV).** Each of 9 vortices glows independently on **3 properties: brightness=activity/load (energy) · colour=emotion (valence) · pulse-speed=urgency (NEW `rate`)**; + **confidence**=opacity/saturation (NEW). Memory-access + thought-flow **reuse M5 / C1·M4** (no new pulse systems). Capstone: a **translucent whole-brain heat field emitted from vortex energy** (hot spots at interactions) that time-decays via a **live Designer slider (~5–60s, default 20s — tune the window while debugging)** → glance = what eLo's been thinking about. **Real observability tool, legibility > spectacle.** Builder emits `systems[x].rate/confidence`; Design renders. `WO-INT7-HEAT_Cognitive_Heatmap.md` | INT7-QV · reuses M5/C1/M4/M6 | data contract in WO; David L3 on look |
| **INT7-HR** | **One Brain — High-res glow sprite + tighter falloff** (David asked; redo of reverted §6.5 #4) | **UI/Avatar (Design)** | **P1** | **DONE ✅ David (2026-08-01)** — signed off direct-with-Builder. True native 512px `Radial()` (per-pixel at target res, **NOT** a 128→256 bilinear upscale — resolves the "stretch = blur" reject). Fixes this cycle: (a) resolution 128→**512px** native; (b) **pixelsPerUnit bug** — bumping texture size without scaling `ppu` made every glow 4× bigger/over-bright (`ppu = 100·S/128` → world size unchanged, **no size change**); (c) **`glowFrac` (David-tuned)** — glow fills only the inner sprite (crisp dot + transparent margin, **NOT stretched to fill**); (d) glow size confirmed **RELATIVE** (localScale = cluster×zoom, shared texture, scales with zoom). First pass `78b5b03` superseded. **✅ COMMITTED `5d4427e`** ("INT7-HR: high-res glow — 512px native, size-preserved, smaller crisp dots, glowFrac 0.5") — working tree clean at this base. Colours/motion/clustering/labels/layout untouched. Canon `20 §6.5 #4`. | — | true HR source, not upscale; colours + motion + layout untouched. **Full WO:** `WO-INT7-HR_HighRes_Sprite.md` |
| **INT7-WEB** | **One Brain — persistent web / spider links BETWEEN MODES** (living-organism web, §6.7 — David asked) | **UI/Avatar (Design)** | **P1** | **▶ DISPATCHED → Design (ACTIVE, 2026-08-01) — "WEAVE THE FIELD" (WEB + WEB2 together).** RING-CLEANUP DONE, clean base. Build the whole field as ONE weave: **state↔state** gossamer mesh **+ the mote-level field (INT7-WEB2) + the core "heart" web-sphere (INT7-CORE, core-coloured nucleus)** — motes ↔ each other + ↔ their state, all in the **Core→States wave-line style**, one look-preview → one David L3. **Target look:** fine **spider-silk gossamer mesh** — dense, translucent, shimmering filaments linking the nodes AND the motes, visible at rest with gentle drift; C1/M4 beads ride them; energy subtly lights the strands. Organic (NOT rigid C2 geodesic). Calm at rest (capped/faded). Off clean HR `5d4427e`. | INT7-RING-CLEANUP | mode↔mode web; **couples with INT7-LL (lightning-liquid rides these strands).** **Full WO:** `WO-INT7-WEB_Spider_Web_Links.md` |
| **INT7-WEB2** | **One Brain — mote-field interconnection** (motes ↔ each other + ↔ their state; David asked 2026-08-01) | **UI/Avatar (Design)** | **P1** | **⏳ IN_REVIEW — David-approved in session ('I like it as it is') → COMMITTED `f76a8dc` off `b987d8d` (2026-08-02).** The fine intra-cluster **"LAN" web**: each mote wires to its **3 nearest neighbours** (connected mesh) + a **spoke to its state hub** (spoke fades bright-at-hub→faint-at-mote, lit by the glow); beads **matched to the Core→State family** (flow-wave + flick + alpha), fine size 0.024, **gently curved** (moteWebCurve 0.12), 28 beads/wire, opacity 0.2, distance-faded + **zoom-invariant**. **Firing:** occasional capped pulses (cap 14) travel a wire slowly → the reached mote **lights up + pops**; bright head decoupled from wire opacity (visible cause). Motes **steady** (removed standalone + M2 dormant twinkles that read as random pulsing). Also **cross-state colour morph** (comet + C1 packet gradient source→dest — David's 'phase change'). **⚠️ WO REWRITE NEEDED** (see grammar note): as-built = **straight-then-curved beads, dense LAN wire, state-lit spokes, firing+morph** — diverges from the original WO (curved-only, few/low-opacity, no firing). → David eyeballs the committed build → DONE. **Full WO:** `WO-INT7-WEB2_Mote_Field_Interconnection.md` |
| **INT7-CORE** | **One Brain — core web-sphere "heart"** (add rotating motes + web links AT the core; core setup unchanged — David asked 2026-08-01) | **UI/Avatar (Design)** | **P1** | **▶ IN THE ACTIVE WEAVE (David 2026-08-01)** — built in the SAME pass as WEB/WEB2 while the mote+web-line renderer is fresh (reuses it), one combined look-preview. Keep the existing core as-is; **add** a compact rotating **mote-sphere + web links at the core** — a "heart", **smaller than the core→state section**, reusing the WEB/WEB2 wave-line + mote renderer. Rotates around core; **BEATS WHEN eLo IS THINKING** (breathes faster on a thinking signal / rising `cluster_energy`, calm at rest — this is where the thinking-breath lives; motes elsewhere stay steady). **Takes the CORE's own colour** (inherits the core hue, not a new one) — highlights the centre as a denser concentration of the core itself. **Tweakable: radius/scale · mote count · link density · spin speed/axis · beat · opacity (Designer exposes sliders → David dials it).** Additive only (no core restyle). Off HR `5d4427e`. | INT7-WEB2 | one visual family; David L3 on look | 
| **INT7-LL** | **One Brain — "lightning-liquid" show between modes** (David asked 2026-08-01) | **UI/Avatar (Design)** | **P1** | **QUEUED → Design (after WEB).** New effect: energy travels the mode↔mode web strands as **branching lightning** but **flows with liquid smoothness** — electric arcs + molten/flowing motion, a "show" on high activity/peak cognition. Rides the INT7-WEB strands. **Designer proposes the exact look (short preview) → David visual-approves** before commit. MoodPalette colour only; must not overpower rest state (show fires on energy, calm at rest). Off HR `5d4427e`. | INT7-WEB | lightning branching + liquid flow; couples WEB. **Full WO:** `WO-INT7-LL_Lightning_Liquid.md` |
| **INT7-RING-CLEANUP** | **One Brain — delete dead sphere-cage ring code** (ShellRing/_rings/ringBeads/DrawRings) | **UI/Avatar (Design)** | P2 | **DONE ✅ auto-verified (Architect L1, 2026-08-01)** — commit `8ba6ea9` off HR `5d4427e`. Deletion-only (−27 lines, 0 insertions): ShellRing · `_rings` · `ringBeads` · `DrawRings` + cage comment removed. Acceptance met — grep → **0 matches**; compiles **0 errors**; **visual BYTE-IDENTICAL** (cage never rendered) → 🟢 AUTO, no David approval needed (nothing changed on screen; diff `git show 8ba6ea9` if you want a glance). Clean base for WEB. **Full WO:** `WO-INT7-RING-CLEANUP_Remove_Dead_Ring_Code.md` | — | cleanup-only, deletion diff |
| INT-8 | **Drag-drop files onto the eLo avatar → eLo reads/reviews** | UI/Avatar + Builder | P2 | READY (partly built) — **PARKED (David: keep One Brain lane as sole Design focus)** | — | **Python side EXISTS:** `desktop/file_drop_handler.py` + `tools/file_reader_agent.py` / `llm_file_agent.py` + capability registry `file_drop`; feeds Perception **Vol XII (Files)** + **Vol XV §2 (Files domain)**. **Missing = the Unity avatar drop-target gesture** (drop onto eLo → hand path to `file_drop_handler`). Cross-lane: UI adds the drop target; Builder confirms ingest→read. |

> **🔍 One Brain — viewer diagnostics (Design + Architect, 2026-08-01, CORRECTED):** (1) **`ShellRing` sphere-cage confirmed DEAD** — never rendered; not what's on David's screen. → cleanup WO `INT7-RING-CLEANUP`. (2) **CORRECTION** (my earlier note was wrong): the **static M6 test snapshot is NOT the cause** of the rings/lines. C1/M4/M5 fire on a **rising energy edge**; a static file holds constant energy and never crosses a threshold, so it **cannot** trigger them. (3) **Root action taken — get to a clean base:** UI agent **reverted the uncommitted WEB build** (it was reading the wrong data) → working tree clean at approved **HR `5d4427e`**; dead ring code to be deleted via `INT7-RING-CLEANUP`; then re-do WEB correctly as a fresh WO. Architect's calm at-rest `brain_state.json` (cluster_energy 0.16, valence 0) still valid for viewing rest — **eLo OS must be OFF or it rewrites the file** (throwaway).

> **🎨 One Brain — BLEND synthesis from David's pinned refs (Design, 2026-08-01) — ARCHITECT PLEASE SLICE:** David (viewing INT7-WEB preview): *"we want a blend of everything, the spec I gave has pictures."* Re-read the 7 pinned frames (`docs/architecture/_refs/one_brain/`). The look = the full §6.7 blend: (a) **orange brain-mass** (vortex motes) at centre; (b) a translucent **web-sphere** around it with **BOTH curved great-circle rings AND straight geodesic chords** (frames .01.59/.02.16/.02.26); (c) **lightning-liquid** = **straight bright streaks whose hot heads pour/flow** along the lines (blue frames .02.46/.03.03.24); (d) the **gossamer connectome** (mode↔mode) laced through; (e) **orange-mass-in-blue-sphere = valence colour language** (MoodPalette-driven, not hardcoded). **→ David's "straight lines" ask = the geodesic-chord + straight-lightning part of the blend — NOT anti-§6.7-organic; it's a *component* of the blend.** This RE-INTRODUCES a web-sphere STRUCTURE (done properly this time, not the removed dead `ShellRing` code). **This is bigger than one WO** — Design requests the Architect slice it into ordered INT7 WOs (e.g. WEB-gossamer ✔ preview · WEB-SPHERE structure+chords · LL streaks · 2D→3D cloud per §6.7 flag). Design is bringing a **first-pass blend look-preview** (straight strands + lightning-liquid pour, uncommitted) for David to react to before any commit.
>
> **🧬 One Brain — VISUAL GRAMMAR (David, 2026-08-01) — governs all slices:** *"mixing liquid cells with electric signals — signals along straight lines, liquid for things that are fluid; wave emotions/speech; look like the images."* → (1) **STRAIGHT lines = ELECTRIC signals** (mode↔mode + mote↔core connectome — sharp, travel straight). (2) **LIQUID/WAVE = the fluid things** — the **motes are liquid cells**, and **EMOTION + SPEECH read as WAVES** (fluid/undulating, NOT straight electric). (3) match the pinned frames. **Approved & committed:** WEB+LL mode↔mode straight electric strands + lightning-liquid pour (`0dc5b20`, David ✅). **Preview live (uncommitted):** INT7-WEB-MOTES = persistent straight electric strands mote↔core↔mote + depth cue ("everything connected · more depth to the cloud"). **Design-requested slices for Architect:** `INT7-WEB-MOTES` (mote-level web + depth) · `INT7-SPIRAL` (re-add the spiral swirl on the line elements) · `INT7-WAVE` (emotion/voice = liquid wave treatment) · web-sphere structure+rings · 2D→3D cloud.
>
> **⏸ Session pause 2026-08-01 (David → sleep):** Committed keeper `0dc5b20` (mode↔mode straight electric strands + lightning-liquid, David ✅). **Uncommitted preview left live** on top for David to eyeball on return: motes ORBIT each state as a coherent shell + strong DEPTH cue (near bright/big, far dim/small — "looking INTO it") + Emotion/Voice liquid WAVES; each modular. `INT7-WEB-MOTES` (22 persistent strands) tried & REVERTED — too busy ("previous was better"); lesson: depth ≠ more strands. **Vision (David):** *"quantum = a lot of particles making up something else — we're looking into it, and adding electric wiring."*
>
> **🖧 One Brain — DATA-FLOW / "system link" (David, 2026-08-02) → ARCHITECT slice as INT7-LL extension:** David: *"imagine I'm a byte travelling from the core → to a state → to a mote → to another mote, creating a system link."* + analogy *"a LAN with different computers connected."* Progress: WEB (mode↔mode straight electric) ✅committed `0dc5b20`; orbit+depth+emotion-wave ✅committed `b987d8d`; **INT7-WEB2 mote-web** (the LAN substrate — motes wired to 2 nearest = mesh + spokes to state hub, opacity matched to motes, wave-along-line + fade) live/uncommitted on `b987d8d`, being tuned with David. **NEW behaviour to slice:** a **byte VISIBLY ROUTES the full path** core→state→mote→mote, lighting each hop = firing/routing layer = extend **C1** (core↔state packet) + **lightning-liquid** DOWN into the mote mesh (rides the WEB2 substrate). **Bug fixed this session:** clicking a state zoomed in and the mote-web faded out (distance-fade span missed `_zoom`) → now zoom-invariant. Open Q for David: pin/click currently isolates (other states dim to focus) — keep or all-lit.

> **One Brain v-next motion queue** (canon `20 §6.6`, ratified from ChatGPT + Gemini intakes) — each
> a separate INT7-* WO, one change at a time, safest-first: **M1 ✅ → M2 ✅ → M3 ✅ → C1 ✅ → M4 (DISPATCHED)** →
> **M1–M6 ✅ · C1 ✅ · HR ✅ · RING-CLEANUP ✅.** **ACTIVE:** INT7-WEB **+ WEB2 (weave the field, together)** → **INT7-LL** (lightning-liquid). **Then the David-relay batch (2026-08-01):** INT7-QV (vortex consistency) → INT7-M5B (echo-ring rework) → INT7-HIT (hit/contact reaction) → INT7-BEAD (firing bead size) → INT7-VW (voice-wave radius) → INT7-M6-TUNE. **Then** resume core motion queue: C3 Clock-Pulse → M7 Phase-Lock → M8 Plasticity → C2 Geodesic → M9 Prediction.
> (LBL label-behaviour ✅ done alongside.) Architect drafts each WO on approval of the prior.

> **Untracked deliberately** (Engineer relay): Unity Presence items (focus-follow, teleport snap,
> parkour gating…) belong in the **Presence tracker**, not this board.
> **Also queued (not yet WOs):** Volume V Ch.1/2/3/6/8/9/10 each need a build WO — Ch.5 (WO-013)
> is the immediate unblock; the rest follow.

### Creative & Marketing work stream (production house)

Runs the `Brief → Strategy → Concept → Production → Post → Publish → Measure` pipeline
(`Output/DISENELO_CREATIVE_PRODUCTION_HOUSE.md`). CR-* = Co-Creative, MK-* = Marketing.
David approves at the **concept** and **publish** gates.

| WO | Title | Agent | Pri | Status | Depends on | Roadmap |
|----|-------|-------|-----|--------|-----------|---------|
| MK-1 | Kickstarter campaign plan (audience · message · channels · KPIs) | Marketing | P1 | DONE ✅ David | — | Kickstarter / Phase 2 |
| CR-1 | Kickstarter hero concept + moodboard (Weavy/Figma) | Co-Creative | P1 | BLOCKED | MK-1 | Kickstarter / 30-day content |
| CR-2 | eLo animated teaser (Higgsfield motion) | Co-Creative | P3 | READY | — | Animated content (long-term) |
| MK-2 | Content calendar + audience growth engine | Marketing | P2 | DONE ✅ David | — | Brand / audience |
| CR-3 | Market-stall visual world + signage system | Co-Creative | P2 | READY | — | Market system / Art |

### Fashion House work stream (Design seat · fashion / footwear / jewellery)

Runs on the shared pattern engine (`Output/DISENELO_FASHION_HOUSE.md §2`): Plushies unwrap
→ plotter cut → sew. David already started fashion/footwear/jewellery.

| WO | Title | Agent | Pri | Status | Depends on | Roadmap |
|----|-------|-------|-----|--------|-----------|---------|
| FH-1 | Pattern→plotter pipeline (Plushies unwrap → cut-file export → test cut) | Design + Builder | P1 | DONE ✅ David | — | Fashion foundation (P1) |
| FH-2 | Lock signature silhouette system | Co-Creative + Design | P1 | READY | — | Fashion foundation (P1) |
| FH-3 | 3–5 fashion prototypes | Design | P1 | BLOCKED | FH-1, FH-2 | Phase 1 |
| FH-4 | First footwear prototype (upper pattern + last/sole 3D) | Design | P2 | BLOCKED | FH-1 | Phase 2 |
| FH-5 | First jewellery drop (sculpt → print → cast) | Design | P2 | READY | — | Phase 2 |
| FH-6 | Tee mockups (fast win) | Design + Marketing | P1 | READY | — | 30-day |
| FH-7 | Mini collection + lookbook | Design + Co-Creative + Marketing | P2 | BLOCKED | FH-3 | Phase 2 |

### Business · Legal · R&D work stream (ChatGPT + Gemini desktop occupants — external → intake)

Onboarding: `Output/DISENELO_AGENT_ONBOARDING.md`. These run externally (paste brief → app produces →
output to `_intake/` → Architect triages). Kickstarter-critical.

| WO | Title | Agent | Pri | Status | Depends on | Roadmap |
|----|-------|-------|-----|--------|-----------|---------|
| MK-1 | Kickstarter campaign plan (audience · message · channels · KPIs) | Marketing (ChatGPT) | P1 | **IN_REVIEW → David** (Codex delivered 2026-07-31; Architect L1 ✅) `Output/DISENELO_MK-1_Kickstarter_Campaign_Plan.md` | — | Kickstarter |
| MK-2 | Content calendar + audience-growth engine (pre-launch → live → fulfilment) | Marketing (ChatGPT) | P1 | **IN_REVIEW → David** (Codex delivered 2026-07-31; Architect L1 ✅) `Output/DISENELO_MK-2_Content_Calendar_and_Audience_Growth_Engine.md` | MK-1 | Kickstarter |
| BO-2 | Kickstarter cost + funding model (COGS + fees + fulfilment → goal + tier margins) | Business Ops (ChatGPT) | **P1** | **IN_REVIEW → David L3 (money)** (Codex delivered 2026-07-31 — structural model complete, honest "DRAFT — INPUTS MISSING": official KS fees + Royal Mail sources, product COGS **intentionally blank**, needs David reward-tiers + supplier quotes) `Output/DISENELO_BO-2_Funding_Model/…xlsx` | — | Kickstarter · money → David L3 |
| LG-1 | Pre-Kickstarter legal + safety checklist (IP · toy/robot compliance · T&Cs · privacy) | Legal (ChatGPT) | **P1** | **IN_REVIEW → David L3 (legal)** (Codex delivered 2026-07-31; not legal advice — David/counsel review) `Output/DISENELO_LG-1_Pre-Kickstarter_Legal_Safety_Checklist.md` | — | Kickstarter · safety → David L3 |
| RD-1 | Disney animatronics + NVIDIA robot-learning research → eLo Robot Phase 1 approach | R&D (Gemini) | P1 | **DONE ✅ David (2026-07-31)** — recommendation adopted: hybrid Bowden head/neck + chest-inflation breathing + TPU shell; scripted P1 / learned P2. `_intake/RD-1_DISNEY_NVIDIA_RESEARCH.md` | — | Robot · tracker 🟢 |
| RD-2 | NVIDIA Isaac Lab sim setup — PhysX-5 FEM deformable + domain randomisation + synthetic gaze (Phase 2 prep) | R&D (Gemini) | P2 | DONE ✅ David | RD-1 ✅ | Robot Phase 2 · sim direction |
| RD-CAD | eLo Robot head/neck **safety-aware CAD contract** (2-DOF Bowden, base servos, cable geometry) | Design + Builder (hardware) | P2 | **READY → route (safety-aware, Codex 2026-07-31)** | RD-1 ✅ · couples LG-2 | **Deliverables BEFORE any prototype test:** motion envelope · hazard overlay · physical-stop paths · base-stability layout · power-off behaviour · limiter/stop/test interfaces. Brief: `Output/DISENELO_RD-CAD_Head_Neck_Safety_Constraint_Brief.md` (Codex delivered 2026-07-31, synced to Output). **No prototype test without David L3 + human safety review (LG-2).** |
| LG-2 | **Product-Safety scope — force limiters / soft-stop** (current-sensing/clutch) for human interaction | Legal · Product Safety (ChatGPT + human) | **P1** | **IN_REVIEW → David L3 + human review** (Codex delivered 2026-07-31; safety scope — human review required before any build) `Output/DISENELO_LG-2_Robot_Force_Limiter_Soft_Stop_Safety_Scope.md` | RD-1 ✅ | Robot safety · **David L3 + human review before any build** |

### Game work stream — eLo's Planet (Game Designer/Builder · Unity)

**Repo:** `/Users/Disenelo/eLo-Planet` · git `github.com/disenelo/eLo-Planet` (main) · Unity `6000.3.6f1`
URP · New Input System · **CharacterController-only (no Rigidbody)**. Spec pinned
`docs/architecture/_refs/game/…v4.md`; detailed tracker `~/Documents/DISENELO/memory/projects/eLo-Planet_Tracker.md`.
**Reality (Game-agent relay, 2026-07-27) is AHEAD of spec §19.1:** the anim system is being *aligned*,
not un-started — **GM-2 is already underway.** Separate Unity project (not eLo OS / not DesktopBuddy).
**Model roles (David, 2026-07-27):** `eLo_v2` = the NEW import and the **live working target** — all
changes are being transitioned onto it, incl. the gun-fire arm/pose (a **copy of the Presence model has
already been made into the game project**, so no cross-project Change Control dependency remains). `eLo`
(old) = the **authoritative BACKUP**; it must be brought into full alignment *before* it can be retired.
So this is a **transition + align-then-retire** task, **not** a "pick which is authoritative" decision.

| WO | Title | Agent | Pri | Status | Depends on | Spec |
|----|-------|-------|-----|--------|-----------|------|
| GM-0 | **Transition eLo → eLo_v2 + align backup** — migrate all changes onto `eLo_v2` (live target); gun-fire arm/pose uses the **local copy** of the Presence model (already in-project); bring the `eLo` backup into alignment; **retire old eLo only once fully aligned**. Interim: both are `PlayerAnimator`-enabled + share head-bone fileIDs — keep them from conflicting in-scene until retirement. | Game (Unity) | **P0** | DONE ✅ David | — | gates GM-2 completion |
| GM-1 | Core Loop skeleton prototype (placeholder + camera rig + depth-plane shift) | Game (Unity) | P1 | ~superseded | — | base movement already in; folded into GM-2 reality |
| GM-2 | **eLo_v2 rig + arms/animations** — the transition's core; broken into the ordered slices below (David 2026-07-27: **arms + animations are top priority**) | Game (Unity) | **P0** | **IN_PROGRESS** | GM-0 | spec §19.2 Step 2 |
| GM-2a | **Swim-lean + head in eLo_v2** — carry the swim-lean animation across; the **head is not currently included in the new eLo_v2** → include/fix it | Game (Unity) | **P0** | **NEXT** | GM-0 | order #1 |
| GM-2b | **Run → gun-fire blend** — blend the **hands + run animations into the gun-fire state** (Run↔GunFire 1D blend), so firing while running reads correctly | Game (Unity) | **P0** | QUEUED | GM-2a | order #2 |
| GM-2c | **Arm + gun positioning** — place/align the arms and weapons (sockets, hold pose) on eLo_v2 | Game (Unity) | **P0** | QUEUED | GM-2b | order #3 |
| GM-2d | **Backpack** — model/attach a backpack accessory on eLo_v2 | Game (Unity) | P1 | QUEUED | GM-2c | order #4 |
| GM-A8 | Duplication sweep — verify Vehicles/Weapons/Pickups/Cameras reference `eLo_v2` not old eLo | Game (Unity) | P1 | READY (after GM-0) | GM-0 | ground-truth verify |
| GM-3 | **First playable invasion stage** — *assemble* from existing parts (6-weapon system ✅ · collectibles/crates ✅ · enemy roster ✅ · score ✅), not from scratch | Game (Unity) | P1 | BLOCKED | GM-2 | spec §20 Core Loop — ingredients live per tracker |
| GM-4 | FPS-style aim — arms follow cursor during 2.5D traversal (IK vs procedural fork) | Game (Unity) | P2 | BLOCKED | GM-2 | after model/anim swap |
| GM-punch | **⚠️ polish/test punch-list** (banana-grenade test · water VFX/buoyancy tune · crosshair PNG wire · Sub rotation + seated entry/exit · avatar-mask arm-layer Play test · PatrolEnemy MGS alert rotation · Tank AimAtPlayer LookPlane→XY · Blob `BlobCluster.compute` assign · day-night events · movement-speed tune) | Game (Unity) | P2 | QUEUED (after GM-0) | GM-0 | tracker §7 — each a one-slice WO when scheduled |

> Roadmap (§20 — **reconciled**): skeleton + Core-Loop *systems* = **built** (see tracker inventory) →
> current phase = **model transition (GM-0) + polish (GM-punch)** → then Companion AI → Prologue Arc →
> full Invasion Stages → Upgrade → Co-op → Polish → Racing → Launch. Under Change Control (D-M): one
> slice, to spec, build, David reviews.
> **Immediate (David 2026-07-27 — arms + animations are top priority):** GM-0 fileID/transition prep,
> then the ordered arm/anim slices **GM-2a swim-lean + head → GM-2b run→gun-fire blend → GM-2c arm+gun
> positioning → GM-2d backpack**. GM-A8 sweep + GM-punch list hold until these clear (no scope-creep).

### Company Runtime work stream — Presence ↔ eLo (EA-3 · Evolution Phase II)

Additive `company_runtime/` package (NOT eLo cognitive core — LAW-017, freeze-safe). Lets David talk to
eLo on Presence to **show · move · organise · approve** the company. Dashboard = observer that *requests*
through the Executive (EA-3 Amendment 7). Canon: `DISENELO_UNIVERSAL_RUNTIME_EA3.md`,
`DISENELO_PRESENCE_ELO_INTEGRATION.md`. David-approved 2026-07-29 (Option B → converge to A, validate).

| WO | Title | Agent | Pri | Status | Depends on | Spec |
|----|-------|-------|-----|--------|-----------|------|
| **EA2-1** | Company State writer + action intake + `company.approve` stub | Builder (Python) | **P1** | **DONE ✅ David (2026-07-31)** | — | `company_runtime/company_state_writer.py` (Builder) + `company_graph.py` (Architect — mood-aligned connectome, schema reconciled) · parses live board → **66 WOs** → `blender/company_state.json` · L3 + safety gate enforced · `tests/test_ea2_1_company_state.py` **6/5 passed**, **frozen kernel green** (wo001 5/5·wo014 5/5·wo006 10/10) · dashboard renders live |
| **EA2-2** | Presence Company Brain panel + request channel + `company.*` intents | Designer UI Agent (Unity) + Builder (data) | **P1** | DONE ✅ David | EA2-1 ✅ | **DIRECTION (David 07-31): the brain REUSES `EloBrainCluster` (One Brain Visualiser engine) in a company-data mode — feed `company_state.graph`, NOT a new renderer. No orange founder core.** HUD panels (briefing/board/approvals) per `Output/DISENELO_COMPANY_BRAIN_UI_SPEC.md`. Approve = request via Executive (EA-3 §7). **UPDATE 08-01: live data now feeds it — `agents[]` heartbeat (agent_bus) drives node energy/valence, `wo_tests`+importance badges, `coordination` beads. Figma-first (frames → David review → Unity on EloBrainCluster). Interim HTML dashboard mirrors the same data 1:1 as build reference.** `WO-EA2-2_Presence_Panel_And_Requests.md` |
| **EA2-2B** | **Company Brain — author the Figma frames (One Brain look) → David review → Unity assemble** | UI/Avatar (Design) | **P1** | **READY → Design 🟠 (queues after INT7-WEB, 2026-08-01)** | EA2-2 data ✅ | Reuse `EloBrainCluster` in **company-data mode** (divisions=vortex systems · seats=motes · `agents[]` heartbeat → energy/valence · graph+web links · LL on activity). **No founder core.** Figma `UdpnVgHT7qWOiyzk0MIgLU` (MoodPalette vars there) → **David L3 on the look** → assemble in Unity. Data already emitted in `company_state/v1`. `WO-EA2-2B_Company_Brain_Figma_Frames.md` |
| EA2-4 | Scheduling Faculty (move/reorder WOs) | Builder | P2 | QUEUED | EA2-1 | EA-3 §9 |
| EA2-5 | **Approval Faculty** (L3 gate as a faculty — net-new) | Builder | P2 | QUEUED | EA2-1 | EA-3 §4 |
| EA2-6 | Orchestration Faculty (multi-seat chains — net-new) | Builder | P3 | QUEUED | EA2-5 | EA-3 §4 |
| EA2-7 | Company Memory store (via unified Memory) | Builder | P3 | QUEUED | EA2-1 | EA-3 §6 |

> **Validation gate (David "but validate"):** no slice advances until its acceptance tests pass **and**
> the frozen cognitive-kernel tests stay green (additive-only proof). EA2-1 → EA2-2 is the first
> "talk to eLo → it shows + approves" round-trip (Phase II).

---

## 2. What is "pending implementation" (spec exists, code does not)

Grouped for the CEO Agent. All of these have canon; none is built.

**Foundational (unblocks the rest)**
- Faculty Bus / envelope (WO-001) — Audit #1. *D-A ratified — READY to build.*
- Contract wiring into the live spine (WO-004) — only `CognitivePlan` runs today; the
  other three contracts are aspirational (`16_spine_runtime.md`).

**Memory (HIGH-severity per WP_D)**
- `integrate_session()` replacing `compress_session()` (WO-005) — `17_memory_update.md`.
- Working Memory as a typed object (WO-008) — Audit #3, *needs Volume VI first*.

**Cognition faculties (Volume V)**
- Emotional Processing (WO-006), Personality Evolution unified (WO-007).

**World & perception**
- `LiveWorldState` (WO-002) — Audit #2, spec done (`Volume_XV`).
- Perception Faculty (WO-009) — Audit #5, *needs Volume XII first*.

**Cross-agent hygiene**
- Alias/mood table sync (WO-010) — silent-drift risk between Python and Unity.

---

## 3. Recommended sequence

**CEO-approved implementation sequence (DECISION_LOG, 2026-07-27):**
```
Phase 1 (immediate):
  WO-005  integrate_session() replaces compress_session()        Builder · P0
  WO-003  finalise Volume V legacy contracts (ratified lifecycle) Architecture · P1
  WO-001  Faculty Bus — canonical 9-field envelope                Builder · P0
Phase 2:
  WO-004  CognitiveState/EmbodimentState/ExecutionReport → Spine  Builder
  WO-002  unified LiveWorldState                                  Builder
  WO-011  memory consolidation + forgetting curve                 Builder
Phase 3:
  WO-010  Python↔Unity alias/mood table sync                      UI/Avatar + Builder
  WO-009  complete Perception Faculty                             Builder
Phase 4:
  WO-012  Dream phases + DeepDream (against Volume IX)            Builder
```
Rule (Executive Directive): implement against the **Canon**, not conversational prompts.

---

## 4. Status roll-up

```
DONE (David-approved):  5  (WO-002, WO-008, WO-009, WO-011, WO-012)  — Policy A
DONE (Builder-claimed, awaiting David):
                        14 (WO-001, WO-004a, WO-004b, WO-005, WO-010, WO-006, WO-007, INT-2, WO-013, WO-014, WO-016, WO-017, WO-018, EA2-1)
                           WO-001: tests/test_wo001_faculty_bus.py 5/5
                           WO-004a/b: tests/test_wo004_contracts.py 12/12
                           WO-005: tests/test_wo005_integrate_session.py 5/5
                           WO-010: state_writer dup removed · blender/shared_tables.json copied
                           WO-006: tests/test_wo006_emotional_processing.py 10/10
                           WO-007: tests/test_wo007_personality_evolution.py 13/11
                           INT-2: tests/test_int2_robot_vision_bridge.py 5/5
                           WO-013: tests/test_wo013_significance_engine.py 7/7
                           WO-014: tests/test_wo014_spine_wiring.py 5/5
                           WO-016: tests/test_wo016_voice_plugin.py 5/5
                           WO-017: tests/test_wo017_movement_trace.py 6/6 (Python lane; Unity lane OPEN)
                           WO-018: tests/test_wo018_capability_gate.py 6/6
                           EA2-1: tests/test_ea2_1_company_state.py 6/6 · company_runtime/ additive · frozen kernel 20/20
READY (Builder lane):   WO-003 (Architecture)
BLOCKED:                WO-015 (D-K), INT-3 + Creative/Fashion streams (other lanes)
```

_Updated 2026-07-27 — WO-013 (7/7) + WO-014 (5/5) + WO-017 Python lane (6/6) completed.
Builder-lane READY: WO-016, WO-018. 11 WOs awaiting David approval. Still open: INT-6b citation · WO-015 (D-K) · WO-017 Unity lane._

_Updated 2026-07-31 — WO-018 (6/6) + EA2-1 (6/6) completed. Builder-lane READY: WO-003 (Architecture). 14 WOs awaiting David approval. EA2-2 unblocked (Unity lane)._

Spec-complete canon feeding these: Volume V (10 ch + CONTRACTS), Volume XV (2 ch),
`16_spine_runtime.md`, `17_memory_update.md`. See `docs/architecture/00_CANON_INDEX.md`.

---

## 5. Completion log

### WO-010 — Sync Python↔Unity alias/mood tables — UI/Avatar side complete (2026-07-27)

Filed by **UI/Avatar (Unity)** against `CO_WORKING_GUIDE.md §4`. Status → **IN_REVIEW**.

Reconciled Unity's tables against the Python canon (`animation_driver._CANONICAL`,
`embodiment_publisher._UNITY_MOOD`, `spotify_agent` music moods, `brain_state_writer` labels):

- **Animation clips — already in sync.** `EloOSAvatarReceiver.ResolveClip` lowercases, strips
  the `eLo_` prefix the spine sends, then maps via a table that is a **superset** of `_CANONICAL`
  (5 canonical clips + 15 aliases all resolve). No change needed.
- **Mood-collapse targets — already in sync.** Every `_UNITY_MOOD` output
  (`curious·alert·calm·neutral·excited`) was already in `MoodPalette`.
- **Mood vocabulary — was the silent-drift, now fixed.** 19 words the spine can emit had no
  palette entry and fell back to neutral: `warm · celebrating · open · recalling · dreaming ·
  quick · rapid · present · steady · settled · grounded · still · quiet · silent · resting ·
  sleeping · slow · lost · heavy`. Added to `Assets/Scripts/MoodPalette.cs`, each placed by
  valence on the existing Hawkins/Abraham-Hicks scale. Reconciliation now: **music_mood ALL
  RESOLVE · brain_state labels ALL RESOLVE** (the lone apparent miss, `active`, is the boolean
  JSON key, never a `label` value). Palette recognises 108 tokens.

**Scope note:** the sync is one-directional — the spine emits the vocabulary, Presence must
recognise all of it (now does). No reciprocal Python change was required, so **nothing was
edited on the eLo OS side** (read-only there, per role). Presence writes only its own event keys
(`elo_spatial.json` edge/on_window), which are not moods/aliases.

**Ships:** next Presence build batch (Unity-only code change; takes effect on rebuild).

*Filed by UI/Avatar (Unity) — awaiting Builder/CEO review to mark DONE.*

#### UI/Avatar response to Architect review — CONTESTED (2026-07-27)

Architect looped WO-010 back: *"make Unity read `shared_tables.json` (it still hard-codes its
own vocabulary); hand back the diff proving parity."* Responding on both points.

**1. Parity IS met today (evidence).** Reconciliation of Unity's tables against the Python canon,
run 2026-07-27:
- **Animation clips:** `EloOSAvatarReceiver.ResolveClip` strips the `eLo_` prefix then maps via a
  **superset** of `shared_tables.json:animation_aliases` — all 15 aliases + 5 `known_clips`
  resolve. Exact parity.
- **Moods:** every word the spine can emit resolves in `MoodPalette` — `music_mood` **ALL
  RESOLVE**, `brain_state` labels **ALL RESOLVE** (108 tokens). Zero silent neutral-drops.
  The lone apparent miss, `active`, is the boolean JSON key, never a `label` value.
  → The drift the WO guards against is **not present today**. The Architect's concern is
  *future* durability, not a current parity gap.

**2. The `shared_tables.json` mood design regresses David's One Brain (David's ruling).**
`mood_aliases` collapses the vocabulary to **8 canonical moods** (`resting→neutral`,
`playful→excited`, `reflection→calm`, `thinking→alert`…). That collapse is **correct for the
coarse embodiment / belly-glow mood** (the light-engine's 20→8), but **wrong for the One Brain
visualiser**, whose per-system `label`s must render on the **full continuous MoodPalette**
(Hawkins/Abraham-Hicks scale) — an explicit, repeated David requirement (*"this should all be
from the colours of the mood plate"*). Consuming the 8-mood collapse for the One Brain would
flatten a colour range built deliberately this session. **David's decision: keep the rich
palette.**

**3. Constructive resolution (requesting the Architect bless this).** Unity WILL adopt
`shared_tables.json` as the durable single source — *without* collapsing:
- **Clips:** load `animation_aliases` + `known_clips` from the JSON at runtime (retire the
  hard-coded `Canonical` table). Pure win, no downside.
- **Moods:** use the JSON as a **fallback layer beneath** the rich palette — try the raw word in
  the full `MoodPalette` first (rich One Brain colour); only if unknown, apply
  `mood_aliases → canonical → palette`. This gives the Architect the runtime single-source +
  guaranteed no-drift they want, **and** preserves David's colour.
- One wiring note: `shared_tables.json` lives in `blender_bridge/`; Presence reads state from
  `blender/`. Builder to also emit/copy it into `blender/` (or confirm a read path) so Presence
  can consume it.

**Status:** leaving the row at `LOOP BACK` pending the Architect's ruling on #3. If blessed, the
fallback-layer wiring is a small Unity change; the rich palette stays. No Unity change is being
made until then (David: keep the hand-sync as-is meanwhile — it is parity-correct today).

*Filed by UI/Avatar (Unity) — response to Architect review, per David's decision.*

#### Architect ruling — WO-010 (2026-07-27) — UI/Avatar UPHELD ✅

The UI/Avatar analysis is correct; I withdraw the "parity unmet" framing and rule in its
favour, with one canon clarification everyone now follows:

- **Two mood consumers, two granularities (now canon):** (1) the coarse **belly-glow /
  embodiment mood** correctly uses the 8-mood collapse (`mood_aliases`); (2) the **One Brain
  visualiser** MUST render the **full continuous MoodPalette** (David's explicit requirement)
  and must NOT consume the 8-mood collapse. These are different consumers — the collapse is
  right for one, wrong for the other.
- **Approved design (do this):** Unity adopts `shared_tables.json` as the durable single
  source — load `animation_aliases` + `known_clips` from it (retire the hard-coded
  `Canonical` table); for moods, try the raw word in the full `MoodPalette` first, fall back
  to `mood_aliases → canonical → palette` only if unknown. Runtime single-source + no-drift
  **and** the rich palette preserved. Better than either original position.
- **Builder action (elo-ai scope ✓):** emit/copy `shared_tables.json` into `blender/` (Presence
  reads from `blender/`) or confirm a read path.
- **Parity today: accepted** — the hand-reconciled superset is verified; no silent drift present.

Status → **IN_PROGRESS** (Unity wiring the fallback layer; not a blocker). I'll fold the
two-consumer distinction into the embodiment canon.
*Ruling by Architect (Claude).*

#### UI/Avatar — approved design implemented + parity diff (2026-07-27)

Built to the ruling. Presence commit `bccf184` ("WO-010: Unity consumes shared_tables.json").

**What changed (Unity):**
- **`SharedTables.cs`** (new) — loads `~/elo-ai/blender/shared_tables.json` once at runtime
  (Newtonsoft) and exposes `mood_aliases` / `animation_aliases` / `known_clips`. Missing/unreadable
  file is safe: tables stay empty and every caller keeps its built-in fallback (parity holds offline).
- **`EloOSAvatarReceiver`** — the `Canonical` alias table is now **built at runtime from the shared
  `animation_aliases`** (alias → `eLo_<Clip>`) via a Unity-local `_clipToState` map (the Animator
  state names only Unity knows). Hard-coded alias list retired; a built-in mirror is used only if the
  JSON is absent; presence-mode words (`explore/observe/…`) kept as local defensive coverage.
- **`MoodPalette.Resolve()`** — rich-first resolver for the **coarse consumers** (belly glow, chat
  glow, capability dot): full 108-word palette first, collapse via `mood_aliases` → 8 canonical only
  on an unknown word. Added `distress` so all 8 canonical targets resolve.
- **One Brain (`EloBrainCluster`) untouched** — still calls `TryColor` directly (full continuous
  palette, no collapse), per the two-consumer canon.

**Parity diff (simulated the new resolvers against `blender/shared_tables.json`):**
- **Clips:** 33 inputs (15 `animation_aliases` + 5 prefixed `eLo_*` clips + 13 local extras) →
  **all resolve to a real Animator state** (`Idle/Walk/Run/Calm/eLo_LongJ`). No `Idle` fallbacks.
- **Moods:** 63 inputs (music moods + `brain_state` labels + all `mood_aliases` keys + the 8
  canonical) → **all resolve to a palette colour**. Zero silent neutral-drops.
- **8 canonical targets** (`neutral·calm·curious·alert·excited·joy·sad·distress`) all present in palette.

Build clean (0 compile errors), signed, relaunched. **UI/Avatar side complete — ready for Architect
verification + David's `COMPLETION_LOG` approval.**
*Filed by UI/Avatar (Unity).*

---

### WO-009 — Perception Faculty — DONE ✅ (2026-07-27)

Filed by **Builder** against `Volume_XII/01_Perception_Faculty.md`. Status → **DONE**.

`faculties/perception/perception_faculty.py` — Architecture Audit gap #5 resolved.

**Deliverables:**
- `PerceptionResult` frozen dataclass: `modality_reads · scene · active_surface · salient_objects · user_activity · confidence · source_health`
- `perceive()` — core entry point; 4 independently degradable modalities (vision, window, voice, files)
- `perceive_from_live_state()` — convenience wrapper for spine/CognitiveState assembly; reads `desktop.window_state` + vision cache from blender_state.json
- Anti-fabrication: `vision_permitted=False` → `source_health.vision=absent`, no salient objects extracted regardless of text supplied
- App→surface mapping table (30+ entries), surface→activity inference

**Acceptance tests — 7/7 passed:**
- FT-1: coding session → scene, surface=code, activity=working, salient_objects populated
- FT-2: PerceptionResult is frozen (immutable dataclass)
- FT-3: source_health complete; creative surface; vision=absent when not supplied
- ST-1: vision absent → window+surface+activity still resolve; confidence lowered (0.95)
- ST-2: screen-record denied → vision=absent, no fabricated objects
- ST-3: no sensors → surface/activity=unknown, confidence=0.70, no fabrication
- IT-1: all 4 modalities live → complete modality_reads, confidence=1.0

**Key rule upheld:** Perception interprets; never decides (One Brain principle).
**INT-2 unblocked** — `capture → PerceptionResult` bridge can now begin.

---

### WO-012 — Dream phases + DeepDream image pipeline — DONE ✅ (2026-07-27)

Filed by **Builder** against `Volume_IX/02_Symbol_Engine_and_DeepDream.md`. Status → **DONE**.

Additive changes to `faculties/dream/dream_faculty.py` (existing cycle preserved):

**New functions added:**
- `_run_nrem_phase(symbols, recent_topics)` — CONSOLIDATION: identifies strong symbols (weight ≥ 1.2), prunes noise (weight < 1.0), extracts memory_refs. Records `phase: "NREM"`.
- `_generate_dream_image(symbols)` — DeepDream pipeline: derives visual metaphor from top 3 symbols → calls `tools.image_gen_agent.generate()`. Best-effort, non-blocking. No symbols → None. Returns path or None. `hud_image` written via `state_writer.patch` inside image_gen_agent.
- `_extract_personality_proposal(insight)` — scans insight text for trait-affecting language → returns `{trait, direction, source, validated: False}` PROPOSAL for Ch.7. Never self-applied.

**`run_dream()` extended:**
- New kwarg: `idle_seconds: float = 1800.0` (backward-compatible)
- Phase gating: `idle_seconds < 1800` → NREM only; `≥ 1800` → NREM + REM narrative + image
- Journal entry enriched per Canon §1.4: `dream_id`, `theme`, `phase`, `symbols` (with weight), `narrative`, `insight`, `memory_refs`, `personality_delta_proposed`, `image_ref`, `mood`, `curiosity`, `session_read`, `focal_thread`

**New constants:** `NREM_MIN_IDLE = 600`, `REM_MIN_IDLE = 1800`

**Acceptance tests — 11/9 passed (both chapters covered):**
- Ch1-FT-1: trigger discipline (fires at idle≥600; cooldown blocks repeat)
- Ch1-FT-2: association graph → 5 symbols; weights populated
- Ch1-FT-3: journal appended with all Canon fields (dream_id, phase, memory_refs, personality_delta_proposed, image_ref)
- Ch1-ST-3: rate-limited — DREAM_COOLDOWN blocks second cycle
- Ch1-ST-2: personality proposal extracted, validated=False — routes to Ch.7, never self-applied
- Ch2-FT-1: weight by source count — 4 "garden" topics → Garden weight=3.0, leads graph
- Ch2-FT-2: phase order — short idle=NREM, long idle=NREM+REM
- Ch2-FT-3: image pipeline completes without crash; None=text-only fallback (no API key in test env — correct)
- Ch2-ST-1: text-only fallback — narrative+insight+symbols journaled when image_gen fails
- Ch2-ST-2: no symbols → no image (returns None immediately)
- Ch2-ST-3: personality proposal (patience) created, validated=False

**Architecture rules upheld:** dreaming never preempts a turn (offline only); personality changes are proposals, never self-applied; image pipeline is best-effort and never blocks journaling.

---

### Builder action items — completed 2026-07-27

**WO-001 — Test file committed**
`tests/test_wo001_faculty_bus.py` — 5/5 passed. Tests use `make_envelope()` (proper payload.type), expired ISO timestamp for drop test, singleton check via `get_bus()`. Evidence attached.

**WO-004a — Call-site confirmed + test**
`tools/truth_sync.py` is the call-site for `build_execution_report()` (session-close path, not per-turn).
Per-turn wiring would be an S7 migration step — noted for Architect.
`tests/test_wo004_contracts.py` — 3/3 passed for WO-004a section.

**WO-004b — CognitiveState + EmbodimentState built**
`assemble_cognitive_state()` + `build_embodiment_state()` added to `runtime/spine/spine.py` (additive).
- `assemble_cognitive_state()`: packages language/attention/relationship/capability/env faculty dicts → frozen `CognitiveState`. Missing faculty → neutral default + confidence lowered. Never crashes.
- `build_embodiment_state()`: maps `CognitivePlan.presence_plan` + `emotional_vector` → frozen `EmbodimentState`. Glow, robot LED, Unity mode, voice pacing, publish metadata all derived from plan.
- `tests/test_wo004_contracts.py` — 12/12 passed (AC-1 one decision, AC-2 frozen, missing-faculty graceful, all surface fields populated).
- **Note for Architect:** These are standalone functions. Per-turn wiring into `run()` is the S3/S6 migration step (requires behaviour-parity batch verification). Recommend as a follow-on after David approval.

**WO-005 — Test file committed**
`tests/test_wo005_integrate_session.py` — 5/5 passed. Tests: significant session produces spot, below-threshold skipped, result dict keys, lesson formed, bad input handled without crash.

**WO-010 — Builder tasks done**
- Duplicate `_MOOD_ALIASES` removed from `blender_bridge/state_writer.py` → imports from `shared_tables`.
- Bug fixed: `"alert" → "curiosity"` in old local dict was wrong; shared_tables correctly maps `"alert" → "alert"`.
- Missing entries added to `shared_tables.MOOD_ALIASES`: `"open"→"neutral"`, `"warm"→"calm"`, `"quiet"→"calm"`, `"lit"→"joy"`.
- `blender/shared_tables.json` copied from `blender_bridge/shared_tables.json` for Unity Agent.

**Test suite total: 57/57 passed across 9 test files (2026-07-27)**
_(added: test_wo016_voice_plugin.py — 5/5; test_wo017_movement_trace.py — 6/6; test_wo018_capability_gate.py — 6/6)_

---

### EA2-1 — Company State writer + action intake — DONE ✅ (Builder, 2026-07-31)

**New additive package: `company_runtime/`** — mirrors `blender_bridge/brain_state_writer.py` pattern.

**Deliverables:**
- `company_runtime/company_state_writer.py` — reads `DISPATCH_BOARD.md`, emits `blender/company_state.json` (`company_state/v1` schema). Callable as `publish()` per cycle or one-shot CLI.
- Action intake: watches `blender/company_actions.json` (reverse-channel, same pattern as `unity_events.json`). Validates, dispatches, wraps as Faculty Bus Envelope (runtime:"company" in payload body — envelope stays universal per EA-3 §5), clears file.
- `company.approve` stub: L3 gate (`david/disenelo/founder`), safety/money/legal gate (keyword match on WO row; human_flag required), `_flip_wo_status()` (targeted line replacement in board markdown), re-emits state.
- `company_runtime/__init__.py` — empty package init.

**FREEZE_V1_LOCK compliant:** zero edits to `core/`, `runtime/spine/`, `prompts/`, or any frozen kernel file.

**Acceptance tests — 6/6 passed (`tests/test_ea2_1_company_state.py`):**
- AT-1: `publish()` emits valid `company_state/v1`, 66 rows, 11 required keys, `seats_sample ≥ 4`
- AT-2: `approval_request` with L3 actor (`david`) flips WO status in board + re-emits state
- AT-3: money WO without `human_flag=True` → refused; with `human_flag=True` → passes
- AT-3b: same WO passes with `human_flag=True`
- AT-4: malformed / non-L3 requests all refused gracefully, no crash
- AT-5: frozen kernel tests still green — `test_wo001_faculty_bus.py` 5/5 · `test_wo014_spine_wiring.py` 5/5 · `test_wo006_emotional_processing.py` 10/10

**Unblocks:** EA2-2 (Presence company panel, Unity side), EA2-4 (Scheduling Faculty), EA2-5 (Approval Faculty).

**Test suite total: 63/63 passed across 10 test files (2026-07-31)**
_(added: test_ea2_1_company_state.py — 6/6; frozen kernel 20/20)_

---

### WO-020 — Kernel routing drift — DONE ✅ (Builder, 2026-07-31)

**Root cause (two seams):**
- **Seam A:** `_conversation_action()` in `runtime/executive.py` (FROZEN) falls through to default `connect` on plain imperatives ("open Joe Budden Podcast"). Executive can't be touched — fix is a post-process wrap in `server.py`.
- **Seam B:** `tools/web_search.py` `is_search_intent` matches "what is done?" and extracts query "done" → DuckDuckGo/Wikipedia search for "DONE" algorithm. That result latches in conversation history; next turn eLo confabulates "Opening DONE" on "open Joe Budden Podcast" (Seam A drift keeps action=connect → LLM associates stale "DONE" entity). Secondary: `tool_router.py` `_last_agent` latch not cleared between turns on new explicit requests.

**Deliverables (`FREEZE_V1_LOCK` compliant — no edits to `executive.py` or `prompts/`):**
- `server.py` — `_original_raw = raw` capture at top of `_process_turn()`.
- `server.py` — Seam B web search guard: `_WS_AMBIGUOUS` frozenset; extracted query in set → skip search (prevents "done/ok/ready/…" being web-searched).
- `server.py` — Seam A override block: after stabilisation override; if action in `{connect,reflect,witness}` AND input is a plain imperative (starts with open/play/find/…, no "?") → override to `answer`.
- `server.py` — Per-turn routing trace: `{user_input, intent, valence, conversation_action, cal_reason, tool_agent, backend_used, _ts}` → `blender/routing_trace.json` (atomic write) after each turn. Observable without guessing.
- `tools/tool_router.py` — entity latch reset: `_last_agent = None`, `_last_arg = None` when follow-up detection returns None (new explicit request → stale entity cleared before new intent detection).

**Acceptance tests — 6/6 passed (`tests/test_wo020_routing_drift.py`):**
- AT-1: "what is done?" → extracted query "done" confirmed in `_WS_AMBIGUOUS` guard set
- AT-1b: "what is the Joe Budden Podcast?" → not ambiguous → search would proceed
- AT-2: Seam A override correct for all 6 cases (imperatives → override; questions → no override; already-answer → no override)
- AT-3: entity latch cleared on new turn — `_last_agent` resets to None after non-follow-up input
- AT-4: routing trace schema validated
- AT-5: frozen kernel 20/20 — `test_wo001_faculty_bus.py` 5/5 · `test_wo014_spine_wiring.py` 5/5 · `test_wo006_emotional_processing.py` 10/10

**Test suite total: 69/69 passed across 11 test files (2026-07-31)**
_(added: test_wo020_routing_drift.py — 6/6; frozen kernel 20/20)_

---

### WO-022 — Memory recall wired — DONE ✅ (Builder, 2026-07-31)

**Root cause:** `_memory_recall_response()` and `_MEMORY_RECALL_TRIGGERS` were defined in `server.py` but never called — dead code. The memory query detection block (lines 2398-2456) only ran if `_cw` (session window) was non-empty, and its trigger set didn't cover "what do you remember?" or "tell me something from your memory". Result: vault lookup never fired on general recall → LLM confabulated the stats line.

**Deliverables (`server.py` only, additive):**
- **Expanded trigger set** (18 phrases): added "what do you remember", "tell me something you", "from your memory", "from memory", "what have you kept", "what do you have stored", "what's in your memory", "pull something from memory", "recall something", "share something from", "what do you know about me", "what have you learned"
- **Restructured vault recall block**: trigger check fires FIRST (no longer gated on `_cw` non-empty); vault lookup always runs on recall intent
- **Focused topic query**: strips question/filler words (`_recall_skip` frozenset) before calling `vault_layer.lookup()` so the query is about the subject, not "what you remember". Falls back to "disenelo" if no topic words remain
- **LLM directive**: appended to `[VAULT MEMORY]` context — "Respond by sharing what you actually remember — speak from these records in eLo's voice. Never say 'Memory's running' or give a record count as a reply."

**Acceptance tests — 5/5 passed (`tests/test_wo022_memory_recall.py`):**
- AT-1: all 9 recall phrases detected correctly by expanded trigger set
- AT-2: "tell me something from your memory" / "tell me something you know" — both detect (were missing before)
- AT-3: topic extraction skips fillers for all 5 cases; focused query surfaces subject not question words
- AT-4: stats-line prohibition directive confirmed in server.py prompt injection
- AT-5: frozen kernel 20/20 — all 3 frozen test files pass

**Closes:** Vol VIII retrieval-into-conversation gap (store ✅, recall ✅).

**Test suite total: 74/74 passed across 12 test files (2026-07-31)**

---

### WO-019 — Voice tail-drop + response-mode debug — DONE ✅ (Builder 2026-07-31)

Filed by **Builder**. Status → **DONE ✅**.

**Root cause — Bug A (TTS speaks only first sentence):**
`server.py` had two sequential truncations before `_voice_speak()`:
1. `_tts_text = _bubbles[0]` — only the first `\n\n`-separated paragraph reached TTS, silently dropping every subsequent sentence the LLM put in a new paragraph
2. `ELO_TTS_MAX_CHARS = 160` default — even a single first paragraph was capped at 160 chars (≈1 sentence), preventing any trailing content from reaching TTS

`normalise()` in `backend_router.py` preserves `\n\n` paragraph structure (correct, for chat rendering), so a 2-sentence response with a paragraph break between sentences was being rendered correctly in the chat panel but only speaking sentence 1.

**Bug B (cryptic replies):** covered by WO-020 (Seam A override).

**Fix (`server.py` lines 2745–2756):**
- `_tts_text = " ".join(_bubbles)` — join all paragraphs with a space so multi-sentence responses play in full
- `ELO_TTS_MAX_CHARS` default raised 160 → 400 (enough for 2–3 sentences; long plans still capped)
- Comment updated to document the intent
- Per-turn voice/response trace: `blender/voice_trace.json` (atomic write, 7 keys: `conversation_action · tts_text · sentence_count · backend_used · tts_max_chars · bubble_count · _ts`)

**Deliverables (server.py only, additive):**
- Bug A one-line fix: `_bubbles[0]` → `" ".join(_bubbles)` at line 2752
- Cap default raised: `"160"` → `"400"`
- Voice trace write block (modelled on WO-017 routing_trace / movement_debug pattern)

**Acceptance tests — 5/5 passed (`tests/test_wo019_voice_routing.py`):**
- AT-1: 2-sentence `\n\n` response — both sentences present in TTS text (was: only first)
- AT-2: single-paragraph response unchanged
- AT-3: response over 400 chars trimmed at last sentence boundary
- AT-4: `voice_trace.json` schema validated (7 required keys)
- AT-5: frozen kernel 20/20 — all 3 frozen test files pass

**Test suite total: 79/79 passed across 13 test files (2026-07-31)**
_(added: test_wo022_memory_recall.py — 5/5; frozen kernel 20/20)_

---

### EA2-2 — Builder lane: company.* voice intents — DONE ✅ (Builder 2026-08-01)

Filed by **Builder**. Status → **IN_REVIEW** (Builder lane DONE; Unity/Design lane ongoing).

**Scope (Builder portion):** Wire 5 voice intents so eLo can respond to "how's the company", "show the board", "what needs approval", "approve WO-XXX", and "move WO-XXX to STATUS" directly from conversation.

**What was added:**
- `company_runtime/company_state_writer.py` — new `is_company_intent()` (intent detection, regex for approve/move) + `handle_company_voice_intent()` (reads `blender/company_state.json`, dispatches to existing `handle_company_approve()` stub, writes `company_actions.json` for approve/move — never touches `company_state.json` directly — LAW-017 Amendment 7 compliant)
- `server.py` — new intent dispatch block after tracker_agent / before cultural_facts (~line 2060), same pattern as existing faculties
- `tests/test_ea2_2_company_intents.py` — 11 ATs

**Design decisions:**
- `is_company_intent` returns intent key string or None (not bool) — lets the handler branch on intent type cleanly
- approve/move → write `company_actions.json` only; `watch_actions()` (background thread already running) picks it up — no direct state mutation
- Failure on approve falls back to a "check the log" spoken reply, not a crash (silent `except` in server.py per existing pattern)

**Acceptance tests — 11/11 passed (`tests/test_ea2_2_company_intents.py`):**
- AT-1 to AT-6: intent detection (briefing / board / approvals / approve-regex / move-regex / unrelated→None)
- AT-7: briefing returns live `voiced_briefing` from state
- AT-8: approvals reply includes WO ids + count
- AT-9: approve writes `company_actions.json` with correct type + work_order
- AT-10: move writes action with type/work_order/to_status
- AT-11: frozen kernel untouched — executive.py + prompts/ clean

**Commit:** `af9a451`

**Test suite total: 90/90 passed across 14 test files (2026-08-01)**
_(added: test_ea2_2_company_intents.py — 11/11)_
