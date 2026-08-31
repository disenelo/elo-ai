"""
elo_neck_magnetic_housing.py — eLo robot neck: magnetic ball-and-socket joint housing
Spec: SPEC_physical_elo_hand_body_2026-08-30.md / PE-037 (David L3 2026-08-30)

Coordinate convention:
  Origin: centre of ball sphere
  XY: ball equatorial plane
  +Z: up (toward eLo head)
"""
from build123d import *
import math

# ── Parameters ────────────────────────────────────────────────────────────────
BALL_D            = 25.0   # ball diameter
SOCKET_ID         = 26.0   # socket inner diameter (1mm clearance each side)
SOCKET_WALL       = 5.0    # socket body wall thickness
SOCKET_CAPTURE    = 270.0  # arc of capture (degrees)
CLEARANCE_GAP     = 3.0    # gap between ball top and housing rim

WIRE_D            = 5.0    # wire routing channel diameter (2 channels)

FLANGE_D          = 40.0   # base flange outer diameter
FLANGE_T          = 6.0    # flange thickness
BOLT_CIRCLE_D     = 30.0   # M3 bolt circle diameter
M3_CLEAR_D        = 3.4    # M3 clearance hole diameter
N_BOLTS           = 4

# Derived
ball_r        = BALL_D / 2
socket_r      = SOCKET_ID / 2
socket_od     = SOCKET_ID + 2 * SOCKET_WALL

# Socket body extends down below the ball equator to give 270° capture.
# 270° arc → the cup opens 45° above equator (90° removed from 360°).
# Opening half-angle from +Z axis = (360 - 270) / 2 = 45°
# Socket body height = ball_r + ball_r * cos(45°) ≈ ball_r + ball_r * 0.707
opening_half_deg  = (360.0 - SOCKET_CAPTURE) / 2.0
opening_half_rad  = math.radians(opening_half_deg)
socket_depth_from_ball_centre = ball_r + ball_r * math.cos(opening_half_rad)


def gen_step():
    # Ball is positioned with its centre at origin.
    # Socket body sits below (–Z), base flange at the bottom.

    # ── 1. Ball ───────────────────────────────────────────────────────────────
    ball = Sphere(ball_r)

    # ── 2. Socket body ────────────────────────────────────────────────────────
    # Outer cylinder of socket
    socket_total_h = socket_depth_from_ball_centre + FLANGE_T
    socket_outer = Cylinder(socket_od / 2, socket_total_h,
                             align=(Align.CENTER, Align.CENTER, Align.MIN))
    socket_outer = socket_outer.moved(Location((0, 0, -socket_depth_from_ball_centre)))

    # Inner hemisphere cut — removes material to form the cup
    # Hemispherical cut centred at origin (ball centre)
    inner_hemi = Sphere(socket_r)
    # Keep only the bottom half that is within the socket body
    inner_cut = Cylinder(socket_r, socket_depth_from_ball_centre + 1,
                          align=(Align.CENTER, Align.CENTER, Align.MAX))
    inner_cut = inner_cut.moved(Location((0, 0, 0)))
    inner_cup = inner_hemi & inner_cut  # hemisphere below equator

    socket_body = socket_outer - inner_cup

    # Opening slot at top of socket (45° chamfer to allow ball entry)
    # Remove a cone frustum above the capture arc to give the opening
    opening_r = ball_r + 1.0  # slightly wider than ball
    cone_h = ball_r * math.sin(opening_half_rad) + 2.0
    opening_cone = Cone(opening_r, socket_r - 0.5, cone_h,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))
    opening_cone = opening_cone.moved(Location((0, 0, -cone_h + 0.5)))
    socket_body = socket_body - opening_cone

    # ── 3. Base flange ────────────────────────────────────────────────────────
    flange_z = -(socket_depth_from_ball_centre + FLANGE_T)
    flange = Cylinder(FLANGE_D / 2, FLANGE_T,
                       align=(Align.CENTER, Align.CENTER, Align.MIN))
    flange = flange.moved(Location((0, 0, flange_z)))
    socket_body = socket_body + flange

    # ── 4. M3 bolt holes through flange ───────────────────────────────────────
    bolt_r = BOLT_CIRCLE_D / 2
    for i in range(N_BOLTS):
        angle = math.radians(i * 360.0 / N_BOLTS)
        bx = bolt_r * math.cos(angle)
        by = bolt_r * math.sin(angle)
        bolt = Cylinder(M3_CLEAR_D / 2, FLANGE_T + 2,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))
        bolt = bolt.moved(Location((bx, by, flange_z - 1)))
        socket_body = socket_body - bolt

    # ── 5. Wire routing channels through socket base ─────────────────────────
    # Two 5mm channels symmetrically placed along X axis, through socket wall
    for x_offset in (-SOCKET_WALL, SOCKET_WALL):
        wire = Cylinder(WIRE_D / 2, socket_depth_from_ball_centre + FLANGE_T + 2,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))
        wire = wire.moved(Location((x_offset, 0, -(socket_depth_from_ball_centre + FLANGE_T + 1))))
        socket_body = socket_body - wire

    # ── 6. Return compound: ball (reference) + socket housing ─────────────────
    # Ball is a reference geometry only (the actual magnet ball is purchased)
    ball.label = "neck_ball_reference"
    socket_body.label = "neck_socket_housing"
    housing = Compound(children=[ball, socket_body])

    return housing


if __name__ == "__main__":
    from build123d import export_stl
    shape = gen_step()
    export_stl(shape, "elo_neck_magnetic_housing.stl")
    print("Generated: elo_neck_magnetic_housing.stl")
