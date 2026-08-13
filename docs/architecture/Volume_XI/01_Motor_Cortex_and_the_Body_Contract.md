---
chapter: 1
title: "The Motor Cortex & the Body Contract — Command Down, Confirmation Up"
volume: XI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  UNITY_ELOOS_IO_CONTRACT.md (David L3, 2026-08-06) · WO-035 (intent) · WO-040 (_sitHeld) · WO-041 (ACK) ·
  WO-054 (in-flight queue) · WO-063 (command while dormant) · WO-086 (loop pattern) ·
  _intake/SOURCE_2026-08-10_brain_body_brain_loop.md (VERBATIM) · live code (blender_bridge/state_writer.py, server.py, avatar/)
implementation: PARTIAL (channel + ACK loop LIVE for sit·move·leave·return; generalisation + route field PENDING)
audit_status: OPEN
dependencies:
  - Volume XIII (Presence & Embodied Spatial Intelligence — the sole legitimate source of movement intent)
  - Volume XVI (Coordination Under One Executive — one plan per turn)
  - Volume V/CONTRACTS.md (envelope, lifecycle, base contract)
  - ADR-Exec-001 (Verified Speech) · ADR-Exec-002 (Single Cognitive Truth) · ADR-Exec-003 (Embodied Truth)
---

# Chapter 1: The Motor Cortex & the Body Contract

## 1.0 Purpose

A decision that never reaches the body is a thought. A motion the brain never hears about is a rumour. This
chapter defines the two channels that turn one into the other, and the discipline that makes the round trip
*truth*.

> "brain > body > brain. A CLOSED LOOP: the brain decides + drives the body (DOWN), the body only SENSES and
> ACTS and reports its state back UP, and the brain reads that back and decides again. The body NEVER
> decides on its own."
> — David, `_intake/SOURCE_2026-08-10_brain_body_brain_loop.md` (VERBATIM primary source — read it)

The contract already exists and works (`UNITY_ELOOS_IO_CONTRACT.md`, David L3 2026-08-06; live for sit,
move, leave and return). What it never had was a canonical home, so each new action re-litigated it in a
WO. This chapter is that home.

**Why it exists at all,** stated by the contract itself: *"the sit loop broke because the Designer wrote the
ACK to `unity_events.json` while the Builder read `blender_state.json` — write-here / read-there. An ACK
eLo OS can't read and act on is pointless. This contract fixes the class of bug, not the one instance."*

## 1.1 Principle

**1.1.1 The Motor Cortex decides nothing.** It carries. Any logic in this layer that *chooses* between
actions has become a second brain and must be removed (§1.7).

**1.1.2 Channels are defined by DIRECTION and DELIVERY TYPE, never by topic.** Emotions, moods, states, new
actions are **fields inside an existing channel, never new files**. A new file is justified only by a new
direction or a genuinely different delivery type — and only by updating the IO contract, which both seats
sign. (David L3.)

**1.1.3 ACK before belief.** eLo believes he has acted only when his body confirms it. The order is
**Thought → Decision → Body → Confirmation → Belief → Speech** — never speak-then-hope-the-body-follows.
(Embodied Truth, ADR-Exec-003.)

**1.1.4 Commanded state owns the body.** While a command is in flight, no autonomous behaviour may overwrite
it. "Come sit" means he sits *and stays sitting* until something with equal or greater authority changes it
(WO-035 intent · WO-040 `_sitHeld` · WO-054 in-flight queue).

**1.1.5 Honest failure is a first-class outcome.** Timeout → *"I tried to X but couldn't."* Never silence
that reads as success; never a claim.

**1.1.6 Autonomous and commanded are one capability.** What eLo does by choice, the Executive can invoke;
what the Executive invokes, eLo can also choose. Never two divergent paths that can drift apart.

## 1.2 The channels (this is the whole interface)

