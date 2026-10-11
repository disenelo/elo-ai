# WO-SEAM-A — Executive intent→action minimum repair
## FREEZE_V1_LOCK LIFTED FOR THIS WO ONLY

**Authority:** David L3, 2026-08-30
**Source:** `docs/architecture/_intake/SOURCE_2026-08-30_DAVID_CA_architectural_locks_unlocks.md`
**Full WO:** `engineering/work_orders/WO-020_Kernel_Routing_Drift.md` (Seam A section)
**Priority:** P0

> "LIFT FREEZE_V1_LOCK for the minimum work required to bring Executive behaviour into alignment with the canonical execution flow. Not redesign the Executive. Not reopen the whole brain. Fix the seam."

---

## Scope — minimum repair only

**`executive.py` MAY be modified for this WO only.** Scope is strictly:
- Tighten the priority ladder in `_conversation_action()` so plain commands and direct questions route to ANSWER / capability-execute
- CONNECT / REFLECT / WITNESS branches must only fire on genuinely reflective or associative input — raise their thresholds, require stronger signals
- A plain imperative ("open X", "tell me Y", "do Z") must NEVER land in CONNECT/REFLECT/WITNESS

**Do NOT:**
- Redesign the executive kernel
- Change the cognitive spine (faculties, perception, significance)
- Touch the provider routing layer
- Alter the plan/capability structure
- Introduce new concepts not already in `_conversation_action()`

---

## Acceptance Tests

- **AT-1:** Plain command ("open Joe Budden Podcast on YouTube") → routes to ANSWER / capability-execute. Does NOT land in CONNECT/REFLECT/WITNESS.
- **AT-2:** Direct question ("tell me the weather") → routes to ANSWER. Not associative.
- **AT-3:** Repeated explicit request → executes, does not REFLECT on the request.
- **AT-4:** Genuinely reflective input ("that's an interesting tension, isn't it") → CONNECT/REFLECT allowed.
- **AT-5:** Seam B guard still active — "what is done?" does not web-search "done" (regression).
- **AT-6:** Frozen-kernel tests (test_wo001, test_wo006, test_wo014) still pass.
- **AT-7:** Routing trace `conversation_action` field confirms ANSWER for AT-1/AT-2 inputs.

---

## Constraint

This is the ONLY active FREEZE_V1_LOCK lift. Once this WO closes, `executive.py` returns to FREEZE_V1_LOCK unless David issues a new lift.

## Return

`DONE/FROM_BUILDER_WO-SEAM-A_executive_minimum_repair_result.md` · AT pass count · commit hash · routing trace sample confirming ANSWER routing

*Board / Lead Architect · 2026-08-30*
