# ▶ DESIGNER — START HERE (2026-08-10, current). First START_HERE for this seat.

**Self-serve from here. Do ONE WO per run, in lane (DesktopBuddy Unity C# only), ship with an inject/log
test you run yourself, write your outbox, then take the next. David runs no commands — his only check is the
visual/feel L3. Append to your outbox, don't overwrite (outbox protocol).**

## YOUR QUEUE — top to bottom
1. **WO-087 — FULL local-driver audit (DO FIRST — READ-ONLY, NO greenlight needed).** Sweep every DesktopBuddy
   component that touches behaviour and classify it: ROUTE-THROUGH-BRAIN / KEEP-AS-REFLEX / COMPLIANT /
   NEEDS-REVIEW. Deliver as an appended outbox relay. This is unblocked right now — it doesn't change behaviour
   or touch the sensitive avatar file, so you can run it immediately. Spec:
   `FROM_ARCHITECT_2026-08-10_WO-087_full_audit.md`.
2. **WO-074 C + F — movement-feel bugs** David keeps hitting: (C) eLo roams to the screen EDGE oddly; (F) he
   LEAPS too far instead of finding a route — should pathfind to the window, not jump. Also WO-074-A: the
   fire-jump GUN prop must be hidden on the desktop rig. Spec: `WO-074_Movement_Visual_Bugs_Live_Obs.md`.
3. **WO-075 — Desktop gravity / screen-wrap / landing.** Dropped eLo currently FLOATS where placed instead of
   falling to a surface — he must always land on a real platform (Embodied Truth). Spec:
   `WO-075_Desktop_Gravity_Screen_Wrap_Landing.md`.

## GATED — do NOT start until David greenlights (surfacing to him)
- **WO-086 steps 1-2** (mouse-idle → brain emit + retire the local calm driver). Touches the sensitive avatar
  file + changes autonomous behaviour → needs David's greenlight AND the Builder brain-decide half ready.
  Step 3 (audit) is already delivered. Your 4 asks are confirmed in `FROM_ARCHITECT_2026-08-10_WO-086_confirms.md`.

## FYI — not your build
- **WO-088 (walk-to-screen + teleport)** is diagnosed as an MCP-bridge artifact from Claude clients touching
  the live editor, fixed operationally (Architect stays off the live editor). Only optional, low-priority
  hardening remains (persist eLo's transform across domain reload) — ignore unless you have spare cycles.
  Spec: `FROM_ARCHITECT_2026-08-10_WO-088_screen_teleport.md`.
