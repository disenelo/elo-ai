# 00 — ⚡ **ROW 13 VERIFY: the Unity half of ACK. This is yours, and it was wrongly all on Builder.**

**Seat:** design · **Priority:** **P1 — take ahead of your queue** · **Gate?** none
**Row:** 13 VERIFY · **unblocks:** every row that depends on knowing an action actually happened.

## Why you're getting this
24 of the 26 capability rows were assigned to Builder. Several have a **Unity half** that only you can
build, and holding them in one lane is why the matrix moves slowly. **Row 13 is the clearest case.**

## The finding [VERIFIED 2026-08-13]
ACK exists for **exactly three actions**, all yours on the Unity side and already correct:
- sit — `EloOSAvatarReceiver.cs:661` · move — `:690` · exit — `:714` (+ `sit_held`/`sit_ended` heartbeats)

**Everything else claims success with no signal.** The worst case is on the brain side but the fix is
yours: `blender_bridge/anim_trigger.py:34` **returns `True` on a file write** — the Python side treats
"I wrote the command" as "the animation happened." **Nothing in Unity tells it otherwise.**

So when eLo says *"I waved"*, he is reporting that a file was written. That is an ADR-Exec-001 Verified
Speech breach on every animation and gesture.

## Build — the Unity side of a generic ACK
Builder is building the contract `action_id → executor → ACK{ok, detail, ts}` (`builder/QUEUE/05a`).
**Your half: emit the ACK from Unity when the thing actually happens.**

1. **Every anim trigger / gesture ACKs on completion**, not on receipt. Use the same shape you already use
   for `move_complete` — `WriteUnityEvent("<action>_complete", "<action>", detail)`.
2. **Include the `action_id`** Builder sends down, so the ACK can be matched to the request. Agree the
   field name with them in the outbox — **one exchange, then build.**
3. **Failures ACK too.** Animation missing, clip not found, blocked by state ⇒ `ok:false` with the reason.
   **An ACK that only fires on success is worse than none** — it makes failure invisible.
4. Same for **scale** and **spawn_wave** if they're driven your side.

## Also yours — row 3 BODY
`server.py:3088` currently writes `embodiment="desktop"` as a **hardcoded string**. It should reflect the
real active body. **If Unity is the authority on which body is live, emit it** — a top-level `embodiment`
field on `elo_spatial.json` beside the ones you added at 19:30. One line, and it kills a hardcoded
constant that's pretending to be state.

## Test (without David)
- Trigger a gesture ⇒ ACK arrives on completion, matched by `action_id`.
- Trigger a gesture that **can't play** ⇒ ACK arrives with `ok:false` and a reason.
- Kill the animator mid-action ⇒ **failure is reported**, not silence.

## Done when
Committed, hash to outbox, **and tell Builder the ACK field names** so their contract matches yours.
**Then take `01` One Brain.**
