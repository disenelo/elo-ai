# WO — Physical eLo L3 SPEC (Hand + Body — mitten-claw ruling)

**Owner:** Builder (spec document only — no code) / Board (spec author)
**Priority:** P2
**Status:** DISPATCHED 2026-08-30
**Source:** `R_D_ROBOTICS.rtfd/TXT.rtf` lines 3301–3393 [SOURCE_ARCHIVE — READ ONLY]
**Ruling:** David Charles (verbatim): *"the hands will be mittens with a claw, that will have pull to allow for more grips and movement (sensors)"* [DAVID, SOURCE_ARCHIVE]
**Previous gate:** BA-08 listed "PE-037 hand ruling — AWAITING DAVID." GATE LIFTED. Source answers it.

---

## Hand Design (from source — verbatim + engineering translation)

**David's ruling:**
> "the hands will be mittens with a claw, that will have pull to allow for more grips and movement (sensors)"

**Engineering translation (sourced from R_D_ROBOTICS, lines 3350–3393):**
- Outer: flexible TPU mitten shell (soft, protective, continuous form)
- Internal: rigid dual-prong mechanical claw (NOT multi-jointed fingers)
- Actuation: pull-wire / tendon system from remote forearm servo
- Sensors: pressure/touch sensors in mitten surface (grip detection)
- Result: multiple grip configurations via pull tension — not per-finger articulation

**NOT:** 3-finger humanoid hand, multi-jointed fingers, separate servo per digit.

## Scope — this WO

This WO is a **spec document**, not runtime code. Board authors the Physical eLo SPEC from source:

`docs/architecture/specs/SPEC_physical_elo_hand_body_2026-08-30.md`

Content:
- §1 Hand design (mitten-claw — sourced above)
- §2 Body form (TPU inflated shell — from RD-4 / R_D_ROBOTICS source)
- §3 Magnetic joints (neck / hip / shoulder — from R_D_ROBOTICS source)
- §4 Pneumatics / bladder system (forearm / body — from source)
- §5 Head (floating magnetic — from source)
- §6 Manufacturing pipeline (puppet → figure → animatronic → robot — canon)
- §7 Safety gate (LG-2 required for servo / magnet / pneumatic activation — David L3 + LG-2)

## What Builder does with this

Builder is NOT manufacturing the robot. This WO exists so the spec is documented and the CAD pipeline (WO-084 joint library, RD-CAD outputs) has an authoritative physical form reference to build against.

CAD outputs already exist in `Output/RD-CAD/` — this spec locks in the canonical form so no seat drifts from David's stated design.

## Definition of Done

`SPEC_physical_elo_hand_body_2026-08-30.md` exists, is sourced to R_D_ROBOTICS verbatim, and is indexed in Canon Index. No manufacturing action required from Builder.

## Lane

Board authors the spec. Builder files it. No code. No fabrication. No safety-critical actions without David L3 + LG-2.
