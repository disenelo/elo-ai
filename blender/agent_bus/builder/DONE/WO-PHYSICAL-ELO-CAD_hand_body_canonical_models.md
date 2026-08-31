# WO-PHYSICAL-ELO-CAD — Physical eLo Canonical CAD Models
**From:** Board / Lead Architect  
**Date:** 2026-08-31  
**Priority:** P2  
**Authority:** David L3 ruling 2026-08-30 (PE-037 mitten-claw hand — gate lifted) + SPEC_physical_elo_hand_body_2026-08-30.md  
**Spec:** `docs/architecture/specs/SPEC_physical_elo_hand_body_2026-08-30.md` (canonical form — read before starting)  
**Safety gate:** LG-2 required before any physical fabrication (servo / magnet / pneumatic activation). CAD generation is Board-lane only — no physical build without David L3 + LG-2.  
**Output:** `Output/RD-CAD/` — update / add files to match canonical spec  
**CAD tools:** `text-to-cad` skill (earthtojake/text-to-cad) OR `build123d` in sandbox

---

## What to produce

Update / create canonical STL/STEP outputs in `Output/RD-CAD/` that match the ratified spec:

### 1 — Hand (mitten-claw form — PE-037 ruling)

Produce: `Output/RD-CAD/elo_hand_mitten_claw.stl` and `.step`

**Canonical form (from spec §1):**
- Outer shell: rounded mitten silhouette — no individual finger separation
- Internal mechanism channel: dual-prong claw with pull-wire routing channel through palm
- Pressure sensor mount points: 3 per hand surface (palm, thumb-side, finger-tip region)
- Forearm connection interface: standard wrist socket matching shoulder/hip joint spec

### 2 — Neck magnetic ball joint housing

Produce: `Output/RD-CAD/elo_neck_magnetic_housing.stl`

**Canonical form (from spec §3 + R_D_ROBOTICS):**
- Magnetic ball-and-socket, floating head clearance 2–4mm
- Socket: captures ball with ~270° of articulation
- Wire routing channels for head electronics

### 3 — Inflated body shell reference volume

Produce: `Output/RD-CAD/elo_body_shell_inflated_reference.stl`

**Canonical form (from spec §2):**
- Inflated TPU outer shell shape — rounded, squashable proportions
- Internal skeleton anchor points marked as mounting features
- Bladder inlet port location
- Match eLo character proportions from character design canon

### Verification

For each model:
- STL must be watertight (manifold)
- Scale: eLo target height ~35–45cm (use midpoint 40cm as reference)
- All files saved to `Output/RD-CAD/`
- Update `Output/RD-CAD/README.md` (or create if absent) with model inventory

**Do NOT begin any physical fabrication. CAD models only.**
