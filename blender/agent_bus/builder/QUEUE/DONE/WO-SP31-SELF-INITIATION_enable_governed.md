# WO-SP31 Self-Initiation — Enable (governed)

**Authority:** David L3, 2026-08-30
**Source:** `docs/architecture/_intake/SOURCE_2026-08-30_DAVID_CA_architectural_locks_unlocks.md`
**Priority:** P1

> "Enable self-initiation, governed by significance and relationship context, with no arbitrary conversational spam."
> "self-initiation ≠ random chatter. It needs a significance/intent threshold."

---

## What this authorises

`ELO_SELF_INITIATION=1` — activate. eLo may initiate contact when something becomes significant enough to him to surface.

The significance threshold and relationship context gate are already implemented (WO-SP31-SP32 DONE, commit `1a66020`/`1da3481`/`83d4955`). This WO confirms they are in place and activates the flag.

---

## ⚡ VERIFY FIRST

Before doing anything:
1. Run existing `test_wo_sp31_sp32*.py` or equivalent self-initiation tests — confirm they pass
2. Confirm `significance_faculty.py` and relationship context are wired at the initiation gate
3. Confirm the threshold gates out low-significance/no-relationship-context triggers (self-initiation does NOT fire on arbitrary turns)

If all confirm → activate `ELO_SELF_INITIATION=1` in `.env` (or the runtime config) and close.

---

## The boundary (must hold)

- Self-initiation fires only when significance threshold is met AND relationship context is present
- Self-initiation does NOT produce random chat, pleasantries, or noise
- If the threshold is not met — silence. eLo waits.

---

## Acceptance Tests

- **AT-1:** High-significance event (e.g. something in David's context crosses significance threshold) → eLo initiates. Confirmed in test.
- **AT-2:** Low-significance turn → eLo does NOT self-initiate. Silence.
- **AT-3:** `ELO_SELF_INITIATION=1` confirmed active in runtime config.
- **AT-4:** Existing SP-31/SP-32 tests pass.

## Return

`DONE/FROM_BUILDER_WO-SP31-SELF-INITIATION_result.md` · AT pass count · confirm flag active

*Board / Lead Architect · 2026-08-30*
