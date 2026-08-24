# WO-SPG-001 — SPG Runtime Integration
**Status: 🔴 CANCELLED — SPG NOT ONBOARDED. David L3, 2026-08-22.**
**Authority:** `findings/SPG_BOARD_RECORD_2026-08-22.md` · `_intake/SOURCE_2026-08-22_DAVID_SPG_closed_not_onboarded.md`
**Do not build. No implementation follows from E-4. G-2/G-3/G-5 blocking.**
**Priority:** P1 (after WO-WKG-001..002)
**Source:** existing SPG architecture / contract on disk
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Date:** 2026-08-22

---

## Objective

Connect the already-defined SPG into the runtime as the persistent structured self-model. Do not create another self-model — wire the one that exists.

## What to wire

```
SPG
 ↓
persistent structured self-model
 ↓
EloSelfState  ←  current runtime state
 ↓
Executive (during assembly)
```

SPG = persistent, authoritative, evidence-backed self-state.
EloSelfState = runtime working state.
They are not merged. SPG informs EloSelfState; EloSelfState does not write back to SPG without going through the evolution path (WO-SPG-002).

Read the existing SPG contract before implementing — implement to it, not to this card.

## Acceptance

- SPG self-state reaches Executive during assembly as structured data
- EloSelfState is populated from SPG at session start
- EloSelfState changes do not automatically mutate SPG
- Existing SPG tests (if any) still pass
- No new self-model created alongside SPG

## Hard constraints — do NOT

- merge SPG and EloSelfState into one object
- move WKG world-knowledge into SPG
- create a third self-model
- redesign identity
- modify `canonical_identity.md`
