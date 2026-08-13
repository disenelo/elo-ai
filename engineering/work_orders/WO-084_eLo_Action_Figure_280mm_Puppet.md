# WO-084 — eLo Puppet (280 mm articulated master, cut from the existing model)

**Owner:** R&D + David (CAD in **Blender**) · Architect authors the spec (markdown, not geometry).
**Priority:** P2 — R&D lane, PARALLEL to / behind Presentable (does NOT touch the finish-line 6).
**Status:** OPEN — spec'd 2026-08-08 (David + Chief Architect full design convo). **David L3** on the print.
NOT RESERVED (a print — no robot magnetics/pump/force safety gates).

## Approach (the key decision): CUT the existing eLo model — don't rebuild him
Make the complete eLo **280 mm master** first, proportions locked, then DUPLICATE and cut the copy into puppet
parts. Separate the visual body from the mechanical articulation. Keep THREE saved versions:
- `eLo_MASTER_280mm` — the untouched character (never cut).
- `eLo_PUPPET_280mm` — the cut-into-parts version.
- `eLo_PUPPET_PRINT_280mm` — parts with sockets/balls/holes/tolerances/assembly features.
**Rule:** once cut, do NOT scale pieces individually — the whole set stays at 280 mm (scale the WHOLE puppet
uniformly later for a 400–500 mm display version).

## eLo's actual anatomy (drives the mechanics — NOT a human action figure)
Oversized head (~1.5× the body) · fat belly (a mechanical cavity, not a problem) · shoulders ON the body,
arms SWING from the body · arms ~2× the size of the legs (chunky cartoon tubes) · mitten hands (NO fingers) ·
short chunky legs ending in big STOMP feet · soft/rounded silhouette, no sharp mechanical edges. The belly and
big head are assets — they hide the mechanism and make the flexible neck wire very effective.

## Part breakdown (cut planes)
Head (cut just behind the ears) · **UPPER TORSO** · **LOWER TORSO** (the two are articulated at a large
**BELLY ball joint** — NOT a front/back shell) · L arm · R arm · L leg · R leg · Neck collar. Cuts hidden
under the arm / in natural forms so the assembled puppet reads as eLo, not "a 3D-printed puppet."

## Joint architecture (final decisions)
| Joint | Type | Size tier | Notes |
|---|---|---|---|
| Head | flexible wire → **boss** | ~3 mm wire | bend/rotate head; wire anchored in a reinforced boss |
| **Belly (upper↔lower torso)** | **large ball** | belly (~22 mm) | the whole upper body leans/twists/bows on the lower body — socket in upper torso, ball on lower torso |
| Shoulder | **BUTTERFLY / pivot** (prototype this first, not ball) | — | arms swing FROM the body, not a human shoulder |
| Elbow | **ball** | medium | expressive bend + some rotation; small ball hidden in the chunky arm |
| Wrist → mitten | **ball** | small | rotate the whole mitten (no fingers needed) |
| Hip | **ball** | large | leg swings; ball on the leg, socket in the torso |
| Knee | **ball** | medium | can be slightly constrained to prefer a forward bend |
| Ankle | **OMIT v1** | — | stomp integrated into the lower leg; add a small ankle ball LATER only if posing needs it |
Size tiers: LARGE ball → shoulders/hips · MEDIUM → elbows/knees · SMALL → wrists (+ ankle later) · WIRE → neck.
(Starting ball/socket dims from the 280 mm master; clearances TUNED to printer/material — friction-fit vs free.)

## Head (the first thing to solve)
Sphere → **cut just behind the ears** → front face shell + rear skull cap (each hollow, ~2–3 mm wall). Make the
seam slightly IRREGULAR (ear → behind ear → around the skull) so it disappears into the form. **Locating pegs
(2–3)** + magnets or small screws to close → click shut / pull open for access. Ears stay on whichever shell
prints strongest.
**The BOSS = a deliberately THICK internal reinforcement** (not a thin floating cylinder) at the bottom-rear
inside, with generous fillets/ribs into the shell, so the neck-wire load spreads instead of stressing the
2–3 mm shell. The ~3 mm bendable **aluminium/armature wire** anchors into the boss and runs head → neck → torso
anchor. Optional light internal cross-brace for strength without filling the head with plastic.

## Torso — ARTICULATED at the belly (David correction 2026-08-08; supersedes the earlier front/back shell)
The torso is TWO sections that MOVE relative to each other, joined by a large **belly ball joint**:
- **UPPER TORSO** — holds the **socket** of the belly joint; shoulders mount here (butterfly OR ball);
  neck-wire anchor lives here.
