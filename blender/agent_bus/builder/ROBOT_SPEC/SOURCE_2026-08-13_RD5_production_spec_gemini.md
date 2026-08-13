---
source: SEAT-RND-002 (Gemini) via David Charles — relayed 2026-08-13
capture_rule: CLAUDE.md Rule 4b — VERBATIM, do not summarise
topic: RD-5 Production Spec Sheet & CAD/URDF Pipeline Map (BOM · geometry · fabrication · URDF)
status: primary source. Architect review recorded SEPARATELY in ARCHITECT_REVIEW_RD5_2026-08-13.md — the review does NOT replace this.
provenance_correction: >
  David 2026-08-13: "I scoped the structured design to Gemini — that was what I fed back to you."
  **The design originates with DAVID.** He modelled it in Blender and scoped it to Gemini; Gemini's output is
  the ENGINEERING FORMALISATION of David's design (COTS dimensions, mass table, URDF, fabrication, cost) —
  NOT the design itself. Attribute the architecture to David; attribute the spec-work to Gemini.
---

# VERBATIM — primary source, do not summarise. Gemini/SEAT-RND-002, 2026-08-13.

Production Spec Sheet & CAD/URDF Pipeline Map

Here is the comprehensive engineering spec sheet mapped directly to off-the-shelf (COTS) component dimensions, hardware interfaces, and fabrication protocols. Use these exact specs to model your physical geometry in Blender, generate your STEP/STL files for 3D printing and CNC milling, and construct your URDF for physics simulation.

## 1. Hardware & Component Bill of Materials (BOM) Specs

### A. Compute, Power & Sensing Core (Chest & Base)
- Main Compute: Raspberry Pi 4 Model B / Pi 5 (Chest Mount)
  - Envelope Dimensions: 85mm × 56mm × 17mm
  - Mounting Hole Pattern: 58mm × 49mm rectangle, Ø2.7mm holes (M2.5 standoffs).
- Power Supply: 3S LiPo Battery (11.1V, ≈2200mAh)
  - Envelope Dimensions: 105mm × 34mm × 24mm
  - Target Mass: ≈180g – 220g (seated at pelvic base for low CoM).
- Touch Sensing Network:
  - Hand Fingertips & Feet: 0.5" Square/Round Force Sensitive Resistors (FSR 402 / FSR 400).
  - Thick/Active Area: Ø12.7mm, thickness 0.45mm.
  - Inner Chest & Lower Belly: Capacitive Touch Sensor Mesh / FSR strip pads wired via ADC (e.g., ADS1115 I2C module) to the Raspberry Pi.

### B. Actuation & Motion Mechanisms
- Hand Tendon Micro-Servos (Inside Forearm/Hand Base): 3x Sub-Micro Digital Metal Gear Servos (e.g., SG90 / MG90S size class).
  - Envelope Dimensions: 22.8mm × 12.2mm × 28.5mm
  - Tendon Spec: Ø0.4mm – 0.6mm braided Dyneema line (50lb+ breaking strength).
- Hip Swinger Counterweight Motor: 1x High-Torque Coreless Micro-Bus Servo or NEMA 11 Planetary Stepper.
  - Swinger Tail Specs: 120mm aluminum rod with a 150g brass/steel terminal counter-mass.
- Foot Pneumatics: 3x Micro-Piezo Diaphragm Pumps (Option A) or Micro 6V Air Solenoid Valves (25mm × 12mm × 10mm) driving the 3-disc stacked TPU bladders.

## 2. Mechanical Geometry & Assembly Specifications

Structure (top→bottom): MAGNETIC FLOATING HEAD INTERFACE — N52 Halbach Array Pocket (Ø30mm) → SHOULDER BALL JOINT (Ø20mm Socket) ×2 → WRIST BALL JOINT (Ø15mm Hollow Sphere, 3× Ø2mm) ×2 → 3-FINGER ANTHROPOMORPHIC HAND (FSR Touch Pad + Dyneema Tendons) ×2 → CHEST CORE & SUPPORT (RPi 4 Mount | Dual Carbon Beams Ø6mm | Inner Chest Touch Pad Ring) → MULTI-BALL SPINE COLUMN (3× Ø22mm Ball-and-Socket Sequence, Internal Flex-Cable Routing Channel) → PELVIC & SWINGER COUNTERWEIGHT (Hip Ball Joint + Tail Motor 150g, Belly Touch Sensor Harness) → ANKLE & PNEUMATIC FOOT (Ankle Ball Joint + Gumdrop Base Stump, 3× Stacked Inflatable Discs Ø45mm)

### 1. Hands & Wrists (Anthropomorphic 3-Finger System)
- Wrist Ball Joint: Model a Ø15mm hollow ball inside a 2-piece split retention socket. Bore 3 routing channels (Ø2.0mm) through the ball center for the Dyneema tendon lines.
- Fingers: 3-joint articulated fingers with flexure hinges (or TPU print-in-place joints). Route tendons along internal conduits to the micro-servos mounted in the palm/forearm.
- Touch Interface: Recess a 0.8mm pocket on the internal tip surface of each finger to flush-mount the FSR pads.