| Channel | File | Direction | Delivery | Holds |
|---|---|---|---|---|
| **DOWN — render + command** | `blender/blender_state.json` | eLo OS → body | continuous (overwritten each tick) | the complete state the body renders: `motion` · `expression` · `state` (emotion/glow) · `gaze` · `presence_plan` · `intent` · panel flags · `capability_list` · **action commands** (`<action>_command`) · `_ts` |
| **UP — events / ACKs** | `blender/unity_events.json` | body → eLo OS | discrete (timestamped, **consumed** after read) | completion ACKs and perceptions: `{"type":"sit_complete","_ts":…}`, `move_complete`, `arrived`, `collided`, `landed`, `resurfaced`, `window_opened` (Vol XIII Ch.3) |
| **UP — sensed state** *(only if needed)* | `blender/unity_state.json` | body → eLo OS | continuous | live sensed values the brain reads into its self/world model: rendered `position` · `surface` · `occluded` · pose-as-rendered. Add **only** when continuous sense-back is required; otherwise fold the value into an event. |

**Adding `emotions.json` / `states.json` / `movement.json` is FORBIDDEN** — it multiplies the
read/write mismatch surface. One concern = one field in the right channel.

**Live note:** `blender/elo_spatial.json` (Unity → Python: `pos_x`, `pos_y`, `height_px`, `window`,
`screen_w/h`, `_ts`) is in practice the third channel, already implemented and read by
`desktop/spatial_state.get_elo_spatial()`. **It should be recognised as the `unity_state.json` slot rather
than left undocumented** — see OQ-1.1. This is exactly the drift the contract exists to prevent.

## 1.3 The action protocol (Embodied Truth — every action is verifiable or it is pointless)

Every **action command** written DOWN must have a matching **ACK** read UP before the Executive speaks the
action. **No fire-and-forget.**

```
eLo OS: write <action>_command (DOWN, blender_state.json)  →  set _PENDING[action] = { since: _ts }
Body:   execute → write <action>_complete (UP, unity_events.json, with _ts)
eLo OS: each turn read UP →
            if type == <action>_complete AND _ts > _PENDING[action].since:
                update self-model (pose / surface / position)
                clear pending
                CONSUME (clear the event)
                → only NOW may the Executive say the action happened
        on no ACK within timeout:
                say so honestly ("I tried to X but couldn't") — never claim success
```

**Protocol rules (MUST):**
1. **Timestamp guard** — `_ts > since`, so a stale event can never false-trigger. (Live in `server.py`.)
2. **Consume** — clear the event after read, so the next action starts from a clean slate.
3. **The ACK type names the action** — `sit_complete`, `move_complete`, `exit_complete`. One naming rule,
   no per-action special cases.
4. **Applies to every action, not just sit:** sit · move (left/right/up/down/shift/to-surface) · jump ·
   wave · hide/step-out · return — the same loop with its own `_command` / `_complete` pair.
5. **In-flight de-duplication** — a duplicate command while one is in flight must NOT re-emit the `_ts`
   (WO-054). Repeating "sit" does not restart the sit.
6. **Dormant/steered bodies must wake, un-steer, and re-attach before executing** (WO-063), and the ACK
   still gates belief — waking is not arriving.

## 1.4 Command envelope (DOWN) — generalising the live shape

Today `state_writer` emits a fixed set (`sit_command`, `move_command{type}`, `leave_command`,
`return_command`). The generalised form keeps the same channel and the same file, and adds only fields:

