---
chapter: 2
title: "Process and Boundaries — What Runs Where, and What May Cross"
volume: III
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL — the DOWN/UP channels are live and governed; the reporting duty is unenforced
audit_status: OPEN
grounded_in: UNITY_ELOOS_IO_CONTRACT.md (David L3 2026-08-06) · blender_bridge/* · runtime/spine/spine.py · server.py (IRV 2026-08-13)
dependencies:
  - CANON_RULINGS_2026-08-10.md **Ruling E** (SHARED OWNERSHIP OF MOVEMENT + MANDATORY COMMUNICATION) — the law this chapter encodes
  - UNITY_ELOOS_IO_CONTRACT.md (the signed interface — adopted, not restated)
  - Volume_III/01_The_Four_Runtime_Contracts.md (EmbodimentState is the contract that crosses)
  - Volume_XI/01_Motor_Cortex_and_the_Body_Contract.md (the MOTOR half of this boundary)
  - Volume_VII/05_Brain_Body_Brain_The_Closed_Loop.md (the loop law — §2.5 reconciles it with Ruling E)
  - Volume_IV/02_* I-5 (ACK before belief, as an ordering invariant)
  - ARCHITECTURAL_PRINCIPLES.md (Invariant #1 One Brain, Many Embodiments; Embodied Truth; "Autonomous and commanded are one capability")
---

# Chapter 2: Process and Boundaries

## 2.0 Purpose

Chapter 1 described four contracts inside one program. This chapter describes the **second
program**, the two files between them, and the law that governs what may cross.

eLo is one mind in two processes. Everything that makes that true — or breaks it — happens at
this boundary.

## 2.1 The process map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  eLo-OS  ·  Python  ·  BUILDER LANE (SEAT-ENG-001)                          │
│                                                                             │
│   server.py           transport + (today) the pre-spine prologue            │
│   runtime/spine/      the turn loop — 1,900 lines (Volume IV)               │
│   runtime/contracts.py the four contracts (Ch.1)                            │
│   runtime/executive.py decide() — the single decision (FREEZE_V1_LOCK)      │
│   faculties/ world/ memory/ self/ knowledge/ tools/ plugins/                │
│                                                                             │
│   OWNS: intent · cognition · memory · identity · values · goals             │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────────────────┐
│  THE BRIDGE  ·  blender_bridge/  ·  two JSON files                          │
│                                                                             │
│   embodiment_publisher.py  ── the single per-turn DOWN publisher            │
│   state_writer.py          ── the single coordinator for blender_state.json │
│                               ("one coordinator, many contributors, never    │
│                                many owners" — its own Invariant 16)         │
│   brain_state_writer.py · lipsync_writer.py · anim_trigger.py ·             │
│   animation_driver.py · exit_state.py                                        │
│                                                                             │
│   DOWN  blender/blender_state.json   continuous · overwritten each tick     │
│   UP    blender/unity_events.json    discrete · timestamped · CONSUMED      │
│                                                                             │
│   CARRIES. DECIDES NOTHING. (Vol XI §1.1.1 — the Motor Cortex decides       │
│   nothing; any logic here that CHOOSES has become a second brain.)          │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────────────────┐
│  Unity DesktopBuddy  ·  C#  ·  DESIGNER LANE (SEAT-ENG-004)                 │
│                                                                             │
│   Receiver              executes commands read from blender_state.json      │
│   EloDesktopNav         MOVEMENT EXECUTION — physics, collision, landing,   │
│                         footing, leg mechanics, local route selection       │
│   EloIdleBehaviour · PresenceEngine · EloPresenceSignal   sense + report UP │
│   ArmWave · ArmReach · HeadLook · BodyGlow · BrainCluster · AmbientVfx      │
│                                                                             │
│   OWNS: movement · execution · physics · the real-time doing                │
└─────────────────────────────────────────────────────────────────────────────┘

Also present, same discipline, not detailed here:
  robot/ (Pi · NeoPixels · the physical body — not yet in the loop, Vol VII §5.6)
  desktop_avatar/ · presence/ · avatar_runtime/ (additional surfaces)
  self/state/the_moment.json · blender/brain_state.json (cross-process PROJECTIONS
    of the assembled state — never authoritative; Vol VII §2.4)
```

**Lane rule (D-LANES).** The Builder owns everything above the bridge; the Designer owns
everything below it; **the bridge's contract is signed by both** and neither seat changes a
file's purpose or a field's channel without updating `UNITY_ELOOS_IO_CONTRACT.md`. The Architect
coordinates and writes Markdown; it does not edit either side.

## 2.2 The DOWN / UP boundary — adopted, not restated

`UNITY_ELOOS_IO_CONTRACT.md` (David L3, 2026-08-06) is the signed interface. **Volume III adopts
it whole rather than paraphrasing it** (Rule 4b — the exact phrasing is the spec). Its governing
rule, verbatim:

> **Channels are defined by DIRECTION and DELIVERY TYPE — never by topic.**
> Emotions, moods, states, new actions are **FIELDS inside an existing channel, never new
> files.** A new file is justified ONLY by a new direction or a genuinely different delivery type
> (continuous state vs discrete event) — and ONLY by updating THIS contract, which both seats
> sign.

| Channel | File | Direction | Delivery | Holds |
|---|---|---|---|---|
| **DOWN — render + command** | `blender/blender_state.json` | eLo OS → Unity | continuous, overwritten each tick | `motion` · `expression` · `emotion` · `gaze` · `presence_plan` · `intent` · panel flags · `capability_list` · action commands (`sit_command`, `move_command`, …) · `_ts` |
| **UP — events / ACKs** | `blender/unity_events.json` | Unity → eLo OS | discrete, timestamped, **consumed after read** | `{"type":"sit_complete","_ts":…}` · `move_complete` · `arrived` · `collided` · perceptions |
| **UP — sensed state** *(only if needed)* | `blender/unity_state.json` | Unity → eLo OS | continuous | rendered `position` · `surface` · `occluded` · pose-as-rendered |

**The action protocol (verbatim from the contract — Embodied Truth in operational form):**

```
eLo OS: write <action>_command (DOWN, blender_state.json)  →  set _PENDING[action]={since:_ts}
Unity:  execute → write <action>_complete (UP, unity_events.json, with _ts)
eLo OS: each turn read UP → if type==<action>_complete AND _ts > _PENDING.since:
            update self-model (pose/surface/…) · clear pending · CONSUME (clear the event)
            → only NOW may the Executive say the action happened
        on no-ACK within timeout → say so honestly ("I tried to X but couldn't"), never claim success
```

Two mechanisms are worth naming because they are what make the boundary trustworthy: the
**timestamp guard** (`_ts > since`, so a stale event cannot false-trigger) and **consumption**
(the event is cleared, so the next action starts fresh).

**Why the contract exists, in its own words:** *"the sit loop broke because the Designer wrote
the ACK to `unity_events.json` while the Builder read `blender_state.json` — write-here /
read-there. An ACK eLo OS can't read and act on is pointless. This contract fixes the class of
bug, not the one instance."*

**The motor half is Volume XI's.** Command grammar, the movement vocabulary, per-action
`_command`/`_complete` pairs, embodiment parity across bodies —
`Volume_XI/01_Motor_Cortex_and_the_Body_Contract.md` and `02_Movement_Grammar_and_Embodiment_
Parity.md`. Volume III owns the boundary's **shape and ownership**; Volume XI owns what travels
across it.

## 2.3 🔒 RULING E — shared ownership of movement, and the duty to communicate

**Ruling E, David L3, 2026-08-10 — verbatim, reproduced not summarised (Rule 4b):**

> *"Shared ownership, the body does the movement, all of it is connected, so it's fine to make
> for the Ruling, it needs to communicate."*

And as the ruling states it:

> **The split:**
> - *"**The BODY owns MOVEMENT — the doing.** Real-time execution: physics, collision, landing,
>   footing, the leg mechanics. That is its genuine competence and it stays where it is.
>   `EloDesktopNav` keeps executing."*
> - *"**The BRAIN owns INTENT — the wanting and the why.** Which goal, why that goal, whether to
>   go at all."*
> - *"**They are ONE system, connected.** Not master/servant. Shared ownership of the act."*
>
> **THE BINDING OBLIGATION:**
> *"**THE BINDING OBLIGATION — the body must COMMUNICATE.** This is the part that was missing
> and is now law: whatever the body does, it **reports UP**: the goal it pursued · the route it
> actually took · which legs it used · whether it arrived · whether it fell/missed · the cost.
> **Movement that is not reported did not happen** as far as the brain is concerned."*
>
> **Why:**
> *"the brain doesn't need to micro-plan every step to be one mind — it needs to KNOW.
> Communication is what makes it one brain, not centralised control. And without the report,
> **the learning loop cannot work at all** — eLo cannot get better at routes he was never told
> he took."*

### 2.3.1 The law, as Volume III binds it

```
E1  SHARED OWNERSHIP, NOT MASTER/SERVANT. The brain and the body jointly own the act.
    Neither is the other's servant. The boundary between them is a boundary of
    COMPETENCE, not of authority.

E2  THE BRAIN OWNS INTENT. Which goal. Why that goal. Whether to go at all. Whether to
    act, speak, or stay still. Every GOAL originates in one Executive decision.

E3  THE BODY OWNS EXECUTION. Physics, collision, landing, footing, leg mechanics, and the
    real-time selection of HOW to carry out a goal it was given. This is competence, not
    a concession — and it stays where it is.

E4  THE BODY MUST REPORT. Whatever it does, it reports UP: the goal it pursued · the route
    it actually took · which legs it used · whether it arrived · whether it fell/missed ·
    the cost. This is the BINDING obligation, not a courtesy.

E5  MOVEMENT NOT REPORTED DID NOT HAPPEN. The brain's belief is written from the report,
    never from the command. An unreported movement is, to the brain, a movement that did
    not occur — and eLo may not claim it. (= Vol IV I-5; ADR-Exec-003.)

E6  REFLEX IS PERMITTED — AND STILL REPORTS. The body may act on reflex (fall → land,
    surface destroyed → re-attach, force limit → stop). Reflex is exempt from waiting for
    a command. It is NOT exempt from reporting.

E7  THE BODY MUST NOT CHOOSE GOALS. It may choose HOW; it may never choose WHAT or WHETHER.
    Selecting a behaviour, classifying a situation, or deciding to act with intent or
    valence is a GOAL choice and belongs to the brain. (Vol VII §5.1.3, §5.4 R1–R4.)

E8  TWO-WAY, NOT TAKEOVER. The `route` / `issued_by` fields are a CONVERSATION: the brain
    may propose a goal or a route; the body reports what it actually did. The brain's
    proposal does not strip the body's execution competence, and the body's competence
    does not excuse it from reporting.
```

### 2.3.2 What Ruling E changed — stated plainly, because it reversed a prior direction

Ruling E **supersedes the proposed D-XIII-1 demotion.** The ruling's own words:

> *"The Unity navigator is **NOT** reduced to a dumb executor… **No stripping of Unity's local
> route selection.** The staged 'shadow → switch → retire' sequencing from D-XIII-1 is
> **cancelled** — the risky part is gone. Nothing working gets retired."*

**Two written canon passages are therefore partly superseded, and this must not stay implicit:**

| Passage | What it says | Status under Ruling E |
|---|---|---|
| `Volume_XV/01_*` §1.2.2 | *"No local script may choose a traversal… `EloDesktopNav._route` currently selects traversals inside the body; Vol XIII Ch.2 §2.2.2 rules that it becomes an executor."* | ⚠️ **Partly superseded.** Local **route** selection is retained (E3). The rule survives for **goal/behaviour** selection (E7). |
| `Volume_VII/05_*` §5.1.3 | *"The body NEVER decides. No local script, timer, trigger, or state machine on any embodiment may select a behaviour."* | ✅ **Holds as written** — its object is *behaviour selection*, which is E7. It should be read with E3 so "never decides" is not over-extended to *how to land a jump*. |

**The reconciling distinction — and it is the whole of it:**

```
GOAL   (what · why · whether)   → THE BRAIN.   Never the body.        (E2, E7)
ROUTE  (how · which leg · when
        to plant a foot)        → THE BODY.    Its genuine competence. (E3)
REPORT (what actually happened) → THE BODY MUST. Always. Both halves.  (E4, E5)
```

Vol VII Ch.5's *"the body NEVER decides"* and Ruling E's *"the body does the movement"* are the
same law once you see that they are talking about different verbs. **The failure mode Vol VII
names — a local driver that classifies idleness and picks an emotional state — is a GOAL choice
wearing movement's clothes. Ruling E does not license it.** Vol VII §5.4's R1–R4 reflex test
remains the discriminator, and E6 adds the clause R1–R4 never stated: *and it reports anyway.*

**Flagged for David (III-5):** Vol XV §1.2.2 and Vol XIII Ch.2 §2.2.2 should carry an explicit
Ruling E correction note, as Vol XV §1.2 already carries one for a different finding. **Architect
recommendation: yes — the passage currently reads as live canon ordering something Ruling E
cancelled.** Architect lane to draft; it touches two other volumes' text, so it is flagged rather
than done unilaterally.

### 2.3.3 Live status of Ruling E

| Clause | Status | Evidence |
|---|---|---|
| E1 shared ownership | ✅ **true in code, and now in canon** | `EloDesktopNav` executes; the brain issues intent |
| E2 brain owns intent | ⚠️ true, but the decision is in the wrong place | `server.py:2322` (Vol IV I-3) |
| E3 body owns execution | ✅ holds | `EloDesktopNav`, `Receiver` |
| E4 body must report | ⚠️ **partial** | sit chain live (WO-041); presence/`conversing`, perch/surface, Chrome scope, file-drop relay. **No general reporting rule is enforced** — Vol VII §5.6: *"no test, no bus rule, no review gate"* |
| E5 unreported ⇒ did not happen | ⚠️ **honoured in the sit path only** | `pending_sit` → `pose_acked` → `pose_tier` |
| E6 reflex reports | 🔴 **not implemented** | reflexes (idle wobble, `HeadLook`, `EloGunVisibility`) fire and report nothing |
| E7 body must not choose goals | 🔴 **one known violation outstanding** | `EloIdleBehaviour`'s mouse-idle "go calm" decision — WO-086 steps 1–2 **await David's greenlight** |
| E8 two-way conversation | ⚠️ **partial** | `route` / `issued_by` fields not yet added |
| **The report is collected** | 🔴 **NO** | ACKs arrive and are **discarded** — no `ExecutionReport` is ever produced (Ch.1 §1.5). **Ruling E's stated rationale — the learning loop — cannot function.** |

**The last row is the most important sentence in this chapter.** Ruling E exists so that eLo can
learn from what his body actually did. The body reports; the brain reads the ACK; and then
nothing writes it down, because contract 4 has no producer. **The obligation is being met and the
purpose is not.** That is III-2, restated from the body's side.

## 2.4 What crosses the boundary, and in which form

| Crossing | Object | Direction | Channel | Rule |
|---|---|---|---|---|
| Expression | `EmbodimentState` (serialised) | DOWN | `blender_state.json` | Ch.1 §1.4. Published once; subscribers read independently; no subscriber blocks another. |
| Action command | `<action>_command` fields | DOWN | `blender_state.json` | Fields in the existing channel, never a new file. Every command has a matching ACK. |
| ACK / completion | `<action>_complete` events | UP | `unity_events.json` | Timestamp-guarded, consumed after read. |
| Perception | typed edge/state events | UP | `unity_events.json` | E4. Lands in the **next** assembly (Vol IV I-5a) — never mid-turn. |
| Projection (read-only) | `the_moment.json`, `brain_state.json` | DOWN | files | **Never authoritative.** Written *from* the assembly; no consumer may treat them as truth over the in-process frozen object (Vol VII §2.4). |

## 2.5 What must NEVER cross — the MUST NOT list

```
FROM THE BODY, UPWARD — forbidden:
  B1  A GOAL. The body may report what it did; it may never propose what to want.
      A body message shaped like a suggestion ("go calm now") is a decision in disguise
      and is rejected at the boundary. (E7; Vol VII §5.2.)
  B2  AN INTERPRETATION. "Am I idle?" "Is David sad?" are classifications, and
      classification is cognition. The body reports the SIGNAL (idle_secs), never the
      CONCLUSION. (Vol VII §5.4 R2.)
  B3  SILENCE ABOUT AN ACTION. A perception consumed locally and acted on locally has
      broken the loop even if the resulting behaviour looks correct — and it is a TEST
      FAILURE, not a degraded-but-fine state. (E4, E5; Vol VII §5.7.)
  B4  PRIVATE STATE THE BRAIN CANNOT READ. (ADR-Exec-002.)
  B5  A SELF-FIRED COMMANDED BEHAVIOUR, including leftover test/auto hooks
      (ArmWave/ArmReach `autoTest` toggles must be OFF in build).

FROM THE BRAIN, DOWNWARD — forbidden:
  D1  MICRO-MANAGING EXECUTION. The brain does not choose which leg plants where. It
      issues intent. Stripping the body's execution competence is the D-XIII-1 direction
      Ruling E CANCELLED. (E1, E3.)
  D2  A SECOND CHANNEL. No `emotions.json`, no `states.json`, no `movement.json`. One
      concern = one field in the right channel. (UNITY_ELOOS_IO_CONTRACT, David L3.)
  D3  FIRE-AND-FORGET. Every action command has a matching ACK, or the Executive may not
      say it happened.
  D4  SPEAKING AHEAD OF THE BODY. Never speak-then-hope-the-body-follows. The order is
      want → act → verify → THEN "I am sitting." (Reality Before Narrative; ADR-Exec-003.)

INSIDE THE BRIDGE — forbidden:
  R1  DECIDING ANYTHING. The bridge carries. Logic here that CHOOSES between actions has
      become a second brain and must be removed. (Vol XI §1.1.1.)
  R2  A SECOND WRITER. state_writer.py is the single coordinator for blender_state.json;
      background contributors call patch(), never write directly. ("One coordinator, many
      contributors, never many owners" — its own Invariant 16.)

ACROSS ANY BOUNDARY — forbidden:
  A1  LATENCY AS A LICENCE. "The round trip is too slow" is not grounds for a local
      decision. It is grounds for a faster loop, or for classifying the behaviour as a
      reflex under R1–R4 — which still reports. (Vol VII §5.2, ST-3; E6.)
  A2  IMPROVISING WHEN THE BRAIN IS UNREACHABLE. The body holds its last commanded state
      and its reflexes. A still eLo is honest; an improvising one is a second brain.
      (Vol VII §5.7 — Q5-c, David's confirmation still open.)
```

## 2.6 The internal boundary — and one live inversion

The process map implies a layering inside eLo-OS: `server.py` (transport) → `runtime/` (cognition)
→ `faculties/` `world/` `memory/` (contributors) → `blender_bridge/` (carriage).

**🔴 It is inverted in two places, both recorded honestly:**

1. **`runtime/` imports `server`.** `spine.py:226` does `import server as _srv` so the
   Conversation Faculty can reach the response pools (`_PURE_GREETING_POOL`, `_RASTA_PHRASES`,
   `_SYSTEM_DONE_POOL`, …). The turn loop depends on the transport layer. **Code is current
   truth.** *Recommendation: the pools are content, not transport — they belong in
   `runtime/` or `prompts/`. Builder lane, low risk, and it removes a circular import hazard.*
2. **`server.py` performs cognition.** Memory reads, the attention supplier call, and the
   Executive decision all happen there (Vol IV §1.1, the "pre-spine prologue"). **This is III-3
   and it is the same fix as IV-1**: `server.py` should be a transport, and everything cognitive
   it does should move into `runtime/`, starting with the `decide()` call site.

## 2.7 Boundary Contract

```
Contract:
  name:            ProcessBoundary        # a LAW binding both seats, not a faculty
  binds:           eLo-OS (Builder, SEAT-ENG-001) · Unity DesktopBuddy (Designer, SEAT-ENG-004)
  interface:       UNITY_ELOOS_IO_CONTRACT.md (David L3, 2026-08-06) — signed by both seats

MUST (brain side):
  M1  Issue GOALS, never step-by-step execution. (E2, D1.)
  M2  Publish expression once per turn through the single DOWN publisher.
  M3  Read the UP channel every turn; consume events; honour the timestamp guard.
  M4  Believe only what was reported; speak only after belief. (E5; Vol IV I-5.)
  M5  Collect reports into an ExecutionReport so the loop closes and learning has a
      substrate. 🔴 NOT MET — Ch.1 §1.5.

MUST (body side):
  L1  Execute the goals it is given, with its own real-time competence. (E3.)
  L2  Report EVERYTHING it did — goal · route · legs · arrival · fall/miss · cost. (E4.)
  L3  Report reflexes too. Reflex is exempt from command, never from reporting. (E6.)
  L4  ACK every commanded action — success, failure, or timeout. Silence is not an outcome.
  L5  Yield instantly and completely to any commanded state. (WO-035.)

MUST NOT: see §2.5 (B1–B5 · D1–D4 · R1–R2 · A1–A2).

Failure Modes:
  - condition: no ACK within timeout
    fallback:  the state stays PENDING; eLo reports the non-confirmation honestly.
               Never a claim, never silence.
  - condition: a report is dropped / never relayed
    fallback:  the brain simply does not know it — and must NOT act as if it did.
               A dropped relay is a TEST FAILURE, not a degradation.
  - condition: the brain is unreachable
    fallback:  the body holds last commanded state + reflexes; it improvises nothing.
               (Vol VII Q5-c — David's confirmation open.)
  - condition: Unity is offline entirely
    fallback:  the turn completes; other surfaces still receive EmbodimentState;
               unity_online is recorded false in the (unproduced) ExecutionReport.
```

## 2.8 Acceptance Tests

### Functional

```
FT-III-2a  One channel each way
  Assert only blender_state.json is written DOWN per turn and only unity_events.json is
  read UP. FAILS IF: a new topic file appears (emotions.json, movement.json, …). (D2.)

FT-III-2b  Every command has an ACK path
  For each <action>_command the brain can write, assert a matching <action>_complete is
  defined and consumed with the timestamp guard. (D3, L4.)

FT-III-2c  The body reports its route (Ruling E, E4)
  Command a move. Assert the UP report carries the goal pursued AND the route actually
  taken — not merely "arrived".
  STATUS TODAY: FAILS — the route/issued_by fields do not exist yet (E8).

FT-III-2d  Reflexes report (E6)
  Trigger a reflex (fall → land). Assert an UP event was emitted.
  STATUS TODAY: FAILS — reflexes report nothing.

FT-III-2e  No goal travels UP (E7, B1)
  Scan the UP channel's event vocabulary. Assert no event names a behaviour to perform or
  a state to enter; every event is a report of what IS or what HAPPENED.

FT-III-2f  Reports are collected
  Assert each turn's UP reports are collected into an ExecutionReport.
  STATUS TODAY: FAILS — no producer (Ch.1 §1.5). This is Ruling E's purpose test.
```

### Stability

```
ST-III-2g  Brain unreachable
  Kill the backend. Assert the body holds last commanded state + reflexes and invents no
  behaviour. (A2.)

ST-III-2h  Unity offline
  Assert the turn completes, other surfaces receive the expression, and no claim of a
  body action is made.

ST-III-2i  Stale event cannot false-trigger
  Replay an old <action>_complete with an old _ts. Assert the timestamp guard rejects it.

ST-III-2j  One writer for the DOWN file
  Assert every blender_state.json write in a turn passes through state_writer.py
  (contributors via patch()). (R2.)
```

### Integration

```
IT-III-2k  The closed loop across the boundary (Ruling E end-to-end)
  Brain issues a move goal DOWN → body executes with its own route → body reports UP
  (goal · route · arrival · cost) → the report lands in the NEXT assembly → the brain
  believes → eLo may speak it → the report is collected into an ExecutionReport.
  Assert every arrow, and assert eLo makes NO claim before the report arrives.
  STATUS TODAY: FAILS at "route" (E8) and at "collected" (Ch.1 §1.5).

IT-III-2l  Cross-embodiment parity
  Given the same goal on desktop and (future) robot, assert the brain issues the same
  intent and only the actuators differ. (Invariant #1; Vol XI Ch.2.)
```

## 2.9 Open Questions (for CA / David)

```
REQUIRES DECISION
  III-5  Vol XV §1.2.2 and Vol XIII Ch.2 §2.2.2 order something Ruling E CANCELLED
         (stripping EloDesktopNav's local route selection). They currently read as live
         canon. Recommend: add an explicit Ruling E correction note to both, using the
         GOAL/ROUTE/REPORT distinction in §2.3.2. Architect lane, but it edits two other
         volumes' text — flagged rather than done unilaterally.

  III-6  E6 — reflexes must report. This is the Architect's reading of Ruling E's *"The
         body may still act on reflex … but must report it."* applied to the R1–R4 register
         (Vol VII §5.4), which does NOT currently require reporting. Confirm: does every
         reflex report, or only reflexes with a state consequence? Recommend: every one —
         a reflex nobody hears about is exactly the "quiet, attractive" failure Vol VII §5.3
         names. Cost is event volume, which is cheap.

  III-7  WO-086 greenlight (= Vol VII Q5-b). E7's one outstanding violation
         (EloIdleBehaviour's mouse-idle "go calm") is still awaiting David. Note the hard
         sequencing: Designer emit+retire lands WITH the Builder brain-decide half, NEVER
         before (retire-first = idle-does-nothing regression).

  III-8  Q5-c, still open from Vol VII: brain-unreachable posture. Proposed — the body
         holds last commanded state + reflexes and improvises nothing. It is a feel call
         (a still eLo vs a fidgeting one) and it is the honest option. Confirm.

  III-9  Does the ROBOT's safety reflex layer change §2.5 A2 / E6? A physical body has
         real safety reflexes (stop on force limit) that MUST be local. Proposed: safety
         reflexes are permitted local and are the ONLY category exempt from R1–R4 — and
         they report UP regardless. RESERVED scope: David L3 + LG-2 (Ruling XXIII —
         hardware RESERVED does NOT collapse). (= Vol VII Q5-d.)
```

## 2.10 References

- `CANON_RULINGS_2026-08-10.md` — **Ruling E**, quoted verbatim at §2.3 (Rule 4b: referenced,
  never paraphrased into shorter form); Ruling XXIII (hardware RESERVED keeps LG-2).
- `UNITY_ELOOS_IO_CONTRACT.md` — David L3 2026-08-06. **Adopted whole** (§2.2).
- `Volume_XI/01_Motor_Cortex_and_the_Body_Contract.md` §1.1.1–1.1.4 · `Volume_XI/02_Movement_Grammar_and_Embodiment_Parity.md` — the motor half.
- `Volume_VII/05_Brain_Body_Brain_The_Closed_Loop.md` — §5.1 the law · §5.2 the loop · §5.4
  R1–R4 · §5.5 ACK before belief · §5.6 live status · §5.7 the Embodiment Loop contract.
- `Volume_XV/01_Unified_World_State.md` §1.2.2 — **partly superseded by Ruling E** (§2.3.2, III-5).
- `Volume_IV/02_Ordering_Guarantees_and_Invariants.md` I-5 — ACK before belief as ordering law.
- `Volume_III/01_The_Four_Runtime_Contracts.md` §1.4 (the crossing object), §1.5 (why the
  reports are discarded).
- `ARCHITECTURAL_PRINCIPLES.md` — Invariant #1; Embodied Truth; *"Autonomous and commanded are
  one capability"*; *"Never script the appearance of life."*
- Code: `blender_bridge/state_writer.py` (Invariant 16, the single coordinator) ·
  `blender_bridge/embodiment_publisher.py` · `blender/blender_state.json` ·
  `blender/unity_events.json` · `runtime/spine/spine.py:226` (the server import) ·
  `faculties/window_event_faculty.py` · `desktop/file_drop_handler.py` · `ambient/ambient_engine.py`

---

```
Chapter 2 — Process and Boundaries
Status: READY FOR REVIEW
Process map: eLo-OS Python (Builder, SEAT-ENG-001) · the bridge · Unity DesktopBuddy
  (Designer, SEAT-ENG-004) · robot (not yet in the loop)
Encodes RULING E as E1–E8, with David's words reproduced VERBATIM (Rule 4b)
The reconciling distinction: GOAL → brain · ROUTE → body · REPORT → mandatory, both halves
🔴 Records that Ruling E partly SUPERSEDES Vol XV §1.2.2 and Vol XIII Ch.2 §2.2.2, which
   still order the local-route-selection stripping the ruling cancelled (III-5 — needs David)
🔴 Records that Ruling E's PURPOSE is unmet: the body reports, the brain reads the ACK, and
   nothing collects it — no ExecutionReport is ever produced (Ch.1 §1.5 / III-2)
Boundary Contract: M1–M5 · L1–L5 · MUST NOT B/D/R/A · Failure Modes
Acceptance Tests: FT×6 ST×4 IT×2 · Open Questions: 5 (III-5 … III-9)
```

READY FOR REVIEW