- **LOWER TORSO** — holds the **ball** of the belly joint; hip sockets here.
So the upper body can lean left/right, forward/back, and twist on the lower body — combined with the two hips
that's a genuine puppet-skeleton range. Each section can still be hollowed in CAD for the wire/mount cavities;
the ARTICULATION split is upper↔lower at the belly, which is a different thing from splitting a shell
front/back. (The belly joint may want a clamp/retention variant in v0.2 since it carries the upper-body load.)

## Parametric joint library (build SEPARATELY, then Boolean into eLo — Blender)
Design the joints as a reusable, PARAMETRIC kit first — do NOT sculpt joints directly into eLo until they're
validated:
```
eLo_JOINT_LIBRARY
├─ J_Ball_Large  (Ball + Socket)   → shoulders(if ball)/hips
├─ J_Ball_Medium (Ball + Socket)   → elbows/knees
├─ J_Ball_Small  (Ball + Socket)   → wrists (+ankle later)
├─ J_Butterfly_Shoulder (Left/Right)
├─ J_Wire_Neck   (Head Boss + Torso Anchor)
└─ J_Pivot       (Pin + Housing)   → M3 pin-joint fallback
```
**Parameters** (regenerate STL from these): `BALL_DIAMETER · SOCKET_DIAMETER · SOCKET_DEPTH · CLEARANCE ·
STEM_DIAMETER · INSERTION_DEPTH · JOINT_STOP_ANGLE`. In Blender: position the joint part, **Boolean-difference
the socket into the torso/limb**, Boolean-union the ball onto the mating part. Same library reused for every
future eLo figure — not a one-off.

## Assembly discipline (the "test before you ship" rule, in plastic)
1. Print small **joint test pieces** first (`[torso test]—●—[arm test]`); tune socket/clearance to the printer
   + material (tight → loosen socket; loose → tighten clearance). 2. ONLY once the joints move right →
   integrate into the 280 mm eLo mesh. Never print the whole body to find the elbow won't move.
**Hardware:** M3 screws + washers + locknuts for pin joints (loose = floppy, tight = poseable — friction is
adjustable) · ~3 mm bendable aluminium/armature wire for the neck.

## CAD order (don't detail-first)
Phase 1 skeleton (torso · head · arms · legs) → Phase 2 joints (shoulder/hip/elbow/knee sockets+balls) →
Phase 3 head (neck collar · wire channel · boss) → Phase 4 details (face · ears · mittens · surface). Make an
ugly mechanical skeleton that MOVES before adding the beautiful character detail.

## Reconciliation (Check-Before-Build — keep it eLo, not a generic doll)
- Derived from eLo's canonical form (**RD-4**) — same silhouette/proportions.
- Shares the ONE character-model pipeline (**INT-1**): plush → figure → robot shell from a single canonical
  eLo master. Evolution path: **eLo Puppet → Figure → Animatronic → Robot**, same architecture, no throwaway.

## Definition of Done
Validated parametric joint library + tuned test pieces → a 280 mm articulated eLo cut from the master
(butterfly shoulders · ball elbows/wrists/hips/knees · wire-poseable head via the boss · stomp legs) that
poses and holds. Three model versions saved. David L3 on the physical print.

## ✅ GENERATED v0.1 (2026-08-08) — parametric joint library as REAL geometry
The `eLo_JOINT_LIBRARY` is built + dimension-verified via build123d (generated in the sandbox; the installed
CAD skill is `text-to-cad` but parametric mechanical joints are better done in code). **10** printable STLs +
STEP + parametric source at `Output/eLo_puppet_cad/`: `J_Ball/Socket_belly` (22 mm — the upper↔lower torso
pivot), `_large` (14 mm shoulder/hip), `_medium` (10 mm elbow/knee), `_small` (8 mm wrist) — snap-fit
(retention lip + relief slot); `J_Neck_Boss` (wire channel + grub lock); `J_Torso_Anchor`. Re-gen from params
in `elo_joint_library.py`. NOT yet done: butterfly
shoulder + M3 pivot (v0.2), and Boolean-into-the-eLo-mesh (after printed fit confirmed). Print `J_*_medium`
first to dial clearance.

## Lane
Architect = this spec + the parametric CAD deliverable (David directly requested the geometry; R&D/CAD domain,
no owning seat, not eLo runtime). David + R&D do the Blender cutting + mesh integration. Ties RD-4 (form) ·
INT-1 (shared model) · RD-CAD (robot, downstream).