```jsonc
// blender/blender_state.json  (DOWN — continuous, overwritten each tick)
{
  "motion":     { "animation": "idle", "speed": 1.0, "intensity": 0.5, "duration": 4.0,
                  "mood": "neutral", "mode": "idle" },
  "expression": { "shape_keys": {}, "head_lean": 0.0, "pacing": "steady", "intensity": 0.5 },
  "state":      { "energy": 0.5, "mode": "idle", "emotion": "neutral",
                  "emotional_state": "neutral", "intensity": 0.3 },
  "gaze":       { "yaw": 0.0, "pitch": 0.0, "active": true },     // orientation — NO eyes
  "intent":     { "name": "move", "sub_type": "wall_jump" },

  "move_command": {
    "type":  "wall_jump",                 // EXISTING single-verb form — still valid (1-leg route)
    "route": [                            // NEW, additive: the Vol XIII Ch.2 route
      { "verb": "APPROACH", "to": {"surface_id":"vscode:1","anchor":{"x":1180,"y":300}},
        "precondition": [],       "expected_ms": 900 },
      { "verb": "PEEK",     "to": {"surface_id":"vscode:1","anchor":{"x":1240,"y":300}},
        "precondition": [],       "expected_ms": 400 },
      { "verb": "LEAP",     "to": {"surface_id":"chrome:1","anchor":{"x":1330,"y":290}},
        "precondition": ["PEEK"], "expected_ms": 700 }
    ],
    "issued_by": "SpatialFaculty",
    "_ts": 1754812345.123
  },
  "_ts": 1754812345.123
}
```

**Envelope rules (MUST):**
- **Additive only.** A `move_command` with `type` and no `route` behaves exactly as today. This is what makes
  the Vol XIII Ch.2 migration safe (parity first, removal second — OQ-2.1 there).
- `issued_by` is **mandatory** on any command implying traversal, and MUST be `SpatialFaculty`. The body
  rejects a route from any other issuer. This is the mechanical enforcement of "one owner of spatial
  reasoning" (Ruling D-XIII-1).
- **Every `LEAP` leg carries `precondition: ["PEEK"]`** and a `PEEK` leg precedes it. The body rejects a
  route that violates it — a blind jump is invalid at the channel, not merely discouraged upstream
  (WO-049 build rule 1).
- The body executes the route **leg by leg** and ACKs each leg. It does not re-order, substitute, or
  shortcut legs.
- Read-merge-write discipline on `blender_state.json` — writers merge; nobody clobbers another owner's block.

## 1.5 Event envelope (UP)

```jsonc
// blender/unity_events.json  (UP — discrete, timestamped, CONSUMED after read)
{ "type": "move_complete",         // or: sit_complete · exit_complete · arrived · landed ·
                                   //     collided · resurfaced · window_opened/closed/moved · user_idle
  "leg":  2,                       // which leg of the route, when applicable
  "at":   { "surface_id": "chrome:1", "pos": {"x":1330,"y":290} },   // where the body ACTUALLY is
  "ok":   true,
  "detail": "",                    // on failure: what happened, factually
  "_ts":  1754812348.4 }
```

**Event rules (MUST):**
- `at` is **mandatory on any motion ACK**. The brain re-reads the *real* position from the body rather than
  assuming the commanded one. This is the "brain reads that back" half of the loop.
- **Reflex events are mandatory** (Vol XIII Ch.2 §2.2.3): `landed`, `resurfaced`, `collided`. A local safety
  action that is never reported is indistinguishable from the body deciding, and is forbidden.
- Perceptions travel on this same channel (`window_opened`, `user_idle`) — they are reports, never
  decisions (Vol XIII Ch.3; WO-086).
- Events are consumed. Nothing may re-read a consumed event and act again.

## 1.6 Faculty Contract

