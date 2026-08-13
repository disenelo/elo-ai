# ⚠ SUPERSEDED — this file was RENUMBERED. See `RD-6_Joint_Actuation_Servo_Bus_Power.md`.

**Collision resolved 2026-08-13 (Architect).** You (SEAT-RND-002) independently opened **RD-5 = "eLo
Parametric CAD Blueprint & Fabrication Handover"**, and your chain depends on it (RD-3 unparks on RD-5's URDF
+ inertia export). **Your RD-5 stands.** The actuation WO the Architect dispatched to you earlier today has
moved to **RD-6** — same content, new number. Architect's Check-Before-Build miss; owned.

**Read `RD-6_Joint_Actuation_Servo_Bus_Power.md` instead.**

## Scope reconciliation — RD-5 vs RD-6 (do NOT duplicate work)
Your RD-5 brief already ANSWERS part of RD-6. Treat these as settled by RD-5 and don't re-research them:
- **Neck articulation** → your **2-DOF Bowden cable gantry** is a valid answer to RD-6 Q1 (how to drive a
  sphere joint without fighting friction). RD-6 Q1 narrows to: the REST of the joints — per-joint POSABLE vs
  ACTUATED classification.
- **Shoulder motion** → your **offloaded motors + spherical push-rods + micro-piezo bladders** answers RD-6 Q4.
  RD-6 Q4 narrows to: confirming the **<18dB** figure in situ and the pinch-point assessment.

**RD-6 remains open and NOT answered by RD-5 on:**
- **Q2 servo bus** — which smart-servo family, and the mapping of its feedback fields to the UP report.
  **This is load-bearing:** Ruling E makes reporting law (*"movement not reported did not happen"*), and a
  standard PWM servo structurally cannot comply. Your CAD must leave room for the bus you choose.
- **Q3 power budget** — worst-case stall current, not nominal. Your base enclosure pockets depend on it.
- **Q4b HANDS** — David decided **3-finger anthropomorphic** on 2026-08-13. **Your RD-5 structural breakdown
  has no hand module.** Needs adding: tendon-underactuated vs per-joint, DOF budget, thumb opposition,
  grip force + inter-finger pinch points.
