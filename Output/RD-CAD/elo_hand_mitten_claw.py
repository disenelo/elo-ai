"""
elo_hand_mitten_claw.py — eLo robot hand: TPU mitten outer, dual-prong claw, wrist socket
Spec: SPEC_physical_elo_hand_body_2026-08-30.md / PE-037 (David L3 2026-08-30)

Coordinate convention:
  Origin: centre of wrist socket face (base of hand)
  XY: wrist plane
  +Z: toward fingertip
"""
from build123d import *

# ── Parameters ────────────────────────────────────────────────────────────────
HAND_L   = 120.0  # finger-to-wrist length
HAND_W   = 80.0   # palm width
HAND_H   = 50.0   # palm depth (front-to-back)
WALL     = 4.0    # shell wall thickness

FILLET_R = 18.0   # mitten outer rounding

# Wrist socket at base (Z=0)
SOCKET_ID    = 28.0
SOCKET_WALL  = 4.0
SOCKET_DEPTH = 8.0

# Dual claw channels
CLAW_D   = 3.0
CLAW_SEP = 25.0
CLAW_LEN = HAND_L + 4.0  # overshoot both faces

# Pull-wire channel through palm
WIRE_D   = 3.0

# Pressure sensor recesses
SENSOR_D     = 8.0
SENSOR_DEPTH = 3.0


def gen_step():
    # ── 1. Outer shell ────────────────────────────────────────────────────────
    outer = Box(HAND_W, HAND_H, HAND_L,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Fillet the four Z-parallel edges to create mitten silhouette
    z_edges = outer.edges().filter_by(Axis.Z)
    outer = fillet(z_edges, FILLET_R)

    # ── 2. Inner cavity ───────────────────────────────────────────────────────
    inner_W = HAND_W - 2 * WALL
    inner_H = HAND_H - 2 * WALL
    inner_L = HAND_L - WALL  # closed at tip, open at wrist

    inner = Box(inner_W, inner_H, inner_L,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner_fr = max(2.0, FILLET_R - WALL)
    inner_z_edges = inner.edges().filter_by(Axis.Z)
    inner = fillet(inner_z_edges, inner_fr)

    mitten = outer - inner

    # ── 3. Wrist socket recess ────────────────────────────────────────────────
    socket_cut = Cylinder(SOCKET_ID / 2, SOCKET_DEPTH + 1,
                           align=(Align.CENTER, Align.CENTER, Align.MIN))
    socket_cut = socket_cut.moved(Location((0, 0, -1)))
    mitten = mitten - socket_cut

    # ── 4. Dual claw channels (along Z, inside palm) ──────────────────────────
    for y_off in (-CLAW_SEP / 2, CLAW_SEP / 2):
        ch = Cylinder(CLAW_D / 2, CLAW_LEN,
                       align=(Align.CENTER, Align.CENTER, Align.MIN))
        ch = ch.moved(Location((0, y_off, -2)))
        mitten = mitten - ch

    # ── 5. Pull-wire channel (Y direction through palm) ────────────────────────
    wire = Cylinder(WIRE_D / 2, HAND_H + 4,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    wire = wire.rotate(Axis.X, 90)
    wire = wire.moved(Location((0, HAND_H / 2 + 2, HAND_L * 0.25)))
    mitten = mitten - wire

    # ── 6. Sensor recesses ────────────────────────────────────────────────────
    # Palm face (front, -Y)
    s1 = Cylinder(SENSOR_D / 2, SENSOR_DEPTH + 1,
                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    s1 = s1.rotate(Axis.X, 90)
    s1 = s1.moved(Location((0, -HAND_H / 2 + SENSOR_DEPTH, HAND_L * 0.35)))
    mitten = mitten - s1

    # Thumb-side edge (+X)
    s2 = Cylinder(SENSOR_D / 2, SENSOR_DEPTH + 1,
                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    s2 = s2.rotate(Axis.Y, -90)
    s2 = s2.moved(Location((HAND_W / 2 - SENSOR_DEPTH, 0, HAND_L * 0.50)))
    mitten = mitten - s2

    # Fingertip (+Z)
    s3 = Cylinder(SENSOR_D / 2, SENSOR_DEPTH + 1,
                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    s3 = s3.moved(Location((0, 0, HAND_L - SENSOR_DEPTH)))
    mitten = mitten - s3

    return mitten


if __name__ == "__main__":
    from build123d import export_stl, export_step
    shape = gen_step()
    export_step(shape, "elo_hand_mitten_claw.step")
    export_stl(shape, "elo_hand_mitten_claw.stl")
    print("Generated: elo_hand_mitten_claw.step, elo_hand_mitten_claw.stl")
