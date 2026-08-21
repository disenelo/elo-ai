# 0081 — `WO-CANON-XI` §A/§D — David ruled `OQ-1.2`. Go.

**Seat:** builder (+ Design for the Unity half) · **Priority:** P1 · **STATE: 🟢 L3 RULED**

> **David 2026-08-21: "Okay that's fine just go"**

**Approved:** add `route` + `issued_by` to `move_command`. Additive, backwards compatible. **The DOWN
contract is amended by the person who signed it.**

## Sequencing — the spec's own, and it is not optional
`Volume_XI/01:390`: *"ship the field, prove parity, **then** remove Unity's local route selection."*
**"Just go" = do all three without pausing between them. It is not permission to skip step 2.**

1. **Ship** `route` + `issued_by` on `move_command`. Nothing else changes; Unity still picks its own path.
2. **Prove parity** — the brain's chosen route matches what Unity would have chosen, across real moves.
   **Log both, compare, report the match rate.**
3. **Only then** remove Unity's local route selection.

🔴 **If parity fails at step 2, STOP AND REPORT. Do not remove Unity's selection.** A brain that routes worse
than the body it replaced is a regression David will see as eLo moving wrong.

## Also in XI, and already recommended — take them
- **`OQ-1.3` timeouts:** derived from the route's `expected_ms` sum plus slack, **not fixed.** Spec's
  recommendation; a three-leg route legitimately takes longer than a sit.
- **`OQ-1.4` ACKs:** **both** — per-leg `move_complete{leg:n}` for verification and learning granularity,
  plus a terminal `arrived` the Executive gates speech on. Pairs with `Vol XIII OQ-2.3`.
- **`OQ-1.1`:** recognise `blender/elo_spatial.json` **as** the IO contract's third channel rather than
  adding `unity_state.json`. *"Undocumented channels are the exact drift class the contract exists to
  prevent."* Needs both seats' sign-off — Builder and Design, not David.

## Wiring
- **Caller:** what emits `move_command` with a route
- **Trigger:** a real move on the live desktop
- **Observable:** eLo takes the brain's path, and the route is visible in the trace

## Test
1. `move_command` carries `route` + `issued_by`; old consumers unaffected (backwards-compat assert).
2. **Parity: brain route vs Unity route across N real moves — report the match rate.** RED if unproven.
3. Per-leg ACK + terminal `arrived`; Executive gates speech on `arrived`.
4. Remove the route field → parity test goes RED.

## Result
- commit: `2c9eefc` · parity match rate: 🔴 UNPROVEN (22 pre-route entries, 0 with brain_route/unity_route) · Unity local selection removed: ❌ BLOCKED (parity gate open) · OQ-1.3 caller: `server.py` `_PENDING_MOVE` + move activation block · OQ-1.4 caller: `server.py` move ACK check (`arrived` + `move_complete`)
- Tests: `tests/test_canon_xi_a_d_route.py` — 3/4 PASS, XI-AD-2 🔴 RED (correct — parity gate, not a failure)
- Next: run live moves that emit `brain_route` + `unity_route` to `route_memory.jsonl`; XI-AD-2 turns GREEN when match rate ≥ 80%
