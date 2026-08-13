---
captured: 2026-08-13
capture_rule: CLAUDE.md Rule 4b — VERBATIM, do not summarise
provenance: >
  QUESTION + design intent AUTHORED BY DAVID (the huggable-face requirement, air flow, TPU bend stiffness).
  ANSWER AUTHORED BY GEMINI (SEAT-RND-002) — material/pressure formalisation. RELAYED by David.
topic: Soft outer facial shell — TPU durometer, wall thickness, pneumatic bias pressure, hug relief, Blender cloth-pressure test workflow
lane: ROBOT HARDWARE — 🔴 RESERVED (pump · pressure). Keeps LG-2.
---

# VERBATIM — primary source, do not summarise.

## DAVID'S QUESTION / DESIGN INTENT (authored by David)

Okay now I with the specs, I should be able to do some modelling and figure out ways to test, plus figure out
what would be the right amount of air flow, and tpu bend stiffness for the model to keep it's face shape with
air in it, and can deflate reasonable, so it feels like it should hugging something soft

---

## GEMINI'S ANSWER (authored by Gemini, relayed by David)

To make the outer facial body feel soft, huggable, and expressive without losing its iconic face shape, you need to balance material durometer (hardness), wall thickness, and pneumatic bias pressure (low continuous positive pressure).

### 1. Material Selection & TPU Bend Stiffness
For a 3D-printed or cast outer soft shell that holds its form when unpressurized yet squishes comfortably when hugged, the optimal material specs are:

| Parameter | Recommended Spec | Engineering Purpose |
|---|---|---|
| Material Type | TPU 85A (3D Print) or Dragon Skin 20 Silicone (Molded) | TPU 85A offers rubber-like compliance while being easy to print airtight. Silicone gives the softest "human-grade" tactile touch. |
| Facial Shell Thickness | 1.2mm – 1.6mm (Uniform Wall) | Thinner than 1.0mm causes the nose/chin to sag under gravity; thicker than 2.0mm feels too rigid when squeezed. |
| Internal Ribbing / Geometry | Structural Bellows & Cross-Ribs | Place 0.8mm internal TPU ribs along the nose bridge and cheekbones to maintain structural shape without needing extra air pressure. |

### 2. Air Flow Rate & Pressure Calibration
The secret to a "huggable" soft-robotic shell is Low-Pressure High-Compliance (LPHC) tuning. You do not want high pressure (like a tire); you want a gentle, low-pressure air pillow.

| Operational State | Air Pressure (Target) | Physical / Tactile Feel |
|---|---|---|
| Idle / Standing | +1.5 kPa to +3.0 kPa | Maintains facial shape |
| Being Hugged (Squeeze) | Pressure surges >6 kPa | Vent opens; soft squeeze |
| Rapid Deflation | Vacuum (−2.0 kPa) | Expressive facial shrink |

**A. Air Flow Rate Requirements**
- Inflation Pump Rate: 2.5 – 4.0 L/min (achieved using low-noise micro-diaphragm or micro-piezo pumps).
- Deflation Venting: Use a mini 2-way 6V solenoid valve (12mm bore size). When an external hug is detected by the chest/belly touch sensors, opening the solenoid allows immediate air venting in <0.4 seconds.

**B. Over-Pressure Hug Relief Valve (Mechanical Passive Safety)**
- Place a passive mechanical check-valve set to open at +5.0 kPa.
- Why? When a person squeezes eLo tightly during a hug, the internal chamber volume shrinks, causing a rapid pressure spike. The passive valve dumps the excess air immediately, making eLo feel soft and yielding like a plush toy rather than an over-inflated basketball.

### 3. Modeling & Testing Workflow in Blender

**Step 1: Blender Cloth & Pressure Physics Simulation**
1. Assign a Cloth Modifier to your outer body facial mesh.
2. Under Cloth > Physics Properties, check the Pressure box.
3. Set Pressure Value = 1.5 – 2.5.
4. Set Fluid Density = 1.2 (air approximation) and Shrink Factor = −0.05 (elastic expansion).
5. Add a collision object (e.g., a sphere representing a hugging arm) to push into the face mesh. Observe how the wall thickness and pressure resist or yield to the squeeze!

**Step 2: Airtight 3D Printing Settings for TPU**
When 3D printing soft TPU bladders for pneumatics:
- Perimeters/Walls: Set to 3 or 4 continuous walls (no infill inside the shell walls).
- Extrusion Multiplier: Increase to 1.05 – 1.08 (105% – 108%) to over-extrude slightly and fuse layer lines completely airtight.
- Layer Height: Print fine at 0.12mm – 0.16mm to eliminate micro-gaps between layers.
