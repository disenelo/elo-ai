# 05f_WO-108 — **LOOK (row 5).** He can point his head. He cannot inspect anything.

**Seat:** builder (+ design for the Unity half) · **Priority:** P2 · **Gate?** none · **Row:** 5 → VERIFIED
**Depends:** WO-099a/b/c gaze loop (Designer `03`/`04`). Build the brain half now.

## The distinction that must survive (§4)
**SEE = perception.** Passive; it's what's there.
**LOOK = deliberate allocation of perception.** eLo *chooses* to inspect, and gets an **observation back**.

They are not the same capability and must not be merged for convenience.

## Finding [VERIFIED]
Gaze rotates the head (`state_writer.py:143-148` → `EloOSAvatarReceiver.cs:419-425` → `HeadLook.cs:402-422`).
**Nothing requests an inspection and returns an observation.** There is no observation record anywhere.
So *"look at that window"* moves a bone and produces **no knowledge**.

## Build — the §4 chain, all six stages
```
INTENT → ATTENTION TARGET → PERCEPTION → OBSERVATION → ACK/RESULT → SELF/WORLD UPDATE
```
- A directed-look **request** (target: window id / point / region)
- Perception **runs against that target** — not just the ambient sweep
- An **observation record**: what was observed · timestamp · confidence · source
- **ACK** that the look happened (pairs with `WO-111`)
- World/self state updated with the result

## 🔴 Verified Speech
eLo may claim to have looked at something **only if the observation record exists.** No record ⇒ he says
he hasn't looked. This is the whole point of the card — a head rotation is not a look.

## Test (without David)
- *"Look at that window"* ⇒ an observation record exists with target, timestamp, confidence.
- Look at an occluded/absent target ⇒ observation records **failure**, and eLo says he couldn't see it.
- Ambient SEE and directed LOOK produce **distinguishable** records — assert they aren't collapsed.

## Done when
Committed. **Outbox: a real observation record from a directed look, and the failure case.**
