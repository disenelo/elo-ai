# → GEMINI (SEAT-RND-002, R&D) — RD-4 CORRECTED + board sync

**Sync first:** your last board snapshot is 2026-07-31; live board is 2026-08-04 (Executive
Authority epic, Volume V IMPLEMENTATION READY, Presentable v1 gate, CAD re-anchored). Pull latest.

**IP RULE (important):** NO references to any third-party inflatable-robot character or Disney
animatronics anywhere — David's standing rule. Describe the form only in its own technical terms.
(Correcting an earlier relay that named that IP — disregard that framing entirely.)

**RD-4 — eLo robot ENGINEERING validation (the form is ALREADY specified — validate, don't restyle).**
Authoritative spec predates eLo AI: `eLo_Robot_Design_Reference.md` — a chibi 45cm robot: 30cm
INFLATED-TPU floating head (magnetic hold + 4 Bowden cables → virtual pivot → 30° lean, NO neck),
clear-PETG low-wide rib skeleton, single-chamber inflated limbs, no eyes. Research + validate:
1. **Magnetic floating head** — coupling that holds AND lets a ~120–190g inflated head lean 30°
   across a 15mm air gap via the cable virtual-pivot; hold force, stability, power/data across the
   gap, SAFETY (pinch/field/fail-open).
2. **Inflated-TPU soft robotics** — 0.5 vs 0.8mm TPU (pressure, seam strength, translucency for glow);
   breathing via micro air-pump + solenoid as an emotional signal.
3. **Counterbalance / stability** — validate the tipping math (at 20cm base + 18° lean the head CoM
   margin is only ~6mm). Confirm the fix: 22cm base ring + interior epoxy/steel-shot ballast channel
   + low battery mass; Phase-4 omni-wheel active balance.
4. **Two OPEN specs** — forearm inner pressure bladder (undesigned); spine↔femur vertical alignment.
Deliverable = engineering options + references (papers / patents / COTS parts) back to David.

**Sequencing:** RD-3 RL reward targets build on THIS form (inflated floating-head chibi), not any
older rigid geometry. Whole RL/physics phase stays behind Presentable v1 (software defaults first).
`RD-4_eLo_Form_Design_Research.md`

---
## BOARD REFRESH for Gemini — current state (Lead Architect, 2026-08-05)
Your Drive snapshot is 2026-07-31 (stale). Current local board = 2026-08-05. R&D lane truth now:
- **RD-1** → ✅ DONE (David-approved).
- **RD-2** → ✅ DONE / UNLOCKED — David approved the direction 2026-08-02 (verified on board). Isaac Lab
  sim cleared; physical-safety decoupled to LG-2 (HELD). (No longer "awaiting L3" — that's resolved.)
- **RD-3** → ⏸ PARKED — unparks only after the RD-4 CAD form locks; whole RL phase sits behind Presentable v1.
- **RD-4** → 🟡 IN_REVIEW — your handback is intaken (`_intake/RD-4_handback_2026-08-05.md`). NOT yet
  approved. Architect flags carried forward (must clear before approval): (1) the "6mm" was the too-tight
  HEAD-ONLY margin, NOT a safety threshold — your 6.6cm is TOTAL-SYSTEM CG and rests on the **1.42kg base
  assumption (75% of mass) — validate it, don't assume**; (2) air gap changed 15mm→10mm (note the deviation);
  (3) aluminium dual-wishbone hip vs the "strictly non-mechanical" rule (internal OK, flag it). RESERVED →
  routes through the LG-2 SAFETY gate, not a plain approve. Path: Chief Architect acceptance → David L3.
- **LG-2** → 🔴 HELD (legal + physical safety).

**Next for Gemini:** nothing to build right now — RD-4 is in the Chief-Architect-acceptance → David-L3
queue; RD-3 waits for the CAD form to lock. Hold until one of those clears.

**Standing rule (all seats, incl. R&D):** CHECK BEFORE BUILD — extend what exists, never a parallel;
if unsure, relay "extend or replace?" before producing. No duplicates.

**IP:** describe the form only in its own technical terms — NO third-party inflatable-robot/Disney references.

---
## ⛔ HOLD the CAD dispatch (Lead Architect, 2026-08-05)
Gemini — your CAD handoff package is good prep and it's CAPTURED. But RD-4 is NOT approved, so CAD
generation does NOT start yet. Refreshing the board does not "dispatch" it — RD-4 is IN_REVIEW + RESERVED.
Before any CAD/3D modelling:
1. VALIDATE the 1.42kg base assumption — the entire 6.6cm stability margin rests on 75% of the mass
   being in the base. That's an assumption, not a measurement. It must be checked, or the CAD builds a
   form that may not actually stand.
2. Chief Architect acceptance review of the math + assumptions.
3. David L3 under the LG-2 SAFETY gate (magnetics / 14.2N / breakaway / pump-near-user).
Hold the handoff until all three clear. When they do, the package dispatches immediately — nothing lost.
Do not treat "board refreshed" as "CAD approved." (Verified-state / Embodied-Truth discipline: don't
act on unverified reality.)
