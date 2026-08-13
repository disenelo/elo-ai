# INTAKE — RD-4 Handback (Gemini / SEAT-RND-002, 2026-08-05) · status IN_REVIEW

Filed to _intake per Gemini's request. NOT approved — staged for Chief Architect acceptance + David L3.

## Summary (as submitted)
- **Magnetic head:** NdFeB N52 Halbach array + 2-DOF Bowden neck gantry; 10mm ±2mm air gap; 14.2N
  attractive bias w/ dynamic tensioners.
- **Counterbalance:** 45cm chassis / 22cm base (R=11cm); base 1.42kg + upper 0.48kg = 1.90kg; 18° lean
  shifts CG 4.4cm → 6.6cm margin.
- **Forearm:** Option A micro-piezo diaphragm pumps + TPU micro-bladders (32g, <18dB).
- **Spine↔femur:** TPU spring spine → dual-wishbone aluminium hip; 85% load to base plate.
- **New open item:** thermal dissipation inside sealed plush cover under sustained compute.

## Architect flags CARRIED FORWARD (unresolved in this handback — must clear before approval)
1. The "6mm" was the too-tight HEAD-ONLY margin, NOT a safety threshold to "clear." The 6.6cm figure is
   TOTAL-SYSTEM CG with a heavy base — not contradictory, but the framing needs fixing AND the **1.42kg
   base (75% of mass)** is an ASSUMPTION to validate, not a measured value.
2. Air gap 15mm→10mm is a deviation from the reference spec — conscious change, note it.
3. Aluminium dual-wishbone hip vs the "strictly non-mechanical" character rule — internal load-path is
   OK but it's a philosophy call to make consciously.
4. RESERVED: magnetics / 14.2N / breakaway / pump-near-user → route through the LG-2 safety gate, not a
   plain approve.

## Gate
Chief Architect acceptance review ("built correctly?" — the math + assumptions) → David L3 (RESERVED +
LG-2). Spec stays DIRECTIONAL (David: a structure to build on). Unblocks CAD tooling + unparks RD-3 only
after the CAD form is locked.
