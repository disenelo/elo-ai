# 03_ROBOT_pi_inference_bridge.md — Robot control loop comes into the Builder lane

**WO:** WO-098 (robot Pi-side runtime) · **Seat:** builder · **Priority:** P3 — **DESIGN ONLY, do not build yet**
**Reserved?** 🔴 **YES — robot hardware. Keeps LG-2.** No powering, no purchasing under this card.
**Source (VERBATIM):** `docs/architecture/_intake/SOURCE_2026-08-13_RD5_wiring_and_sim2real_gemini.md`
Provenance: authored by Gemini (R&D formalisation), relayed by David. Underlying design intent is David's.

## Why this is yours
David: *"This all will need to link to the Builder as it will be robot related."* The robot's Pi-side runtime —
sensor read → ONNX policy inference → motor command — is **eLo-OS Python**, so it lands in your lane, not the
Designer's. It is the same brain in a different body (One Brain → many embodiments, Vol XIII Ch.5).

## 🔴 READ THE FULL SPEC — DO NOT WORK FROM THE SUMMARY BELOW
**David 2026-08-13: "No omitting of information — this is very important information. Although it can change
with how it moves, still need to config it in parts to work exact as [specified]."**

**The complete verbatim spec is in `blender/agent_bus/builder/ROBOT_SPEC/` (4 files, 577 lines):**
- `SOURCE_2026-08-13_robot_joints_servos_pistons.md` — David's own direction: sphere joints, servos↔Pi,
  battery, shoulder pistons, 3-finger hands, counterweight tail, head/spine axis split
- `SOURCE_2026-08-13_RD5_production_spec_gemini.md` — BOM with exact COTS envelopes, mechanical geometry per
  subsystem, fabrication matrix, URDF structure
- `SOURCE_2026-08-13_RD5_mechanical_mass_RL_cost_gemini.md` — mass matrix + CoM, Isaac RL pipeline,
  fabrication strategy, full cost breakdown, hand build guide + hand subsystem budget
- `SOURCE_2026-08-13_RD5_wiring_and_sim2real_gemini.md` — **the wiring/integration spec + the ONNX pipeline
  with working code** (this card's subject)

**Every dimension, part number, pin, voltage and tolerance in those files is authoritative.** Parts must be
configured EXACTLY as specified. Values may evolve as the movement work develops — but they change by David's
decision recorded in a new source capture, **never by a seat quietly substituting something.** If a spec value
looks wrong, **flag it to the Architect; do not silently deviate.**

The section below is an ORIENTATION SUMMARY ONLY — it is not a substitute for the source files.

## What's being proposed (orientation only — read the source for full detail)
- **Hip:** a **3-DOF actively-driven spherical joint** — 3× TYI 2807 brushless outrunners at 120° with omni-wheels
  on a Ø80mm elastomeric ball, AS5047P encoders, triple-axis FOC board. Pi sends `[Vx, Vy, ωz]` @100Hz; FOC
  closes the loop locally @10kHz.
- **Hands:** 6× MG90S on a PCA9685 (I2C), on their own 6V UBEC rail.
- **Power:** 3 isolated rails off a 3S LiPo (raw 11.1V → FOC · 5.1V/5A → Pi · 6V/5A → servos), 15A fuse,
  single-point common ground, BMS/low-voltage alarm, motor wiring ≥20mm from I2C/SPI.
- **Learning:** Isaac Lab PPO → export `elo_policy.onnx` → ONNX Runtime on the Pi at 50Hz, with domain
  randomisation for sim-to-real.

## 🔴 TWO CONCRETE BUGS in the proposed control loop — fix in design before any code
1. **The observation vector doesn't match itself.** The export comment says **18 values**
   `[Roll, Pitch, Yaw, 3x joint velocities, 6x joint angles, 6x FSR]` = 18, but `get_robot_observations()`
   assembles **15** `[3 IMU + 3 hand + 3 hip + 6 FSR]`. **ONNX will reject the input shape at runtime.**
   Whatever the final vector is, it must be defined ONCE and shared between the Isaac training config and the
   Pi loop — a single source of truth, not two comments that drift.
2. **`read_servo_feedback()` cannot work with MG90S.** MG90S are **open-loop PWM** — they report nothing.
   The loop feeds "hand positions" into the policy that the hardware physically cannot supply.
   → Either **swap the hand servos to serial-bus (Feetech SCS0009 / STS-series) which do report position+load**,
   or **remove hand state from the observation vector** and accept the policy is blind to the fingers.
   **This is Ruling E in concrete form:** *movement not reported did not happen.* A PWM servo cannot satisfy it.
   The FOC hip is fine — AS5047P encoders report properly.

## 🟠 Other design notes for you
- **15A fuse looks low** for 3 brushless outrunners plus servos plus Pi. Size it against measured stall, not
  nominal — and per canon, fuse for the worst case.
- **`max_current=5000` in `/boot/firmware/config.txt`** is correct for Pi 5 GPIO-powered operation; keep it.
- **Loop timing:** the `time.sleep()` pattern drifts. For a 50Hz control loop use a monotonic deadline
  (`time.perf_counter()` + fixed period) and log overruns — a control loop that silently slips is the same
  class of failure as WO-096/097 (silent degradation nobody is told about).
- **Telemetry → the learning loop:** the CSV logging in Step 3 is the robot's version of WO-094 §D. Make it
  emit the same **verified-outcome** shape the desktop uses, so both bodies feed ONE learning loop
  (Ruling F: identity from the spine, skill learned from verified consequences).

## Scope of THIS card (design only)
1. Define the **single canonical observation/action vector** shared by Isaac and the Pi.
2. Decide the **hand servo question** (serial-bus vs drop hand state) and record it.
3. Sketch the runtime module boundaries — where this sits relative to `runtime/` and the Faculty Bus. It is
   another **body**, so it must speak the same DOWN-command / UP-ACK contract as Vol XI, not a private protocol.
4. **Write nothing that touches hardware. No purchase. No power.** The force-limiter/soft-stop still does not
   exist in `avatar/safety_controller.py` and gates all powered work.

## Done when
the vector definition + servo decision + module boundary are written to your outbox for Architect review.

---

## Close-out (builder · 2026-08-20)

**Status:** DONE — design-only deliverable per card scope.
**Deliverable:** `blender/agent_bus/builder/FROM_BUILDER_2026-08-20_03_ROBOT_pi_inference_bridge_DESIGN.md`
**Acceptance:** vector definition (§1) + servo decision (§2, PROPOSE) + module boundary (§3) written to outbox for Architect review — matches card "Done when".
**Reserved-lane compliance:** no hardware touched, no purchase, no power, no BOM substitution. LG-2 force-limiter gate still open (verified: `avatar/safety_controller.py` grep for force/soft_stop/limiter returns nothing).
**State per SEAT_CONTRACT four-states:** vector schema + module boundary = PROPOSAL. Servo choice = PROPOSE, awaiting David L3. Nothing marked AUTHORISED or IMPLEMENT.
**Commit:** 234fc995a12bed71d328365dd437474d3ffa1ec3
