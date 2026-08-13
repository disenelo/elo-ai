# PAIRED BRIEF — The Sit Chain = the first vertical slice of SITUATED SELF
### For BOTH seats: Builder (eLo OS) + Designer (UI/Avatar). Run this together.

**Why this brief exists (Chief Architect diagnosis, David L3 2026-08-05):** the sit gap is a *symptom*.
The cause is that eLo has no verified runtime SELF — so the Executive generates a plausible sentence and
*hopes* the body follows. The fix is the loop below. We build it once, for ONE capability (sit), and it
becomes the template for every action. Canon: ADR-Exec-003 (Embodied Truth) + **ADR-Exec-004 (Situated
Self, new invariant #5)**.

## The loop (this is the whole point — not just "make sit work")
```
User: "sit with me"
   → Executive reads SELF (Situated Self): pose=standing · location · available_actions⊇sit · locomotion faculty=OK
   → plan: (here or nearest perch) → sit
   → faculties execute: Builder emits sit_command
   → Unity plays + HOLDS the sit (Designer _sitHeld)
   → Unity ACKs sit_complete
   → Executive UPDATES self: pose=sitting, surface=<window>
   → ONLY NOW speak: "I'm sitting with you."   (impossible to say unless it's true)
```

## BUILDER (eLo OS)
- **WO-035** — semantic sit intent (done): emit `sit_command` with target. Keep.
- **WO-041** — `_PENDING_SIT` set on the sit intent; the Executive must NOT say "sitting" until the
  `sit_complete` ACK arrives (NOT on request/emit). On no-ACK timeout → honest "I tried to sit but
  couldn't reach my body" (ADR-Exec-001) — never a false claim.
- **Situated Self hook (the new part):** on the sit turn, READ the self-model (pose · available_actions ·
  locomotion faculty health) BEFORE planning; after the ACK, WRITE back `pose=sitting`, `surface`. For
  THIS slice add only those fields to the EXISTING `self/elo_self_state.json` — do NOT build the whole
  Moment yet (that's WO-052) and do NOT create a new self_state file (Check-Before-Build).

## DESIGNER (UI/Avatar)
- **WO-040** — `_sitHeld` guard: play the sit AT eLo's current location, HELD, so the idle rotation can't
  override it. Reliable minimum = sit-in-place; do NOT gate on walk-to-cursor.
- **WO-041** — emit `sit_complete` ACK back (via `blender_state.json` / event) the moment the sit pose is
  actually playing + held. **This ACK is the signal the Builder waits on — it is what closes the loop.**

## Arbiter (unchanged)
`blender_state.json`: `sit_command` written but avatar not sitting → Designer's. Not written → Builder's.

## Acceptance (David L3)
Say **"come sit"** → eLo reads its self → plays + holds the sit at its location → ACKs → updates its pose
→ *then* says it's sitting. One capability, the whole loop, verifiably true.

## Guardrails
Check-Before-Build: extend the EXISTING sit path + the EXISTING self-model. No parallel sit driver, no
new self_state file. This slice is the seed of The Moment (WO-052) / Situated Self — build it so WO-052
extends it, not replaces it.
