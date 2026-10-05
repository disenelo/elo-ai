# WO-041 Verify-Before-Speak — RESULT: ALREADY IMPLEMENTED
**Status:** Full verify-before-speak pipeline already in server.py. No code change needed.
**Date verified:** 2026-10-05

---

## Verified state (server.py lines ~4361–4465)

Full ACK-gated speech pipeline in place:
1. `_PENDING_SIT["active"]` tracker set when sit intent fires
2. `_ACK_QUEUE` polled for `sit_complete` events newer than sit issue time
3. On ACK: self-model updated, autobiography recorded, lesson recorded, `PENDING_SIT` cleared
4. In-transit (within 300s timeout): `[MOVEMENT IN TRANSIT — WO-041]` injected into g_ctx — eLo says "heading over", never "I'm sitting"
5. Timeout: `[SIT_FAILED — WO-041]` honest fallback — eLo says "I tried to come... couldn't reach"
6. ACK infrastructure: `_ACK_QUEUE_LOCK`, `_ACK_BODY_TYPES` including `sit_complete`, `move_complete`

## Acceptance (live server required)
Send move/sit intent → Unity fires `sit_complete` → eLo references sitting.
Without ACK: eLo says "heading over" / timeout → "something pulled me back".

Builder 1 · 2026-10-05
