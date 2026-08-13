---
source: David Charles (primary)
captured: 2026-08-13
capture_rule: CLAUDE.md Rule 4b — VERBATIM, do not summarise
topic: Robot physical build — 3D render joints · Japanese sphere joint system · servos ↔ Raspberry Pi · battery · shoulder pistons
lane: ROBOT HARDWARE — RESERVED. Keeps LG-2 per David's ruling 2026-08-10 (force · magnetics · pump · thermal · battery · pinch points)
routes_to: RD-CAD · RD-4 (inflated-TPU) · WO-084 (eLo puppet joint library) · Vol XI Motor Cortex · LG-2 safety scope
---

# VERBATIM — primary source, do not summarise. David's exact words, 2026-08-13.

Okay sounds like you got some things to finish, I have started the robot modelling and started to create
joints, for a 3D Render, I will next need to figure out how to make a Japanese Sphere Joint System and Servo
motors that will be able to communicate back to a rasberry pi and have a battery -- and also control small
pistons for shoulders

---
**David, follow-up (same session, 2026-08-13) — VERBATIM:**

And for the hands we will be using a 3 Finger Anthropomorphic Robotic Finger setup

---
**David, follow-up #2 (same session, 2026-08-13) — VERBATIM:**

I can make most of the design in Blender, so a lot of this will move faster, I just need more specifics hand
type, japanese joints, and servo and raspberry pi and how much batter would be need to move a set amount of
joints, and also there is a counter weight swing in the base I will use like a tail counter balance inside

---

## Architect note — this crosses into the RESERVED hardware lane
Per David's own ruling (`CANON_RULINGS_2026-08-10.md`, Ruling XXIII): **software RESERVED collapsed to David
alone, but ROBOT HARDWARE keeps LG-2** — a real, separate second review for **force · magnetics · pump ·
thermal · battery · pinch points**, and **LG-2 must not be the person who designed the part**.
**Servos + battery + pistons are all inside that scope.** The force-limiter / soft-stop scope (LG-2 WO)
**does not yet exist in `avatar/safety_controller.py`** and must be closed before anything is powered near him.
