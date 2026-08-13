# WO-063 — A Command Wakes The Body (dormant / steered / off-window → always execute)

**Owner:** Designer (Unity C# — DesktopBuddy) · with Builder confirm on the command envelope
**Priority:** P2 — robustness. **Sequence:** AFTER Presentable v1 (does NOT block the finish line).
**Status:** QUEUED
**Canon:** One-Brain — *autonomous and commanded are ONE capability, never divergent.* A command is the
brain driving the body; it must ALWAYS execute. ADR-Exec-001 (Verified Speech) already holds via the
honesty guard — this WO adds the *action* half without breaking that guard.

## Origin
Designer FLAG (outbox 2026-08-06, SEAT-ENG-004), reconciled to the board. The MoveAckCo honesty guard
correctly stays SILENT when a commanded move silently no-ops — but the underlying gap is that the command
never actually ran. Root: a commanded move is a no-op while eLo is autonomously **dormant** (drop-off /
`RoamUpdate` early-returns), **steered**, or **off every window** (`WindowRoamStep` gated by `!steered` +
sensor ready + `wins>0`). The Designer prototyped `ExecuteNav {steered=false; if(_exitDormant)
WakeFromExit();}` but **REVERTED it** — unverified (test env had `wins=0`, so no surface to move to) and
shipping unverified speculative movement code late is against discipline. This WO does it properly, verified.

> **Real-usage note (keep scope honest):** when David commands, he is PRESENT, so eLo is not
> userAway-dormant — this gap mostly bites automated / no-presence testing. That is exactly why it is
> P2 / post-Presentable, not a finish-line blocker. But One-Brain wants it closed: a command should pull
> him into action regardless of what he was doing autonomously.

## Scope — a command PULLS eLo into action
On any commanded move/sit (brain → `move_command` / `sit_command`), before dispatch:
1. **Wake from dormancy** — if `_exitDormant` / dropped-off, `WakeFromExit()` (or equivalent) so the roam
   loop resumes and can consume the command.
2. **Clear the autonomous steer** — `steered = false` so `WindowRoamStep` is no longer gated off.
3. **Re-attach to a surface** — if off every window, attach to a valid target (nearest window / last
   surface) so there IS somewhere to execute; if genuinely none exists, fall through to the honesty guard
   (no false ACK — that behaviour is CORRECT and must be preserved).
4. Then dispatch through the SAME autonomous resolver (target + style flag) — no parallel driver.

## Guard rails (do not regress)
- The MoveAckCo honesty guard STAYS: ACK only when a REAL move got set up (`NavMoved`). Waking the body
  must not manufacture a fake `NavMoved`. If, after wake+un-steer+re-attach, there is still no reachable
  surface, eLo stays silent (no false ACK) — verified as PASS, not a regression.
- No new state machine; reuse `HandleNav` / `WindowRoamStep` / the existing dormancy + steer flags.

## Definition of Done — VERIFIED WITHOUT DAVID (the Designer's blocker was untestability)
Build a **windowed test env** (≥1 window surface present, `EloWindowSensor ready=True`, `wins>0`) so the
happy path is actually exercisable — this is the piece that was missing at revert time. Then:
- **Dormant + command:** eLo dropped-off / `_exitDormant` → send `move_command` → wakes, executes, emits
  `move_complete{move}`. LOG the wake transition.
- **Steered + command:** autonomous steer active → command clears it → executes → `move_complete`.
- **Off-window + command, surface available:** re-attaches → executes → `move_complete`.
- **Off-window + command, NO surface anywhere:** stays silent → NO `move_complete` (honesty guard intact).
- **Sit parity:** a commanded sit while dormant wakes + sits + HOLDS (ties WO-040 hold + the `sit_held`
  heartbeat from the sit-hold instrumentation WO).
- All the above as inject/log-verified runs the Designer runs itself (no David); report artifacts to outbox.

## Out of scope
Any change to the honesty-guard ACK logic; any new expression/emotion path; RESERVED (none here).

Refs: `../../blender/agent_bus/design/outbox.json` (the flag) · `MOVESET_SELFMODEL_SPEC_draft.md`
(Capability↔Embodiment §3 — commanded reuses the autonomous resolver) · WO-060 (free-form sub-types) ·
WO-040 (sit hold).
