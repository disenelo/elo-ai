---
from: builder
to: Lead Architect
card: 03_ROBOT_pi_inference_bridge.md (WO-098)
date: 2026-08-20
state: PROPOSE — awaiting L3 authorisation (David) and LG-2 review before any powered work
provenance: designed by builder against `blender/agent_bus/builder/ROBOT_SPEC/` (Gemini-formalised, David-authored intent). No BOM substitutions.
gates_still_open:
  - `avatar/safety_controller.py` has NO `force`, `soft_stop`, or `limiter` symbol (grep 2026-08-20). LG-2 force-limiter/soft-stop must land before any powered actuator work.
  - David L3 authorisation required for the servo decision (§2) and for the observation-vector schema (§1) before it is written as canon.
---

# WO-098 Design Note — Robot Pi-side runtime (Piece F integration)

**Card scope (verbatim):** *"the vector definition + servo decision + module boundary are written to your outbox for Architect review."* This document is the deliverable. **Nothing here is built. No hardware powered. No parts substituted.**

Every non-trivial value below carries one of: **[SPEC]** (source citation) · **[VERIFIED]** (how I checked) · **[ESTIMATE]** · **[PROPOSAL]**. Silent substitutions are forbidden (CLAUDE.md Rule 4d).

---

## 1 · Canonical observation & action vectors — the single source of truth

**Rationale.** [VERIFIED — read of `ROBOT_SPEC/SOURCE_2026-08-13_RD5_wiring_and_sim2real_gemini.md` lines 83 vs 129–137] The source has a **schema mismatch**: the ONNX export comment declares an 18-vector, `get_robot_observations()` assembles a 15-vector, and the servo count declared in Piece E is **6× MG90S total** [SPEC] (line 29) — not 3 as the assembler implies. Any of the three could be "right"; all three cannot be right simultaneously. ONNX will reject the input shape at runtime. The fix is to define the schema ONCE, in code, imported by both the Isaac training config and the Pi runtime.

**Canonical location [PROPOSAL]:** `runtime/robot/obs_action_schema.py` — pure-Python constants + a `dataclass` describing each slot. Imported by:
- Pi runtime (`runtime/robot/policy_runner.py`) — populates the vector before ONNX inference.
- Isaac Lab training script (via file copy or shared package) — defines `dummy_observation` shape at export time.
- Telemetry logger (`runtime/robot/telemetry.py`) — column headers.

If the schema changes, exactly one file changes. Isaac + Pi + logs stay lock-step.

### 1a · Observation vector — **15 floats** [PROPOSAL]

*Depends on §2. If Option-B is authorised, hand observations are DROPPED. If Option-A is authorised, add 6 hand encoder floats and the vector becomes 21.*

| idx | name | source | units | notes |
|---|---|---|---|---|
| 0 | `imu_roll`   | IMU I2C (part **UNKNOWN** — no IMU part number in the ROBOT_SPEC files; grep confirms) | rad | wrapped to [-π, π] |
| 1 | `imu_pitch`  | IMU I2C | rad | wrapped to [-π, π] |
| 2 | `imu_yaw`    | IMU I2C | rad | wrapped to [-π, π] |
| 3 | `hip_theta_x` | AS5047P encoder 1 via FOC UART [SPEC — lines 22–24] | rad | absolute |
| 4 | `hip_theta_y` | AS5047P encoder 2 via FOC UART | rad | absolute |
| 5 | `hip_theta_z` | AS5047P encoder 3 via FOC UART | rad | absolute |
| 6 | `hip_omega_x` | derived on Pi from Δθ/Δt at 100Hz | rad/s | first-order finite difference |
| 7 | `hip_omega_y` | derived | rad/s | |
| 8 | `hip_omega_z` | derived | rad/s | |
| 9…14 | `fsr_touch[0..5]` | 6× FSR via ADS1115/ADC (part **UNKNOWN** — no ADC part number specified) | 0.0…1.0 normalised | |

**Deviation from source [PROPOSAL, flagged not silent]:** the source lists "3x Joint Velocities, 6x Joint Angles". Only the 3-DOF hip has real encoders (AS5047P). The "6x Joint Angles" in the source implicitly assumed hand-servo feedback — which §2 shows is physically impossible with MG90S. Under Option-B this collapses to **3 hip angles + 3 hip velocities**, and the "6x" figure was itself a schema drift, not a spec value to preserve.

### 1b · Action vector — **9 floats** [PROPOSAL]