```
Faculty:
  name:            MotorCortex
  version:         1.0.0
  purpose:         Carry decided actions to the body and carry verified outcomes back, so eLo's belief
                   about what he has done is always the body's report and never his own intention.
                   Delivers; never decides.
  contributes_to:  CognitiveState (verified pose/position/surface) + the Executive's permission to speak an action
  runs_in:         response-path (write DOWN) + per-tick (read UP)

Inputs:
  - type: action_intent    source: Executive / Volume XIII (Presence + Spatial)   required: true
    description: the decided action or route. The ONLY legitimate source of movement intent.
  - type: expression_plan  source: Presence (Vol XIII Ch.1) + Emotional Light Engine   required: false
    description: motion/expression/state/gaze blocks. Carried DOWN, never authored here.
  - type: body_event       source: body UP channel (unity_events.json)            required: false

Outputs:
  - type: command          destination: body (blender_state.json DOWN)
    description: <action>_command with _ts, issued_by, and (for traversal) an ordered route.
  - type: verified_outcome destination: CognitiveState + Vol XIII Ch.4 (learning)
    description: ACK'd action + the body's ACTUAL position/surface. The sole basis for belief.
  - type: failure_report   destination: Executive
    description: honest inability, with the reason. Never silence, never a claim.

Dependencies:
  - faculty: SpatialFaculty (Vol XIII Ch.2, HARD for traversal — the only valid route issuer)
  - faculty: PresenceFaculty (Vol XIII Ch.1, SOFT — expression blocks)
  - surface: Unity / Blender / robot motor abstraction (avatar/motor_abstraction.py)

Failure Modes:
  - condition: no ACK within timeout
    fallback:  clear pending, report honestly ("I tried to X but couldn't"), do NOT retry silently,
               do NOT claim success (ADR-Exec-003). Vol XIII Ch.4 records a verified failure.
  - condition: stale ACK (_ts <= pending.since)
    fallback:  ignore it. It may not satisfy the pending command.
  - condition: duplicate command while in flight
    fallback:  do NOT re-emit _ts (WO-054). The in-flight action continues.
  - condition: body offline / surface not running
    fallback:  commands are not written as if delivered; eLo reasons and speaks headless, and claims
               no action occurred.
  - condition: body dormant or steered (dragged)
    fallback:  wake → un-steer → re-attach → execute (WO-063). Waking is not arriving; the ACK still gates.
  - condition: route rejected (bad issuer, or a LEAP without a preceding PEEK)
    fallback:  reject at the channel, emit a rejection event UP, and do NOT execute a partial route.
  - condition: a command arrives from a non-Executive source
    fallback:  REJECT. Only the one brain commands the body (ADR-Exec-002).
```

## 1.7 ⚖ The "no local driver decides" law (and how it is audited)

**Law.** No component inside the body — Unity C#, Blender driver, robot firmware, or any local script —
may *choose* a behaviour. It may sense, execute what it was commanded, and report. Nothing else.

**The one carve-out** is the bounded reflex (Vol XIII Ch.2 §2.2.3): a local action taken purely to keep the
body physically coherent when the brain cannot be consulted in time — fall→land, own-surface-destroyed→
re-attach, collision→stop. **Every reflex must emit an event UP.** An unreported reflex is a decision.

**Audit rule (MUST be a standing check, not a one-off):**

```
For every observable behaviour B the body performs:
  1. Is there a <action>_command DOWN with issued_by set, whose _ts precedes B?      → LEGAL (commanded)
  2. Else, is B in the bounded-reflex list AND did it emit an event UP?              → LEGAL (reflex)
  3. Else                                                                            → VIOLATION
```

**Known violations at the time of writing:**

| Local driver | Status | Ruling |
|---|---|---|
| `EloIdleBehaviour` mouse-idle calm | **CLOSED** | routed UP; the brain decides the idle repertoire (WO-086) |
| **`EloDesktopNav._route`** | **OPEN — the largest one** | selects the traversal locally. **Ruling D-XIII-1** demotes it to executor + bounded reflex. David explicitly asked for this audit of *other* local drivers when WO-086 was raised; the navigator was never included. |
| `DesktopBuddy` survival re-attach | **LEGAL, keep** | bounded reflex — but it MUST emit `resurfaced` UP (WO-094 §A: must not regress) |

## 1.8 Faculty Lifecycle

```
INITIALISING → open DOWN writer + UP reader; discover which surface/body is present; load pending map
ACTIVE       → carrying continuous state DOWN each tick; polling UP for events; nothing pending
PROCESSING   → on action intent: validate issuer + preconditions → write <action>_command
               → set _PENDING[action] = { since: _ts, expected_ms }
   ├─ ACK with _ts > since ─► update self-model from event.at · clear pending · consume
   │                          · release the Executive to speak the action
   ├─ timeout               ─► ERROR_RECOVERY: clear pending · honest failure report · record failure
   └─ reflex event          ─► update position from event.at; notify Vol XIII to re-plan
LEARNING/UPDATING → (integration window) tune per-action timeouts from observed latencies ONLY.
                    Never a behaviour change; never a personality delta.
STABLE → ACTIVE
```

