---
id: RD-4
title: "eLo robot ENGINEERING validation — inflated-TPU floating-head chibi form (spec already exists; validate the hard parts)."
owner_seat: SEAT-RND-002 (Gemini · Robotics R&D)
priority: P1 (R&D — feeds the CAD rework)
review_required: David (design ideas come back to him)
status: READY → dispatched to Gemini (drive)
depends_on: builds on RD-1 ( soft-robotics, DONE)
feeds: the CAD rework (supersedes RD-CAD rigid neck) → then RD-3 RL reward targets on the REAL form
created: 2026-08-03
---
# RD-4

> IP RULE: NO third-party inflatable-robot character or Disney references anywhere
> (David's standing rule). Provenance: robot body predates eLo AI — foundational form the
> software aligns to. Authoritative source: `eLo_Robot_Design_Reference.md` (2026-06-29).
 — eLo form design research (David's references → in-depth design ideas)

## Brief (from David 2026-08-03)
Research the following design elements in depth and feed DESIGN IDEAS back to David. Go as deep as
the literature/patents/teardowns allow.

1. **the inflated soft form () inflatable soft-form.** The core aesthetic + movement: rounded, huggable,
   low-rigidity body; unhurried, floaty, settling motion. Research real inflatable/soft-robotics
   body structures — vinyl/TPU air-bladder bodies over an internal frame, soft actuation, how to
   get that settling movement quality, safety of a soft shell for human interaction.
2. **expressive soft-form animatronics.** Expressiveness of a soft, segmented, non-humanoid
   character — how it reads as warm + alive in face and gesture. Research 's soft-robotics /
   character-animatronics work (ties to RD-1) for expression mechanisms on a simple form.
3. **Floating head on MAGNETS — no connected neck.** The head holds/levitates above the body by
   magnetic coupling with an air gap. Research: magnetic levitation vs. magnetic coupling for a
   head module, stability + hold force, how it moves/gimbals without a mechanical neck, power/data
   across the gap, and SAFETY (pinch, field, fail-open). This SUPERSEDES the rigid 2-DOF Bowden neck.

## Deliverable
In-depth design ideas + references for each, back to David — feasible approaches, trade-offs,
example systems/papers/patents. This is design exploration, not a build.

## Sequencing
- Feeds the CAD REWORK (retires the connected-neck geometry).
- RD-3 (RL reward targets from eLo motion vocabulary) should NOT compute deep reward math on the OLD
  rigid form — hold until the new soft-form + floating-head design settles, so rewards target the
  REAL robot. Whole RL/physics phase sits behind Presentable v1 (defaults first — David's gate).

---
## RECORDED R&D INTAKE — Gemini (via David), 2026-08-05
*Provenance: Gemini (SEAT-RND-002) pastes R&D to David → David pastes to the Lead Architect → recorded
here (Gemini cannot write docs; this is its record). Three pastes: ArXiv synthesis, CAD blueprint,
physics-sim pipeline. Status: RECORDED · IN-REVIEW · **NOT dispatched** (gate below).*

### ⚠ Source check — ArXiv 2605.06593 (verified by the Architect, honest finding)
The paper is **real**, but it is **"ReActor: Reinforcement Learning for Physics-Aware Motion
Retargeting"** — an RL / motion-retargeting paper. It is **NOT** a source for "integrated compliant
shells / adaptive joint load-offloading / soft-actuation boundaries." Gemini's synthesis matrix
**misattributes** hardware methodology to it. Consequence:
- The CAD parametric bounds below are **RD-4's own prior engineering numbers**, not paper-derived
  "state-of-the-art." They are NOT "locked by SOTA" — treat them as the current candidate spec, still
  pending validation.
- The paper IS legitimately relevant to **RD-3** (RL motion), NOT to the hardware form. Filed there.

### Recorded candidate CAD bounds (the form to validate, not to print)
1. **Base counterbalance:** 220 mm dia footprint; 1.42 kg base ballast (battery + PCB + base servos);
   dynamic CG within a 4.4 cm offset envelope under 18° tilt (→ ~6.6 cm margin *if* the 1.42 kg holds).
2. **Spine + hip skeleton:** TPU spring spine → dual-wishbone aluminium hip; absorbs ~85% vertical load,
   decoupling the soft plush from mechanical stress. (Internal metal = flagged vs "non-mechanical" rule.)
3. **Floating facial pod:** 2-DOF cable-driven Bowden neck gantry; NdFeB N52 Halbach array, 14.2 N
   attraction bias; 10 mm ±2 mm non-contact air gap. (Deviates from the reference 15 mm gap — noted.)
4. **Soft forearm actuation:** micro-piezo diaphragm pumps (~32 g, <18 dB) + TPU micro-bladders; internal
   routing channels only.

### Recorded physics-sim options (for the RL/physics phase — behind Presentable v1)
Isaac Lab/Sim (USD/URDF — GPU RL + PhysX soft-body) · MuJoCo (MJCF/URDF — fast precise rigid-body, CG
margin + Bowden tendon forces) · Drake (URDF/SDF — trajectory/balance optimisation) · Blender/Bullet
(OBJ/FBX/STL — quick visual collision/pinch pass). Workflow: CAD STEP/STL → URDF/MJCF (onshape/fusion2urdf,
inertia tensors) → sim engine → sim-to-real loop. Recorded as reference; not started (gated behind v1).

### ⛔ GATE — recording is NOT approval (unchanged)
CAD generation does **not** start on this record. Before any CAD/print, all three must clear:
1. **Validate the 1.42 kg base** — the entire ~6.6 cm stability margin rests on it. This is David's
   Blender physics test (`Output/RD-CAD/PHYSICS_TEST_softform_v1.md`), not an assumption.
2. **Chief Architect acceptance** of the math + assumptions ("built correctly?").
3. **David L3 under the LG-2 safety gate** — RESERVED items: magnetics / 14.2 N attraction / breakaway /
   pump-near-user. Not a plain approve.
Until then: RD-4 stays IN_REVIEW, RD-3 parked, no CAD dispatch. When the three clear, the recorded
bounds above dispatch immediately — nothing lost.

---
## CAD BRIEF 2026-08-05 — engineering references → eLo's OWN form
Gemini's "CAD Build Brief" cited a character-animatronic section view and a Baymax body wireframe as
reference models. David's approach (stated): reference models INFORM original engineering — he is not
recreating either; eLo's form is its own. So: use the transferable ENGINEERING freely; keep eLo's
silhouette/character its own (`eLo_Robot_Design_Reference.md`); and keep third-party character NAMES out
of eLo's shipped identity + marketing (the actual standing rule). Not a "violation" — normal referencing.

**IP-CLEAN engineering deltas kept (eLo's own terms — no third-party derivation):**
- **Height:** ~450 mm full standing form; base 220 mm × 45 mm pan (v2 base was 40 mm — minor).
- **Materials:** head pod PA12-CF (carbon-nylon); central spine TPU 95A over a 7075-T6 / 6061 alloy core;
  base plate 6061-T6 CNC + moulded shell.
- **Base internals (low CoM):** 3S LiPo placed as low as possible; Jetson-class compute + IMU + radio on
  a base compute ring; base servos. All mass concentrated low — supports the 1.42 kg ballast goal.
- **Spine:** Ø25 mm load-bearing column anchored to the base plate; ~8 mm inner clearance to the soft
  outer skin so the skin stays UNWEIGHTED; carries ~85 % of vertical load.
- **Shoulder/arm (general animatronic principle — actuators in the body, not the joints):** primary
  shoulder actuators sit in the upper-torso cavity, driving the shoulder pivots via dual-axis spherical
  push-rod linkages; pneumatic tubing routes through the upper arm to the forearm bladder.
- **Head:** 2-DOF differential Bowden cable gantry in the upper spine tip; N52 Halbach ring in the pod
  base; 10 mm ±2 air gap, 14.2 N bias; compact eye yaw/pitch + jaw via micro-servos (eLo's own face).
- **Export:** STEP/IGES for prototyping (done for v2 parts); URDF/MJCF (link masses, inertia tensors,
  joint limits) for Isaac/MuJoCo — belongs to the RL/physics phase, BEHIND Presentable v1.

**Status:** deltas recorded for a future v3 (built in eLo's own terms). Gate UNCHANGED — no print/build
until 1.42 kg Blender CG pass → Chief Architect acceptance → David L3 under LG-2.

### Reference images reviewed 2026-08-05 (David showed them)
- IMG1 = a soft-robotics CHARACTER animatronic section view (a bird form): actuators (yellow), soft PU
  foam skin (cyan), compute (purple), with EYE / JAW / SHOULDER linkage callouts. Character-specific
  silhouette = NOT copied. IMG2 = a **Baymax** inflatable-body wireframe = Disney IP = NOT used.
- **The line:** eLo's LOOK/silhouette stays its own (`eLo_Robot_Design_Reference.md`, eyeless chibi soft
  form). Neither character is named in eLo docs/marketing. Only GENERIC, widely-published robotics
  construction is transferable — recorded below in eLo's own terms.

### Form architecture — David's framing (2026-08-05, how the references map)
eLo is a **two-zone structure**, David-integrated:
- **BOTTOM = load-bearing leg/base structure → bottom-heavy.** The leg/base mechanics (QDD leg
  actuators + the 220 mm / 1.42 kg counterbalance base) carry the mass low. This is the stability
  engine — and exactly what the Blender CG test validates.
- **TOP = inflated soft skeleton.** The upper body is the inflated TPU soft-form over a light rigid
  spine, with the floating head above it.
- **David is the integrator:** references inform each zone; he pieces it together, adds the direction,
  plans the structure, and tests it. The CAD/Architect role = generate the geometry he directs and give
  him something to test — not to originate the design.
- **v3 assembly proxy built (`_gen_softform_v3.py`, 2026-08-05):** parts 07 leg structure · 08 inflated
  body shell · 09 full-form assembly. Proxy result: static CG at 76 mm of ~384 mm (20% up), base ≈ 59%
  of mass → bottom-heavy confirmed in proxy. Height ~384 mm vs 450 target = proxy stacking, tunable.
  The Blender 18° tilt CG test is still the gate for the 1.42 kg validation.

**Transferable (non-IP) engineering from IMG1 — a genuinely useful COTS shortlist for eLo:**
- **Actuator classes:** smart serial servos (Dynamixel XH540 / XH430 / XC330 class) for head/neck/jaw
  micro-motion; quasi-direct-drive motors (Unitree 4010 / 8010 class) for base/leg torque. A concrete
  buy-list to price against eLo's own joints — supersedes hobby servos where torque/precision matters.
- **Layout principle (matches our deltas):** battery + Jetson-class compute + secondary compute + radio
  + IMU arranged LOW on a base ring → low CoM (supports the 1.42 kg base goal).
- **Soft-shell principle:** soft PU foam / TPU outer skin over a rigid articulated core, skin UNWEIGHTED.
- **Offloaded 2-DOF shoulder:** two body-mounted revolute actuators drive the shoulder pivot via linkage
  (actuators in the torso, not the arm) — eLo's own arm, this placement principle only.
- eLo is EYELESS per its reference, so the eye-yaw/pitch/eyelid mechanism does NOT transfer; a jaw/mouth
  four-bar transfers only IF eLo's face design calls for a moving mouth (David's call).
