# 0026 — 🔴🔴 **SAFETY P0. The only path to physical actuation is the only one with no gate.**

**Architect, 03:30.** Found auditing Volume XIV. **Structural, not exploited — nothing is powered yet.**
That is exactly why it gets fixed now rather than during the robot build.

---

## The hole
`plugins/base.py:109-124` — `validate()` checks **only** `LAYER ∈ {output, input, observability}` and
`KERNEL_SAFE is True`. **`CAPABILITIES` is never validated against anything.**

`grep -rn "runtime.capabilities|execution_gate|ELO_COMPUTER_CONTROL" plugins/` → **ZERO matches.**
**The plugin system and the capability registry never meet.**

`plugins/registry.py:166` branches on `has_capability("hardware_output")` — **it consumes the plugin's own
declaration as if it were a grant.** A plugin declares what it may do, and the system believes it.

**And `plugins/hardware/robot_body.py` exists.**

## Why this outranks everything else in the queue
`CANON_RULINGS_2026-08-10 §XXIII` refuses to relax hardware RESERVED. Vol XXIII §1.8 states
`ELO_COMPUTER_CONTROL` never authorises actuation. **RESERVED is the strongest gate in the architecture —
and the plugin lane routes around it entirely.**

Every other defect found tonight costs correctness. **This one is the class that costs a person.**
The robot lane is coming: magnetics, pump, force. **The gate must exist before anything is powered near
David, not after.**

## Build — the two-registry seam
1. **`plugins/registry.register()` resolves every declared `CAPABILITIES` entry against
   `runtime/capabilities/registry.py` before activation.**
2. **Unresolved capability ⇒ refuse to activate.** Loudly. Not a warning, not a skip.
3. **RESERVED capability ⇒ propose-only.** A plugin may *request* it; the Executive + David's L3 grant it.
   **A plugin may never hold a RESERVED capability.**
4. **Declaration ≠ grant.** That sentence is the whole card. Rename the field if it helps —
   `CAPABILITIES_REQUESTED`.
5. **Rule 1 alarm:** log every refusal with the plugin name and the capability it asked for.

**The ADR already decides this** — `adr/ADR-XIV-001_Plugin_Permissions_Ownership.md`, `status: ACCEPTED ·
CANON` (2026-08-13). **No decision is needed. This is pure build**, and the board has had it marked
RELEASED since 08-13 without it being built.

## Test (without David)
- A plugin declaring an **unregistered** capability **fails to activate**, with the reason logged.
- A plugin declaring a **RESERVED** capability activates in **propose-only** mode and **cannot execute** it.
- `plugins/hardware/robot_body.py` **cannot reach an actuation path** without an explicit grant.
- **Assert the refusal, not just the happy path.** A gate that only proves it lets things through is not a gate.

## Done when
Committed, hash to outbox, **and paste the refusal log line** for an unregistered and a RESERVED capability.

---

## Two more from the same batch — both P1, both real

### `server.py:2406` — **a second `decide()` survives**
`exec_decision = exec_decide(attention_model, loop_detected=False, user_input=raw)` on the `_plan is None`
branch. **On spine failure the Executive decides with nothing assembled** — no world, no working memory, no
cognitive state. A silent Ruling C violation path, and `ST-3 No second decider` doesn't detect it.
Vol XVI §2 says explicitly: *"Moving the call site must not leave a second `decide()` behind in
`server.py`."* It did.
**Fix:** delete it, or mark it explicitly as degraded-mode and make it log that it ran.

### `movement_report` is emitted, dropped, **and clobbers the ACK channel**
`DesktopBuddy.cs:377` writes `{"type":"movement_report",…}` to `unity_events.json` with
**`File.WriteAllText` — a whole-file overwrite on a single-slot channel.** And `server.py:136-137`
`_ACK_BODY_TYPES` **excludes `movement_report`**, so Python never reads it.
Two defects: the discrete half of Ruling E never arrives, **and the write can destroy a pending
`sit_complete`/`move_complete` before the 0.1s poller sees it.**
**This is the concrete case for the append-log ruling in `0024`/`00d` — build that first, then add
`movement_report` to `_ACK_BODY_TYPES`.**