**Lifecycle rule (MUST):** `PROCESSING` never blocks on the body. Commands are dispatched and ACKs read on
later ticks. A conversational turn must never wait for a jump.

## 1.9 Message Envelope Binding

Per `Volume_V/CONTRACTS.md` §2.

```jsonc
{
  "id": "uuid",
  "sender": "MotorCortex",
  "receiver": "Executive",
  "priority": "high",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "desktop",
    "significance": 0.0,
    "memory_instruction": { "store": true, "priority": "low" }
  },
  "payload": {
    "type": "verified_outcome",
    "body": {
      "action": "move", "leg": 2, "ok": true,
      "at": { "surface_id": "chrome:1", "pos": {"x":1330,"y":290} },
      "evidence": { "event_type": "move_complete", "_ts": 1754812348.4,
                    "commanded_ts": 1754812345.123 }
    }
  },
  "confidence": 1.0,
  "expires": null,
  "trace": ["SpatialFaculty@ts", "MotorCortex@ts(down)", "Body@ts", "MotorCortex@ts(up)"]
}
```

**Binding rules (MUST):** `evidence` is mandatory and MUST show `_ts > commanded_ts` — an outcome without
that proof is inadmissible and may not release speech. `confidence` is `1.0` or the outcome is not a
verified outcome; there is no partial belief about whether the body moved. `trace` shows the full round
trip, which is what makes brain>body>brain auditable after the fact.

## 1.10 Acceptance Tests

### Functional
```
FT-1  Command down, ACK up, then belief
  Given:  a sit intent
  Then:   sit_command is written DOWN with _ts; the Executive does NOT say "I'm sitting";
          on sit_complete with _ts > since, the self-model updates and only then may he say it

FT-2  Stale ACK cannot satisfy a command
  Given:  an ACK with _ts <= pending.since
  Then:   pending is NOT cleared and nothing is claimed

FT-3  Timeout is honest
  Given:  a command with no ACK within timeout
  Then:   an honest failure is reported, pending is cleared, and no success is recorded anywhere

FT-4  Duplicate command does not restart the action
  Given:  a second identical command while one is in flight
  Then:   the _ts is not re-emitted (WO-054) and the in-flight action continues

FT-5  Commanded state owns the body
  Given:  a held sit (_sitHeld)
  Then:   autonomous/ambient behaviour does not overwrite it until an authority of equal or greater
          standing changes it

FT-6  Route validation at the channel
  Given:  a route containing a LEAP with no preceding PEEK, or issued_by != SpatialFaculty
  Then:   the command is REJECTED, a rejection event is emitted UP, and no partial route executes
```

### Stability
```
ST-1  No new files
  Given:  a new action or a new emotional concern
  Then:   it appears as a FIELD in blender_state.json / unity_events.json — no new channel file exists

ST-2  Body offline degrades honestly
  Given:  Unity is not running
  Then:   eLo converses normally and claims no action occurred; nothing is written as if delivered

ST-3  Dormant/steered body
  Given:  a command while eLo is dormant or being dragged
  Then:   wake → un-steer → re-attach → execute (WO-063); the ACK still gates belief

ST-4  Reflex is always reported
  Given:  any bounded reflex fires
  Then:   an event appears UP with the body's ACTUAL position; the brain re-plans from it

ST-5  Additive route field is backwards compatible
  Given:  a move_command with `type` and no `route`
  Then:   behaviour is identical to the current live system
```