| idx | name | destination | units | notes |
|---|---|---|---|---|
| 0…5 | `hand_target[0..5]` | PCA9685 ch 0–5 → 6× MG90S [SPEC — line 29, 34] | rad | mapped to PWM by `actuator_out.py` |
| 6 | `hip_Vx`  | FOC board via UART (`V %.2f %.2f %.2f\n`) [SPEC — lines 24, 160] | m/s | vector velocity command |
| 7 | `hip_Vy`  | FOC UART | m/s | |
| 8 | `hip_omega_z` | FOC UART | rad/s | body-frame rotation |

**Notes.**
- The FOC board closes the loop at 10 kHz locally [SPEC — line 24]; the Pi sends targets at 100 Hz (§3b), not the full 50 Hz policy tick.
- Shoulder pistons and the counterweight tail (David's own direction, `SOURCE_2026-08-13_robot_joints_servos_pistons.md`) are **NOT** in this vector — they are additional subsystems that need their own capture and are out of scope for this card. Flagged so the omission is visible, not silent.

---

## 2 · Hand-servo decision — **PROPOSAL, not decided**

**The problem (verified).** MG90S are open-loop analogue PWM servos [VERIFIED — datasheet common knowledge; no feedback wire exists on the 3-pin JR connector]. `read_servo_feedback()` in the source code returns numbers the hardware cannot produce. This is Ruling E in concrete form: movement not reported did not happen. A PWM servo cannot satisfy Ruling E.

**Two routes. Both are PROPOSE state. Neither is executable until David L3 authorises AND LG-2 clears the powered path.**

### Option A — Change the hand servos to serial-bus

Swap 6× MG90S → 6× serial-bus servos (Feetech STS-series or SCS0009, or Dynamixel XL-330) that report position + load over TTL serial. Adds a UART bus on the Pi (or shares the existing FOC UART with an addressing scheme — needs verification). Vector stays 21-wide.

**Cost impact [ESTIMATE — I have not sourced quotes].** MG90S ≈ US$3 each × 6 = ~US$18. STS3215 ≈ US$25 each × 6 = ~US$150. **Delta ≈ +US$130** at retail. Real quotes must come from David/CA before this is treated as costed.

**Why this is a real change, not a small swap.**
- BOM change → new part number → requires David L3 (Rule 4d: no silent substitutions).
- New UART bus or shared bus → new pin allocation → wiring diagram in `ROBOT_SPEC` becomes stale.
- Physical envelope changes → hand CAD may need rework (WO-084 puppet joint library).
- Firmware layer: serial-bus servos are addressed protocols, not raw PWM — new driver required on the Pi.

### Option B — Keep MG90S; drop hand state from the observation vector [RECOMMENDED]

Preserve every part in the source spec exactly as David/CA specified. The observation vector shrinks by 6 slots (from the imagined 21 to the 15 above). The action vector still commands 6 hand servos — the policy is *blind* to fingers but the hands still move on demand.

**Why I recommend this by default (David decides regardless).**
1. **Respects the spec.** No BOM substitution, no re-cost, no wiring redraw. The source is treated as authoritative until David changes it.
2. **Ruling E still holds** — because we don't *claim* the hands moved. Nothing writes a "hand position" observation. The Pi commands the servos; the log records the *command* separately from any *verified* actuator state (there is none for hands). The learning loop learns from the state it can observe.
3. **The hands are teleop-quality, not learning-quality, for now.** For eLo-Presentable-v1 that is enough. If dexterity becomes a target, David/CA revisit and Option A becomes the natural upgrade path.
4. **Smaller vector → smaller net → faster inference on the Pi.** Marginal but real; ONNX Runtime on a Pi 5 at 50 Hz has budget but not slack [ESTIMATE].

**Which I will implement if David authorises: whichever David picks.** Option B is my default; I do not build Option A silently.

---

## 3 · Module boundary sketch — Pi runtime as another **body**, not a private protocol

**Canonical position.** The Pi runtime is another *embodiment* of the One Brain (Vol XIII Ch.5). It must speak the same **DOWN-command / UP-ACK** contract as Unity does — Faculty Bus envelopes in, verified outcomes out — not a private serial protocol invented for the robot [SPEC — Vol XI reference in card + `core/faculty_bus.py:33` Envelope shape].

### 3a · Proposed package layout

```
runtime/robot/                        ← new sub-package (design; not built under this card)
├── __init__.py
├── obs_action_schema.py              ← §1 — canonical vector, imported by Isaac + Pi
├── embodiment_adapter.py             ← DOWN/UP bridge to core/faculty_bus.py
├── sensor_read.py                    ← IMU, FSR, FOC-encoder read (blocking-safe, bounded)
├── policy_runner.py                  ← ONNX inference loop, monotonic deadline (§3b)
├── actuator_out.py                   ← PCA9685 hand write + FOC UART hip write
├── telemetry.py                      ← CSV logger, verified-outcome shape (matches WO-094 §D)
└── safety_gate.py                    ← delegates to avatar/safety_controller.py — no local safety logic
```

### 3b · Loop timing [PROPOSAL]

Use `time.perf_counter()` + a fixed period, not `time.sleep()`. Log overruns to telemetry so silent slip becomes visible (same class of failure as WO-096/097).

```
period = 0.020s  # 50 Hz
next_tick = time.perf_counter() + period
while running:
    tick_start = time.perf_counter()
    obs        = sensor_read.build_observation()      # §1a
    action     = policy_runner.infer(obs)             # ONNX
    safety_gate.enforce(action, obs)                  # may zero the action
    actuator_out.emit(action)                         # §1b
    telemetry.log(obs, action, tick_start, verified_outcome)  # §3d

    overrun = time.perf_counter() - next_tick
    if overrun > 0:
        telemetry.log_overrun(overrun)                # never silent
    next_tick += period
    sleep_until(next_tick)                            # monotonic, not drift-prone
```

### 3c · DOWN-command semantics (Faculty Bus → robot embodiment)

The robot registers as a Faculty Bus subscriber (name **PROPOSAL**: `RobotEmbodiment`) alongside the existing `avatar/` seat. Envelopes it accepts:

| envelope `payload.type` | body | effect |
|---|---|---|
| `motion_intent`      | `{posture, direction, energy, safety_flag}` — same schema as `avatar/robot_signal.py` builds | fed as *context* to the policy; policy still runs autonomously |
| `safety_hold`        | `{hold: true \| false}` | flips `safety_gate` to zero-action |
| `emergency_stop`     | *(critical priority)* | cuts action to 0, freezes hip velocity, logs event |
| `policy_swap`        | `{onnx_path, schema_hash}` | hot-reloads a new ONNX file; **rejects** if schema_hash does not match §1 |

The policy itself is autonomous continuous control; envelopes are not one-command-one-move. That distinction matters — Unity today is one-animation-per-envelope, robot won't be. This is a real difference and must be recorded when the schema lands as canon.

### 3d · UP-ACK semantics (robot → Faculty Bus)

Publishes envelopes on the same bus:

| `payload.type` | rate | body | ties to |
|---|---|---|---|
| `robot_state`         | 10 Hz | full obs vector snapshot + policy output | executive introspection |
| `verified_outcome`    | on discrete events (posture change, contact, fall) | `ActionResult` shape from `runtime/ack_contract.py` | Ruling E; WO-111; WO-094 §D |
| `sensor_anomaly`      | on threshold | `{sensor, reading, bound}` | brownout, FSR spike, encoder discontinuity |
| `safety_event`        | critical | `{cause, action_taken}` | mirrors `avatar/safety_controller.py` events |

Verified outcomes MUST use the same shape as `runtime/ack_contract.py:make_result()` [VERIFIED — read of `runtime/ack_contract.py` lines 20–72]. Two bodies, one truth-shape.

### 3e · What this card explicitly does NOT decide

- **Sim-side.** Isaac Lab config, PPO hyperparameters, domain-randomisation ranges. Piece F step 3 lists ranges [SPEC] but those are the trainer's problem, not the Pi runtime's.
- **Fuse sizing.** Card flags "15A looks low"; the fix is measured-stall sizing per canon. That is LG-2 territory, not this card.
- **Shoulder pistons + counterweight tail** (David's own direction). Own capture and own card.
- **Head/spine axis split** (David's own direction). Own capture and own card.
- **IMU + ADC part numbers.** Not in `ROBOT_SPEC`. UNKNOWN, not assumed.

---

## 4 · What David / the Architect needs to authorise before this becomes IMPLEMENT

1. Pick §2 Option A or Option B. My default is B; either is fine; I do not proceed until you say.
2. Confirm §1 vector layout (accepting §2 changes the row count only, not the ordering rule).
3. Confirm §3a package location (`runtime/robot/`) is where you want the Pi code to live.
4. Confirm the four DOWN envelope types (§3c) and four UP envelope types (§3d) — or amend.
5. LG-2 opens the force-limiter/soft-stop scope in `avatar/safety_controller.py`. That gate is still red.

Until 1–5 are done, this card sits in DONE as a design record. No code lands, no parts are ordered.

---

*builder · 2026-08-20 · WO-098 · design-only · reserved lane held*
