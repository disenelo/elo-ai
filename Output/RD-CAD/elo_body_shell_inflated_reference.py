"""
elo_body_shell_inflated_reference.py — eLo robot body: inflated TPU shell reference volume
Spec: SPEC_physical_elo_hand_body_2026-08-30.md / PE-037 (David L3 2026-08-30)

Coordinate convention:
  Origin: centre of body at mid-height
  XY: horizontal cross-section plane
  +Z: up (toward neck)

This is a REFERENCE SHELL only — proportion guide for physical build.
No eyes. No fingers. Rounded chibi form.
"""
from build123d import *
import math

# ── Parameters ────────────────────────────────────────────────────────────────
BODY_H    = 220.0  # total body height
BODY_W    = 160.0  # widest point (shoulders/chest), X axis
BODY_D    = 120.0  # depth front-to-back, Y axis
WALL      = 6.0    # TPU bladder wall thickness

# Chibi form: slightly wider at chest, taper toward hips
CHEST_W   = BODY_W
HIP_W     = BODY_W * 0.75
CHEST_D   = BODY_D
HIP_D     = BODY_D * 0.80

# Neck ring at top (opening for head attachment)
NECK_RING_D   = 50.0   # outer diameter of neck opening
NECK_RING_H   = 15.0   # height of neck ring feature

# Anchor bosses: cylindrical standoffs inside shell (for skeleton attachment)
BOSS_D        = 10.0
BOSS_H        = 15.0
# Shoulder bosses: ±60mm from centre, at 65% height from base
SHOULDER_X    = 60.0
SHOULDER_Z    = BODY_H * 0.65 - BODY_H / 2
# Hip bosses: ±50mm from centre, at 25% height from base
HIP_X         = 50.0
HIP_Z         = BODY_H * 0.25 - BODY_H / 2

# Bladder inlet port (rear face, at 15% height from base)
BLADDER_PORT_D  = 12.0
BLADDER_Z       = BODY_H * 0.15 - BODY_H / 2


def gen_step():
    # ── 1. Outer body shell ───────────────────────────────────────────────────
    # Model as a rounded ellipsoid-like form via a lofted cross-section.
    # Use a simple two-section loft: chest ellipse → hip ellipse
    # Then cap the top and bottom with fillets.

    # Instead of a true loft (which needs face normals to match), we build
    # the body as a scaled + filleted box to approximate the chibi silhouette.

    # Base shape: box with chest dimensions, height centred at origin
    outer = Box(CHEST_W, CHEST_D, BODY_H,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))

    # Round Z-parallel edges strongly → inflated/chibi appearance
    outer = fillet(outer.edges().filter_by(Axis.Z), 40.0)

    # ── 2. Inner cavity (shell body) ─────────────────────────────────────────
    inner_W = CHEST_W - 2 * WALL
    inner_D = CHEST_D - 2 * WALL
    inner_H = BODY_H - 2 * WALL

    inner = Box(inner_W, inner_D, inner_H,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))
    inner = fillet(inner.edges().filter_by(Axis.Z), max(2.0, 40.0 - WALL))

    body = outer - inner

    # ── 3. Neck opening at top ────────────────────────────────────────────────
    neck_cut = Cylinder(NECK_RING_D / 2, NECK_RING_H + 2,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))
    neck_cut = neck_cut.moved(Location((0, 0, BODY_H / 2 - NECK_RING_H)))
    body = body - neck_cut

    # Neck ring collar around the opening
    neck_ring = (
        Cylinder((NECK_RING_D + WALL * 2) / 2, NECK_RING_H,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Cylinder(NECK_RING_D / 2, NECK_RING_H + 1,
                    align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    neck_ring = neck_ring.moved(Location((0, 0, BODY_H / 2 - NECK_RING_H)))
    body = body + neck_ring

    # ── 4. Skeleton anchor bosses (internal, +X protrudes inward) ─────────────
    def make_boss(x, z):
        boss = Cylinder(BOSS_D / 2, BOSS_H,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Bosses mount on the inner wall, pointing inward (toward centre)
        # Orient along X axis: boss protrudes from ±X inner wall
        boss = boss.rotate(Axis.Y, 90 if x > 0 else -90)
        start_x = (CHEST_W / 2 - WALL) * (1 if x > 0 else -1)
        boss = boss.moved(Location((start_x, 0, z)))
        return boss

    body = body + make_boss(SHOULDER_X, SHOULDER_Z)
    body = body + make_boss(-SHOULDER_X, SHOULDER_Z)
    body = body + make_boss(HIP_X, HIP_Z)
    body = body + make_boss(-HIP_X, HIP_Z)

    # ── 5. Bladder inlet port (rear face, through outer wall) ─────────────────
    bladder_port = Cylinder(BLADDER_PORT_D / 2, WALL + 4,
                             align=(Align.CENTER, Align.CENTER, Align.MIN))
    bladder_port = bladder_port.rotate(Axis.X, -90)
    bladder_port = bladder_port.moved(Location((0, CHEST_D / 2 - WALL - 2, BLADDER_Z)))
    body = body - bladder_port

    return body


if __name__ == "__main__":
    from build123d import export_stl
    shape = gen_step()
    export_stl(shape, "elo_body_shell_inflated_reference.stl")
    print("Generated: elo_body_shell_inflated_reference.stl")
