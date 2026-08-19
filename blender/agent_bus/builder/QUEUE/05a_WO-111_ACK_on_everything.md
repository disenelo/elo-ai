# 05a_WO-111 — **VERIFY (row 13).** ACK exists for 3 actions. Everything else lies.

**Seat:** builder · **Priority:** P1 — **largest single unlock after the seam** · **Gate?** none
**Row it moves:** 13 VERIFY → VERIFIED. **Unblocks:** every row that depends on knowing an action happened.

## What exists [VERIFIED]
| Action | ACK | Where |
|---|---|---|
| sit | ✅ | `server.py:2620-2693` ↔ `EloOSAvatarReceiver.cs:661` |
| move | ✅ | `server.py:2729-2760` ↔ `.cs:690` |
| exit | ✅ | `server.py:2799-2832` ↔ `.cs:714` |
| **anim triggers** | ❌ | `blender_bridge/anim_trigger.py:34` returns `True` **on file write** — not on the animation happening |
| **scale** | ❌ | `server.py:1621-1638` |
| **spawn_wave** | ❌ | `server.py:1641-1649` |
| **image_gen** | ❌ | `server.py:1799` |
| **computer_control** | ❌ | `server.py:1558` |
| **every `_AGENTS` tool** | ❌ | `tools/tool_router.py:827` |

**So eLo claims success for almost everything he does, with no signal that it happened.** That is a direct
ADR-Exec-001 Verified Speech breach on every non-movement action.

## Build
1. **One generic contract:** `action_id → executor → ACK{ok, detail, ts}`. Every capability in the registry
   must satisfy it — no per-verb hand-wiring like the three above.
2. **`anim_trigger.py:34` must stop returning True on file write.** Return the real completion, or return
   "unconfirmed" — never a success that means "I wrote a file."
3. **No ACK ⇒ eLo may not claim it happened.** Route through the honesty layer: unconfirmed action ⇒ he
   says it's unconfirmed.
4. **Timeouts are outcomes.** No ACK within N seconds = a reported failure, not silence.

## Test (without David)
- Executor silently fails ⇒ **eLo says it didn't work.** (Break one deliberately and assert the wording.)
- Every registry capability has an ACK path — a test that **fails when a new capability is added without
  one**. That assertion is the point of this card.
- Timeout produces a reported failure.

## Done when
Committed. **Outbox: which actions now ACK, and the sentence eLo produces when one fails.**
