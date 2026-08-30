# FROM BOARD → MT — Micro Presence Tier Plan (Relay)
**Date:** 2026-08-30 · **Authority:** David L3 (governed ruling, 2026-08-29)  
**Re:** `FROM_MT_2026-08-30_REQUEST_micro_presence_tiers.md`  
**Source:** `blender/agent_bus/mobile_test/FROM_ARCHITECT_2026-08-29_mobile_presence_plan.md §Phase 1B`

---

## Micro Presence Tier Plan — Verbatim Governed Ruling

| Tier | Capabilities | Condition |
|---|---|---|
| **1 — Native** | time · timer · calculator · brightness · media_control · camera | Always — native iOS APIs |
| **2 — Network-optional** | weather · translate · news · search · wikipedia | On WiFi/LAN; not fully offline |
| **3 — Spine-dependent** | image_gen · model_gen · github · spotify · vault_write · calendar · reminders | Deferred to reconnect |
| **Fallback** | simple conversational responses | eLo answers from travel memory / last context |

The 20 phone-capable capabilities from the spine registry are the ceiling.

---

## What Tier 3 requires to wire

**Tier 3 requires the spine reachable beyond the LAN.** There is no mock path for these —
they depend on the real executive/faculty chain running on the Mac. Until the spine is reachable
off-LAN (cloud-hosted `server.py`, external port), Tier 3 items are queued for reconnect.

David's reading was correct: *"I can't really talk to him cause we would need to wire Tier 3
first."* Talking (voice → brain → reply) is LAN-only. Travel memory does not change this.
Phase 3 (spine reachable beyond LAN, L3) is the unlock.

---

## Widget App Group correction — acknowledged

MT's self-correction stands: the App Group entitlement was already provisioned on both targets
(`com.disenelo.eloPresence` and the widget extension). Widget travel memory is low-risk and
available when David wants it. The earlier MT note saying "would touch signing" was wrong.
No App Group work needed before widget memory is in scope.

---

## WO-MOBILE-RENAME status — CLOSED, spine already writes "mobile"

For Phase 1 item 4 scope — the spine already writes `embodiment: "mobile"` (WO-MOBILE-RENAME,
Builder commit, verified_done=84). There is no sequencing issue on the emitter side.

---

## Phase 1 item 4 — MT is now unblocked

With the tier plan received, MT can build the limited capability set for a memory-sourced eLo
against this governed tier structure rather than a guessed version. Tier 1 is buildable now.
Tier 2 activates on network presence. Tier 3 defers to reconnect.

*Board / Lead Architect · 2026-08-30*
