# RD-6 — Robot actuation architecture: joint strategy · servo bus · power budget · shoulder motion

> **⚠ RENUMBERED RD-5 → RD-6 (2026-08-13).** Collision: Gemini/SEAT-RND-002 independently opened **RD-5 = "eLo
> Parametric CAD Blueprint & Fabrication Handover"**, which their chain depends on (RD-3 unparks on RD-5 URDF).
> Their number stands; this actuation WO moves to RD-6. Architect's Check-Before-Build miss — reused a live number.
**Owner:** R&D (Gemini) — research + recommendation. **Priority:** P2. **Status:** OPEN — spec'd 2026-08-13
from David's live direction. **Lane:** ROBOT HARDWARE.
**⚠ RESERVED — keeps LG-2** per David's ruling (`CANON_RULINGS_2026-08-10.md`): robot hardware retains a real,
separate second review for **force · magnetics · pump · thermal · battery · pinch points**, and **LG-2 must not
be the person who designed the part**. This WO is **RESEARCH AND RECOMMENDATION ONLY — nothing is powered,
nothing is purchased, nothing is assembled on David's desk under this WO.**
**Source (VERBATIM):** `docs/architecture/_intake/SOURCE_2026-08-13_robot_joints_servos_pistons.md`
**Ties:** RD-CAD (head/neck safety-aware CAD) · RD-4 (inflated-TPU float) · WO-084 (eLo puppet joint library,
280mm, belly ball joint) · Vol XI Motor Cortex · Vol XIII Ch.5 (one spatial model, many bodies) · Ruling E.

## David (2026-08-13)
> "I have started the robot modelling and started to create joints, for a 3D Render, I will next need to figure
> out how to make a Japanese Sphere Joint System and Servo motors that will be able to communicate back to a
> rasberry pi and have a battery -- and also control small pistons for shoulders"

---

## THE CORE ENGINEERING PROBLEM (state this first in the report)
**A sphere joint cannot be servo-driven directly.** A ball joint has **3 rotational DOF**; a servo delivers
**1**. Japanese figure/doll systems (BJD elastic-tension · Revoltech "revolver" joints · Figma) are **PASSIVE** —
held by friction so a human poses them. A servo behind a friction ball fights the tension, stalls, and cooks.

**Architect's recommended resolution (validate or refute it — don't just accept it):**
**Keep the sphere as the AESTHETIC; drive it with a 2-DOF gimbal underneath.** A pan/tilt pair in series,
hidden under a cosmetic hemisphere shell, reads as a ball joint while being drivable.
→ **Deliverable: a per-joint classification for eLo — POSABLE (passive sphere, styling, no motor) vs ACTUATED
(driven, mechanism hidden).** Trying to actuate every sphere is where builds like this die. This classification
is the single most valuable output of this WO.

## Q1 — Joint system
- Evaluate: passive BJD/Revoltech-style spheres · 2-DOF gimbal under a cosmetic shell · parallel/tendon-driven
  (Disney-style cable) · compliant/soft joints (ties RD-4 inflated TPU).
- Recommend per eLo body region: **neck** (needs real articulation — head orientation IS his gaze, since
  **eLo has NO EYES**; attention is shown by head/body turn + glow) · **shoulders** · **hips/wishbone** ·
  **belly** (WO-084 already has a 22mm belly ball joint).
- Constraint: whatever is chosen must preserve the eLo silhouette — form is not negotiable to mechanism.

## Q2 — Servo bus: "communicate back" RULES OUT standard PWM
Standard hobby servos are **open-loop** — they accept a position and report NOTHING. David explicitly wants
feedback, and **Ruling E makes it structural**: *the body must report what it did; movement not reported did not
happen.* A dumb PWM servo **cannot satisfy canon.**
- Evaluate serial-bus smart servos: **Dynamixel** (Robotis — position/velocity/load/temp/voltage, the standard,
  expensive) · **Feetech STS/SCS** (cheap, serial bus, position+load) · **HiWonder LX-16A** (cheapest, basic feedback).
- **Daisy-chain on one UART to the Pi** — one line instead of N PWM channels, and every joint reports.
- Deliverable: recommendation with **cost per joint × joint count**, torque headroom at eLo's scale, backlash,
  holding current, **and audible noise at rest and in motion** (see Q5).
- Map the feedback fields to the **UP report** Vol XI / Ruling E require: commanded vs achieved position, load,
  temperature, error. This is the robot's version of `<action>_complete`.