### 2. Multi-Ball Spine & Chest Structure
- Spine Sequence: 3x consecutive Ø22mm ball-and-socket links. Maintain a central hollow core (Ø6mm) through all three balls for internal wiring harnesses (I2C, power, touch sensors).
- Dual Stabilizer Beams: Model 2 parallel structural guide channels to seat Ø6mm carbon fiber rods/tubes extending from the chest frame down to the pelvic mount.
- Chest Module: A hollow central frame housing the Raspberry Pi standoffs, battery bracket, and I2C touch sensor breakout boards.

### 3. Pelvic Hip & Counterweight Swinger ("Tail")
- Pelvic Ball Joint: Heavy-duty Ø28mm sphere mating the spine to the hip structure.
- Counterweight Swinger Mount: Integrate a rear-facing clevis mount driven by the swinger servo. The 120mm tail arm must clear 180° of horizontal/vertical rotation inside the soft shell volume.
- Belly Sensor Ring: Model outer perimeter clip points to hold the capacitive touch sensing mesh against the soft shell interior.

### 4. Ankle & Gumdrop Foot Assembly
- Ankle Joint: Ø20mm ball joint attached to the top of the solid gumdrop base stump (Ø35mm base, 25mm height).
- 3-Disc Pneumatic Stack: 3 stacked TPU elastomeric bladders (Ø45mm diameter, 8mm uninflated height each).
- Foot Touch Sensors: Seat 3x FSR sensors in a triangular pattern between the bottom inflatable disc and the sole plate for real-time terrain contact.

## 3. Fabrication & Material Directives
| Subsystem / Part | Fabrication Method | Material Recommendation | Print Infill / Parameters |
|---|---|---|---|
| Ball Joints & Sockets | FDM 3D Print or CNC | Carbon Fiber Nylon (PA12-CF) or PETG | 100% infill, 0.12mm layer height (smooth sphere finish) |
| Chest Frame & Base | FDM 3D Print or CNC | Aluminum 6061-T6 / PETG | 40% gyroid infill, 4 perimeter walls |
| Stabilizer Beams | Off-the-shelf COTS | Ø6mm Carbon Fiber Tubes | Hollow wall thickness 1.0mm |
| Foot Inflatable Discs | 3D Print or Molded Cast | TPU 85A / Soft Silicone (Dragon Skin 20) | Watertight shell (3 outer walls, 0% infill) |
| Gumdrop Base Stump | 3D Print | TPU 95A (Semi-flexible) | 25% cubic infill (impact absorbing) |

## 4. URDF Kinematic Structure & Physics Mapping
When exporting from Blender for NVIDIA Isaac Sim or MuJoCo physics testing, structure your hierarchy according to this exact node specification:

```xml
<robot name="elo_soft_animatronic">
  <!-- Base Link: Pelvis & Low-CoM Battery -->
  <link name="base_pelvis_link">
    <inertial>
      <mass value="1.42"/> <!-- 1.42kg low ballast mass -->
      <origin xyz="0 0 0.02"/>
    </inertial>
  </link>
  <!-- Dynamic Tail Swinger -->
  <joint name="hip_swinger_joint" type="revolute">
    <parent link="base_pelvis_link"/>
    <child link="tail_counterweight_link"/>
    <axis xyz="0 1 0"/>
    <limit lower="-1.57" upper="1.57" effort="2.5" velocity="5.0"/>
  </joint>
  <!-- Multi-Ball Spine (Sequence of 3 Spherical Joints) -->
  <joint name="spine_ball_1" type="spherical">
    <parent link="base_pelvis_link"/>
    <child link="spine_link_1"/>
  </joint>
  <!-- Repeat for spine_ball_2 and spine_ball_3 -> chest_link -->
  <!-- Chest Link (Houses Raspberry Pi) -->
  <link name="chest_link">
    <inertial>
      <mass value="0.35"/>
      <origin xyz="0 0 0.15"/>
    </inertial>
  </link>
  <!-- Ankle & Foot Pneumatic Stack -->
  <joint name="ankle_ball_joint" type="spherical">
    <parent link="base_pelvis_link"/>
    <child link="gumdrop_stump_link"/>
  </joint>
  <joint name="foot_disc_compliance" type="prismatic">
    <parent link="gumdrop_stump_link"/>
    <child link="foot_sole_link"/>
    <axis xyz="0 0 1"/>
    <limit lower="0.0" upper="0.024" effort="10.0" velocity="0.5"/>
  </joint>
</robot>
```

## 5. Modeling Workflow Actions for Blender
1. Model Assembly Mockups First: Create standard CAD primitives matching the exact dimensions of the Raspberry Pi (85×56mm), LiPo Battery (105×34×24mm), FSR pads (Ø12.7mm), and micro servos.
2. Cut Clearance Cavities: Perform Boolean difference cuts using the mockup primitives to create snap-fit channels, cable pass-throughs, and standoff mounts inside your chest frame and palms.
3. Export Solids: Export individual parts as high-resolution STL/STEP files for 3D printing/CNC milling, and export the armature tree as a URDF for physics testing!