### Integration
```
IT-1  The closed loop, end to end
  Vol XIII decides → MotorCortex writes DOWN → body executes → ACK UP → belief → speech permitted
  Assert: removing the ACK removes the belief AND the speech. There is no path from intent to
          assertion that skips the body.

IT-2  The audit rule finds violations
  Given:  the running system and §1.7's three-step check applied to every observed behaviour
  Then:   every behaviour is either commanded or a reported reflex
          AND EloDesktopNav's locally-selected traversal is reported as a VIOLATION until D-XIII-1 lands

IT-3  Autonomous and commanded are one capability
  Given:  a behaviour eLo performs on his own
  Then:   the Executive can invoke the SAME capability through this channel — no second code path
```

## 1.11 Open Questions (flagged for Chief Architect / David)

- **OQ-1.1** `blender/elo_spatial.json` already carries continuous sensed state UP (position, height, screen
  size) and is read by `desktop/spatial_state.py`, but the IO contract's third channel is written as
  `unity_state.json` *"only if needed."* Recommend **recognising `elo_spatial.json` AS that channel** in the
  IO contract rather than adding a second file — undocumented channels are the exact drift class the
  contract exists to prevent. Needs the two seats' sign-off (both signed the contract).
- **OQ-1.2 (David L3 — changes a contract he signed).** Adding `route` + `issued_by` to `move_command` is
  additive and backwards compatible, but it does change the DOWN contract. Confirm, and confirm the
  sequencing: ship the field, prove parity, *then* remove Unity's local route selection.
- **OQ-1.3** Per-action timeouts: fixed, or derived from the route's `expected_ms` sum plus slack?
  Recommend derived — a three-leg route legitimately takes longer than a sit, and a fixed timeout would
  either falsely fail long routes or hide short failures.
- **OQ-1.4** Should leg ACKs be individual (`move_complete{leg:2}`) or only terminal (`arrived`)?
  Recommend **both**: per-leg for verification and learning granularity, plus a terminal `arrived` the
  Executive gates speech on. (Pairs with Vol XIII OQ-2.3.)

## 1.12 References

- `docs/architecture/UNITY_ELOOS_IO_CONTRACT.md` — **the ratified interface (David L3, 2026-08-06)**; this
  chapter canonises it, and any change to it must update that document too.
- `_intake/SOURCE_2026-08-10_brain_body_brain_loop.md` — **VERBATIM primary source; referenced, never replaced.**
- `_intake/SOURCE_2026-08-10_roam_os_vision.md` §7 — *"goal → aim → find the path → execute → confirm it happened."*
- WO-035 (intent) · WO-040 (`_sitHeld`) · WO-041 (ACK / verify-before-speak) · WO-054 (in-flight queue) ·
  WO-063 (command while dormant) · WO-086 (loop pattern; the mouse-idle precedent) · WO-094 (events UP).
- `ARCHITECTURAL_PRINCIPLES.md` — Embodied Truth · Verified Speech · Single Cognitive Truth ·
  Autonomous-and-commanded-are-one.
- `Volume_XIII/` (the deciding brain) · `Volume_XI/02` (the verbs that travel this channel).
- Code: `blender_bridge/state_writer.py` (`write`, `write_with_presence`, `*_command`),
  `server.py` (ACK gating with `_ts > since`), `avatar/unity_bridge.py`, `avatar/animation_router.py`,
  `avatar/motor_abstraction.py`, `avatar/safety_controller.py`, `blender/unity_events.json`,
  `blender/elo_spatial.json`.

---

```
Chapter 1 — The Motor Cortex & the Body Contract
Status: READY FOR REVIEW
Implementation: PARTIAL (DOWN/UP channel + ACK loop LIVE for sit·move·leave·return; route field + generalised verbs PENDING)
Law: no local driver decides — with a three-step standing audit rule (§1.7) and the open violation named
Faculty Contract: Included · Lifecycle: Included · Envelope: Included (DOWN + UP + faculty envelope)
Acceptance Tests: FT ×6, ST ×5, IT ×3 · Open Questions: 4 (1 David L3)
```

READY FOR REVIEW
