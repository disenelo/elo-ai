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

---

## DONE — 2026-08-19 (bookkeeping stamp; build shipped 2026-08-13)

**Build commit: `a69cd9b`** — "WO-108: directed LOOK produces ObservationRecord; head rotation is not a LOOK."

- **CANON:** this file.
- **IMPLEMENTED:** `runtime/directed_look.py:150` — `look(target) → ObservationRecord`.
  Chain complete: INTENT (call) → ATTENTION TARGET (arg) → PERCEPTION (`_perceive_target`) → OBSERVATION (record) → SELF/WORLD UPDATE (persisted via `_persist`, exposed via `last_observation`).
- **LIVE WIRE:** `server.py:3670-3685` — each conversational turn, if gaze is on a window, `look(gaze.window)` runs and the record persists.
- **EXECUTIVE-VISIBLE:** `runtime/the_moment.py:165,233` — `compile()` includes `last_observation`.
- **PROVEN:** `tests/test_wo108_directed_look.py` — AT-108-1..6 all green. Every test resolves against `runtime.directed_look` — deleting the module fails every one.
- **RUNTIME ARTEFACT:** `self/journals/observation_log.jsonl` — 90 records total, 78 `outcome=observed` (real gaze-on-window turns), plus absent-case records from the tests.

**Real observation (record 87):** `{"target":"Visual Studio Code","outcome":"observed","source":"spatial","confidence":0.9,"observed_at":{"window":"Visual Studio Code","edge":"bottom","on_window":true}}`.
**Failure case (in-memory, verified in AT-108-2):** `look("totally_impossible_app_not_on_screen_xyz_abc_123") → outcome=absent, confidence=0.0` — record exists, but says he couldn't see it. `observation_for()` returns `None` when no record → Verified-Speech gate holds.

Card was still in QUEUE because the bookkeeping was never done, not because the code was missing. This stamp closes that gap.
