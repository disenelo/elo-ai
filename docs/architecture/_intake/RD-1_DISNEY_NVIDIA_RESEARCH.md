# RD-1 — Disney Soft-Animatronics + NVIDIA Robot-Learning Blueprint (eLo Robot Phase 1/2)
**Seat:** SEAT-RND-002 (R&D · Gemini) · **Relayed:** 2026-07-31 · **Status: 🟢 APPROVED — David L3 2026-07-31** (direction adopted; no hardware committed)
Provenance: `[SCIENCE]` (robotics literature) + `[ENGINEERING]` (actuation/software choices).

> Delivered via the Relay Handback Loop (`DISENELO_COMPANY_STRUCTURE.md`). Architect first-pass (L1) below.

## Executive summary
eLo's embodiment must stay soft, healing, expressive **without eyes** — expression via posture/lean, head
tilt/nod, 7-state glow, single curved mouth. This blueprint synthesises Disney soft-robotics + NVIDIA's
GPU robot-learning stack into a buildable Phase-1/2 roadmap.

## Track A — actuation blueprint (physical, Phase 1)
Trade-off for the 45cm form factor:

| Method | Expression | Noise | Weight/Power | Cost | Verdict |
|---|---|---|---|---|---|
| A. Pure pneumatic/fluidic | exceptional compliance | high (hiss/pump) | heavy | high | ❌ reject for core articulation |
| B. Rigid servo + skeletal | jerky/mechanical | med (whine) | light | low | ❌ violates soft-character rule |
| C. **Hybrid cable-driven + soft skin** | fluid, organic | **very low (silent base servos)** | moderate (base-mounted) | moderate | ✅ **primary neck/head tilt** |
| D. **Miniature pneumatic bladder** | soft breathing rhythm | silent (low pressure) | ultra-light | low | ✅ **breathing / chest inflation** |

**Recommended Phase-1 physical architecture:**
1. **Head/neck lean+tilt** — internal 2-DOF Bowden-cable (tendon) skeleton driven by **base-mounted
   high-torque silent servos** (head mass kept low → fluid, non-jerky motion).
2. **Breathing/vitality** — a single ultra-quiet micro air-pump → soft internal TPU **chest bladder**, a
   subtle organic breathing cycle **synced to the glow-state**.
3. **Panelised TPU/elastomer shell** — compliant outer skin; touch feels soft, non-mechanical.

## Track B — NVIDIA robot-learning stack (Phase 2)
- **Sim:** NVIDIA **Isaac Lab** (Isaac Sim + PhysX/Newton deformable-body) to train soft-body kinematics +
  RL policies before hardware. **Domain randomisation** (skin stiffness, cable friction, payload) for
  sim-to-real transfer; **synthetic depth/RGB** for spatial/vision tracking.
- **On-device:** **Jetson Orin Nano/NX** ↔ eLo OS Spine.
- **Scripted vs learned boundary (Phase 1 = scripted; Phase 2 = learned):**
  - **Scripted (FBX):** boot / idle / emergency-off (deterministic safety); core expressions & gestures.
  - **Hybrid (IK+scripted):** gaze/orientation tracking (glow-and-head focus, no eyes).
  - **Learned (Isaac RL / imitation):** adaptive balance & soft compliance (gentle to pushes/pokes);
    curious nudging / soft presence from human-puppeted motion data.

## 4-part relay
1. **Found:** base-motor cable-tendon = standard for low-noise fluid character motion; low-pressure bladder
   micro-pneumatics = silent expressive "breathing"; Isaac Lab natively supports deformable-body sim-to-real.
2. **Open:** power/thermal budget **Jetson Orin Nano vs Pi 5 + NPU** in the 45cm chassis; physical
   **force limiters** (clutch / current-sensing) for guaranteed soft-stop during human interaction.
3. **Recommend:** **Hybrid Bowden-cable head/neck + single chest inflation bladder + TPU shell** — full
   character compliance (soft, silent, non-mechanical), low weight, low Phase-1 COGS.
4. **Unblocks:** CAD/mechanical spec for head/neck assembly; closes the tracker "Disney soft-robot
   research 🔴"; opens **RD-2** (Isaac Lab sim setup) + **RD-5** (Kickstarter build-in-public notes).

Ref: Disney Research air-powered soft-actuator (ultra-low-friction pneumatic transmission) — cited as the
basis for the soft-body recommendation.

## Reference diagrams (from Gemini)

**Physical architecture (Track A):**
```
                                  ┌──────────────────────────┐
                                  │      Pneumatic Core      │
                                  │  (Low-Noise Air Pump +   │
                                  │   Solenoid Micro-Valves) │
                                  └────────────┬─────────────┘
                                               │
                                               ▼
┌─────────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────────┐
│ Bowden Cable Neck/Head  │◄──┤  TPU Panelised Shell     ├──►│  Inflatable Chest Pod   │
│ (Dual-Axis Servo Tilt)  │   │  (Overmolded Elastomer)  │   │  (Dynamic Breathing)    │
└─────────────────────────┘   └──────────────────────────┘   └─────────────────────────┘
```

**Sim-to-real pipeline (Track B):**
```
┌─────────────────────────────────────────────────────────┐
│                    NVIDIA Isaac Lab                     │
│  (PhysX Deformable Body + Domain Randomization)        │
└────────────────────────────┬────────────────────────────┘
                             │  Sim-to-Real Transfer
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   On-Device Deployment                  │
│       Jetson Orin Nano / NX  <──>  eLo OS Spine         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔷 Architect first-pass review (L1) — Claude

**Verdict: 🟢 accept the research; recommendation is sound and eLo-true — escalate to David L3 (robot
safety = reserved gate).**

- **Character-canon: passes.** No eyes; expression via glow + posture + mouth; base-mounted silent servos
  keep it non-mechanical; breathing-as-signal is already in the tracker concept. It **validates** the
  existing Phase-1 concept (inflated TPU shell + Bowden from base cavity + magnet-joint language) rather
  than contradicting it — good sign, not a rewrite.
- **Safety: correctly flagged.** The two open items are the right ones — (a) **force limiters / current
  sensing for soft-stop** is *mandatory* for a comfort robot near people (Legal/Product-Safety seat must
  scope this before any physical build); (b) **Jetson-vs-Pi5 power/thermal** is a real Phase-2 fork. Per
  canon, anything touching robot force/electrical is a **David L3 + human-review gate** — do not build to
  this until stamped.
- **One reconciliation note for David:** the current tracker brain is **Pi 5**; this memo introduces
  **Jetson Orin** for the *learned* (Phase 2) layer. Not a conflict — Pi 5 can run Phase-1 scripted; Jetson
  is the Phase-2 learning target. Worth deciding explicitly when Phase 2 nears (don't buy Jetson for Phase 1).
- **Scope discipline:** this is **research → a recommended direction**, not a build. Approving it = adopting
  the actuation architecture as the Phase-1 direction + opening RD-2/RD-5 and the CAD lane. No hardware is
  committed by this approval.

**On David L3 → I will:** set the eLo Robot tracker "Disney soft-robot research" to 🟢, mark RD-1 DONE,
and open **RD-2** (Isaac Lab sim setup) + the **CAD/mechanical** follow-on + **LG (Product Safety)** the
force-limiter scoping.