## Q3 — Raspberry Pi integration + power budget
- Pi model + how the servo bus attaches (UART/USB adapter; if any PWM remains, a PCA9685 — never Pi GPIO direct).
- **Servos must NOT be powered from the Pi's rail.** Separate BEC/UBEC on the servo bus, **common ground**.
- Pi 5 wants its own regulated 5V at ~5A.
- **Battery (RESERVED — LG-2):** chemistry, capacity for a target runtime, **protection circuitry, fusing,
  charge safety, thermal behaviour**. Include a stall-current worst case, not just nominal draw — that's the
  number that starts fires.
- Deliverable: a power budget table (idle · nominal motion · worst-case stall) + a wiring topology diagram.

## Q4 — Shoulder motion (pistons)
David asked for **small pistons**. Evaluate honestly against alternatives:
- **Pneumatic:** needs pump + valves + reservoir. **The pump is RESERVED.** A compressor spooling up is LOUD.
- **Micro linear actuators:** quiet, crisp travel, simple to drive, no fluid.
- **Compliant/inflated (RD-4 TPU):** already in flight for this project — likely the more coherent thread.
- Deliverable: recommendation with a **noise figure**, and a clear statement of what pneumatics would cost in
  acoustic terms.

## Q4b — HANDS: 3-finger anthropomorphic setup (David, 2026-08-13)
> "And for the hands we will be using a 3 Finger Anthropomorphic Robotic Finger setup"

**Decided by David: three fingers, anthropomorphic.** Research the implementation, not the choice.
- **Actuation strategy:** the standard for multi-finger hands at this scale is **tendon-driven with
  underactuation** — one motor pulls a tendon through a finger whose joints flex in sequence, so the finger
  **conforms to the object it touches** without needing a motor per joint. Evaluate that against
  per-joint micro-servos (more control, far more motors, more noise, more volume in the palm).
- **DOF budget:** how many motors for three fingers? Recommend the minimum that still gives a believable
  grasp + an expressive open hand. Include whether the thumb (or its equivalent) is independently driven —
  opposition is what makes a 3-finger hand read as a *hand* rather than a claw.
- **Compliance + safety:** underactuated tendon fingers are naturally compliant, which is a **safety
  advantage** — they yield instead of crushing. Assess grip force and **pinch points between fingers**
  explicitly for LG-2.
- **Feedback (Ruling E):** the hand must report too — at minimum open/closed/holding, ideally tendon load so
  eLo knows he's actually gripping something rather than assuming it (ADR-Exec-003 Embodied Truth: he only
  says he's holding something once the body confirms it).
- **Character:** the hand is highly visible and expressive — it gestures, points, reaches (ties the desktop
  ArmAim / Two Bone IK work, WO-090). Silence at rest applies here too; fingers must not buzz while idle.
- **Scale:** must suit the eLo silhouette and the 280mm figure lineage (WO-084) — recommend a scale ratio.
- Deliverable: recommended architecture (tendon-underactuated vs per-joint), motor count, BOM + cost, grip
  force envelope, and the pinch-point assessment for LG-2.

## Q5 — THE CHARACTER CONSTRAINT (do not treat as secondary)
eLo is a **calm presence companion** (D-PRESENCE, presence over engagement). **Servo whine at rest, or a
compressor kicking in, would damage the character more than the added motion is worth.** Every recommendation
must carry a noise assessment, and **silence at rest is a hard requirement** — if a joint must hold position
audibly, prefer a mechanism that holds passively.

## Deliverables
1. Per-joint POSABLE vs ACTUATED classification for eLo.
2. Servo bus recommendation + feedback-field → UP-report mapping (Ruling E / Vol XI).
3. Power budget + wiring topology (incl. worst-case stall).
4. Shoulder motion recommendation with noise figures.
5. A **bill of materials with costs** — David is cost-sensitive; nothing gets ordered off the back of a guess.
6. **An explicit safety section for LG-2 review** — pinch points, force at each joint, thermal, battery,
   and what a soft-stop would need to do.

## HARD GATE — before ANY of this is powered near David
**The force-limiter / soft-stop scope does NOT exist** — `avatar/safety_controller.py` has no implementation.
Per David's own ruling, that must be **DONE and LG-2 reviewed before anything is powered on his desk.**
This WO produces a paper design. **Powered assembly is a separate, gated WO.**

## Done when
the six deliverables are handed back to the Architect, who routes the safety section to LG-2 and the design to
David. **No purchase, no assembly, no power under this WO.**
