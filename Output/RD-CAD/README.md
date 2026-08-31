# RD-CAD — eLo Physical Robot Reference CAD

Authority: PE-037, David L3 ruling 2026-08-30. Gate lifted for CAD generation.
Spec: `docs/architecture/specs/SPEC_physical_elo_hand_body_2026-08-30.md`
Generated: 2026-08-31

---

## Parts

### elo_hand_mitten_claw
- **Files**: `elo_hand_mitten_claw.stl`, `elo_hand_mitten_claw.step`
- **Generator**: `elo_hand_mitten_claw.py`
- **Spec**: 120 × 80 × 50 mm. Rounded mitten outer shell, 4mm wall. Dual 3mm claw channels (25mm c-c). Pull-wire channel through palm. 3× 8mm sensor recesses. Wrist socket 28mm ID × 8mm deep.
- **Material intent**: TPU (flexible outer shell)

### elo_neck_magnetic_housing
- **File**: `elo_neck_magnetic_housing.stl`
- **Generator**: `elo_neck_magnetic_housing.py`
- **Spec**: 25mm ball (reference) + socket housing. Socket 26mm ID, 270° capture. 2× 5mm wire channels. Base flange 40mm OD, 6mm thick, 4× M3 at 30mm bolt circle.
- **Note**: ball geometry is reference only — actual magnet ball is a purchased component

### elo_body_shell_inflated_reference
- **File**: `elo_body_shell_inflated_reference.stl`
- **Generator**: `elo_body_shell_inflated_reference.py`
- **Spec**: 220 × 160 × 120 mm. Rounded chibi form, 6mm wall. Neck ring 50mm ID at top. 4× anchor bosses (10mm dia × 15mm, at shoulder ±60mm and hip ±50mm). Bladder inlet 12mm at rear base.
- **Purpose**: proportion reference and skeleton anchor map only — not a final fabrication shell

---

## Usage

All generators require `build123d` and `cadpy` (installed in miniconda):

```bash
~/miniconda3/bin/python3 elo_hand_mitten_claw.py
~/miniconda3/bin/python3 elo_neck_magnetic_housing.py
~/miniconda3/bin/python3 elo_body_shell_inflated_reference.py
```

Re-run any generator after parameter edits. STEP files are primary; STL is for preview/slicing.
