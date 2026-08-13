---
chapter: 5
title: "brain > body > brain — The Closed Loop"
volume: VII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (DOWN leg + ACK live for the sit chain, WO-041/WO-035; the UP-relay rule is unenforced and WO-086 is OPEN awaiting David greenlight)
audit_status: OPEN
dependencies:
  - _intake/SOURCE_2026-08-10_brain_body_brain_loop.md (VERBATIM — David's loop model and principle; PRIMARY SOURCE)
  - engineering/work_orders/WO-086_Mouse_Idle_Through_Brain.md (the first application + the Designer local-driver audit)
  - DECISION_LOG.md ADR-Exec-003 (Embodied Truth · Embodied Cognition · Affordance Before Action · Presence-is-a-state), ADR-Exec-001 (ACK before claim), ADR-Exec-002 (Single Cognitive Truth)
  - ARCHITECTURAL_PRINCIPLES.md (Invariant #1 One Brain, Many Embodiments; Embodied Truth; "Autonomous and commanded are one capability"; "Never script the appearance of life")
  - Volume_XVI/03_Faculty_Bus_Routing_and_Priority.md (the channel the UP leg travels) and /04_… §4.3 (the DOWN projection — no body re-decides)
  - Volume_XII (Perception — the UP leg's producer), Volume_XI (Motor Cortex — the DOWN leg's executor)
  - WO-035 (commanded state owns the body) · WO-041 (verify/ACK) · WO-063 (command wakes body) · WO-064 BP-1 (presence/conversing signal)
---

# Chapter 5: brain > body > brain — The Closed Loop

> **CANONISATION NOTE.** This principle existed in exactly two places: `WO-086` and the verbatim
> intake file it references. WOs close. When WO-086 closes, the rule would have vanished from the
> live architecture — and the `AUDIT_INTENT_core_brain_2026-08-10.md` finding says so explicitly:
> *"'The body NEVER decides on its own… no local script may choose a behaviour' (2026-08-10) —
> **Absent from all five volumes.** Lives only in WO-086 + the intake file."* This chapter is where
> it now lives. WO-086 is the first *application*; this chapter is the *law*.

## 5.0 David's words (VERBATIM — primary source, do not summarise)

From `_intake/SOURCE_2026-08-10_brain_body_brain_loop.md`. Reproduced exactly; canon references it,
it does not replace it (Rule 4b).

**The loop model:**

> brain > body > brain. A CLOSED LOOP: the brain decides + drives the body (DOWN), the body only
> SENSES and ACTS and reports its state back UP, and the brain reads that back and decides again.
> The body NEVER decides on its own. Mouse-idle is just one PERCEPTION feeding this loop — not a
> special case. The generalisable rule the Architect should check: every body perception (mouse-idle,
> occlusion/behind-window, perch/surface, user-active, file-drop) relays UP so the brain closes the
> loop; no local script may choose a behaviour.

**The principle:**

> The brain feeds ALL autonomous behaviour: brain > body > brain. Even a mouse-idle trigger must
> relay UP to the brain and be read back DOWN — no local driver deciding what eLo does.
> (one brain / no parallel drivers)

**What the Architect was asked to check:**

> Evaluate this as the LOOP PATTERN (brain>body>brain), with mouse-idle as the first application.
> Then audit for OTHER local drivers that skip the loop (EloIdleBehaviour's mouse-idle calm is the
> known one; check for others that decide behaviour without relaying up). Confirm it composes with
> WO-041 (verify/ACK) + WO-035 (commanded state owns the body).

## 5.1 The law

**5.1.1 The brain DECIDES and drives DOWN.** Every behaviour eLo exhibits — commanded or autonomous —
originates in one Executive decision (Ch.1). There is no second origin.

**5.1.2 The body SENSES, ACTS, and reports UP. It does nothing else.**
A body's three verbs are *sense*, *act*, *report*. "Choose" is not among them.

**5.1.3 The body NEVER decides.** No local script, timer, trigger, or state machine on any
embodiment may select a behaviour. Not on the desktop avatar, not in the game, not on the robot.

**5.1.4 Every body perception relays UP.** Mouse-idle, occlusion/behind-window, perch/surface,
user-active, file-drop — and every future one. A perception that is consumed locally and acted on
locally has broken the loop, even if the resulting behaviour looks correct.

**5.1.5 Commanded state owns the body.** When the brain has commanded a state, the body holds it.
Autonomous behaviour yields to it. (WO-035; already true in code — `EloIdleBehaviour` yields to
`SitHeld`.)

**5.1.6 ACK before belief.** The brain does not believe an action happened until the body confirms
it. Belief precedes speech; the ACK precedes belief. (ADR-Exec-003 Embodied Truth; ADR-Exec-001;
WO-041.) A commanded state that is never ACKed is a *pending* state, not a true one.

**5.1.7 Autonomous and commanded are one capability.** What eLo does by choice and what the
Executive invokes drive the **same** underlying capability. Never two paths that can drift apart.
(`ARCHITECTURAL_PRINCIPLES.md`; `Volume_XVI` §4.3.)

**5.1.8 Never script the appearance of life.** Life emerges from continuity between faculties, not
from local behaviour scripts. A local driver that produces lifelike behaviour is *counterfeit*
continuity — it looks alive and is not connected to anything eLo knows.
(`ARCHITECTURAL_PRINCIPLES.md`, D-CONTINUITY.)

## 5.2 The loop

```
                        ┌──────────────────────────────────────────┐
                        │            THE BRAIN (One Brain)         │
                        │                                          │
   UP ────────────────► │  ASSEMBLE  (Ch.2 — perception lands in   │
   perceptions,         │             UnifiedCognitiveState)       │
   ACKs, state          │       ↓                                  │
   reports              │  DECIDE    (Ch.1 — ONE CognitivePlan)    │
                        │       ↓                                  │
                        │  COMMAND   (projection, Vol XVI §4.3)    │ ───────► DOWN
                        └──────────────────────────────────────────┘
                                          │
   ┌──────────────────────────────────────┼───────────────────────────────────┐
   │                     THE BODY (any embodiment)                            │
   │                                                                          │
   │   SENSE ──────► (relay UP, always)          ACT ◄────── (execute command) │
   │   mouse-idle · occlusion · perch/surface ·   move · sit · wave · LED ·     │
   │   user-active · file-drop · collision        expression · exit            │
   │                                                                          │
   │   REPORT ─────► (relay UP, always)                                       │
   │   ACK / fail / timeout · pose · position · commanded-state held          │
   │                                                                          │
   │   DECIDE ─────► ✗ FORBIDDEN                                              │
   └──────────────────────────────────────────────────────────────────────────┘
                                          │
                                          └──────► UP (back to ASSEMBLE)
```

**Loop rules (MUST):**

- **The loop closes every turn.** A perception relayed UP lands in the *next* assembly and is
  decided against there. It is never acted on where it was sensed.
- **The UP leg is a report, not a request.** The body says *what is*; it never says *what to do*.
  A body message shaped like a suggestion ("go calm now") is a decision in disguise and is rejected.
- **The DOWN leg is a command, not a suggestion.** The body executes; it does not evaluate whether
  the command is a good idea. Its only permitted refusals are physical (`can't reach`, `blocked`) —
  and those go UP as reports.
- **One channel each way.** UP travels the canonical event path (`unity_events.json` → the bus,
  `Volume_XVI` Ch.3); DOWN travels the canonical action path (`blender_state.json`), the same one
  meditation/sit/move already use (WO-086 confirmation (c)). No side channels.
- **Latency is not a licence.** "The round trip is too slow" is not grounds for a local decision.
  It is grounds for a faster loop, or for the behaviour being classified as a reflex (§5.4).

## 5.3 Why this is the same law as One Brain

This is not a new rule; it is Invariant #1 applied to the DOWN/UP boundary, and Volume XVI already
enforces half of it:

| Leg | Rule | Where it already lives |
|---|---|---|
| **DOWN** | *"No body re-decides."* Each surface renders the plan through its actuators; it never re-interprets the world or invents private state. | `Volume_XVI` §4.3 (projection rules) — **written** |
| **DOWN** | Autonomous and commanded share one path. | `Volume_XVI` §4.3 + `ARCHITECTURAL_PRINCIPLES.md` — **written** |
| **UP** | Every body perception relays UP; no local script may choose a behaviour. | **Nowhere, until this chapter.** The audit: *"The UP leg of `brain > body > brain` is absent… This is the natural home and it is empty."* |

**Why the UP leg is the harder half.** The DOWN leg fails loudly — if a surface re-decides, eLo
visibly contradicts himself. The UP leg fails *quietly and attractively*: a local driver produces
plausible, timely, lifelike behaviour, and nothing looks wrong. That is exactly why it needs to be
canon rather than a review habit. David's diagnosis in WO-086 names the failure precisely:

> *"the body is making a cognitive call (am I idle? go calm) instead of the brain making it from
> real presence state. Same family as the earlier autonomous warp/wave/expression firing
> mid-conversation."*

## 5.4 The reflex line

Not every twitch is a decision. A body may retain **sub-perceptual reflexes** — motion that carries
no intent, no valence, and no interpretation.

**The test (proposed — `OQ-VII-5`).** A body behaviour may remain local **only if all four hold**:

```
R1  It carries NO intent and NO valence. It does not mean anything.
R2  It INTERPRETS nothing. It does not classify a situation ("am I idle?", "is David sad?").
R3  It YIELDS immediately and completely to any commanded state (WO-035).
R4  Removing the brain entirely would not change whether it fires.

Fail any one ⇒ it is a DECISION and must route through the brain.
```

**Applied — the WO-086 Designer audit, already confirmed by the Architect (2026-08-10):**

| Behaviour | Verdict | Why |
|---|---|---|
| `EloIdleBehaviour` mouse-idle "go calm" **decision** | **ROUTE THROUGH BRAIN** | Fails R2 — it classifies idleness and picks an emotional state |
| `EloIdleBehaviour` idle-breathing wobble | **KEEP as reflex** | Passes R1–R4; neutral aliveness |
| `EloIdleBehaviour` detection + publish + yield-to-commanded guard | **KEEP** | Sensing and reporting are the body's job (§5.1.2) |
| `EloEmojiReact` | **REVIEW (open)** | If it *interprets* to pick a valence → fails R2, brain owns it. If it *mirrors* an already-decided emotion → passes, keep |
| `ArmWave` / `ArmReach` | **KEEP (event-commanded)** | Executors — but confirm `autoTest` self-fire toggles are OFF in build (a self-firing test hook is a local decider) |
| `HeadLook` gaze-follow | **KEEP** | Reflex; yields to brain |
| `EloGunVisibility` | **KEEP** | Visual reflex |
| `BodyGlow` · `BrainCluster` · `OneBrainPanel` · `AmbientVfx` | **KEEP** | Reflect brain state; decide nothing |
| `PresenceEngine` · `EloPresenceSignal` | **KEEP** | Correct UP emitters |
| `Receiver` | **KEEP** | Executor |

**Rule (MUST):** the reflex list is **enumerated and reviewed**, never assumed. A new local
behaviour is presumed a decision until it passes R1–R4 in review. The WO-086 audit list is the
standing register; adding to it is a canon-adjacent act, not a code-review nicety.

## 5.5 ACK before belief — the chain

The loop's most important instance, and the one that is actually built. From
`SITUATED_SELF_v1_assembly.md` (and it is exactly the CA's "self-aware sit loop"):

```
intention → capability check → command (DOWN) → body acts → ACK (UP) → pose update →
self-model update → THEN speech
```

- Before ACK: *"I'm attempting to sit…"* (tier POSSIBLE — Ch.3)
- After ACK: *"I'm sitting with you."* (tier VERIFIED)
- On fail/timeout: *"I tried to sit, but my movement system didn't confirm it."* (honest, in system
  terms — never silence, never a claim)

**Rule (MUST):** the self-model is updated **from the ACK**, not from the command. A commanded state
is `pending` in the self-model until confirmed. This is what makes `pose_tier: "verified" if
pose_acked else "last-known"` in `runtime/the_moment.py` correct rather than decorative.

**Rule (MUST):** an ACK is a *report*, and reports go UP through the normal channel. There is no
special ACK back-door that skips assembly — the confirmation lands in the next
`UnifiedCognitiveState` like everything else.

## 5.6 Live status (verified — stated honestly)

**Built and working:**

- **DOWN leg.** One plan → `EmbodimentState` → surfaces, incl. `robot_led_state` and
  `motion_command`, all from the same plan (`runtime/spine/spine.py::build_embodiment_state`,
  `_LED_FROM_EMOTIONAL_STATE`). ADR-Exec-002 in code.
- **ACK chain.** The sit chain (WO-041) with pending/confirmed/timeout wording; `BodySchema`
  carries `pending_sit`, `sit_pending_since`, `queued_intent`
  (`runtime/cognitive_snapshot.py`); `pose_acked` drives the epistemic tier
  (`runtime/the_moment.py`).
- **Commanded owns the body** (WO-035). `EloIdleBehaviour` already yields to `SitHeld`.
- **Some UP perceptions land.** Presence/`conversing`/`last_user_ts` (WO-064 BP-1), perch/surface
  state (`blender_bridge/state_writer` → `surface_type` in the snapshot), Chrome scope (WO-057),
  file-drop (`desktop/file_drop_handler.py`).

**Not built / open (PENDING — do not claim):**

- **The UP-relay rule is not enforced anywhere.** There is no test, no bus rule, and no review gate
  asserting that a body perception must relay UP. Canon now says it must (this chapter); nothing
  checks it.
- **WO-086 is OPEN and gated.** Steps 1–2 (emit the idle EDGE events UP; retire the local calm
  decision) **await David's greenlight** — they touch the sensitive DesktopBuddy avatar file and
  change autonomous behaviour. Step 3 (the audit) is DONE. Sequencing is confirmed and hard:
  *"Designer emit+retire lands WITH the Builder brain-decide half, NEVER before (retire-first =
  idle-does-nothing regression)."*
- **The idle repertoire does not exist yet.** WO-086 confirmation (c): the response to idle is not
  always "calm" — the repertoire (calm · look-around · stretch · glance at an app · wander · soft
  utterance) is the Builder's ambient engine, extending WO-066. Until it exists, routing idle
  through the brain has nowhere good to route *to*.
- **`EloEmojiReact` verdict is unresolved** (§5.4) — needs the closer read.
- **The robot body is not in the loop at all yet.** Vol VII's law is written to be embodiment-neutral
  precisely so the robot inherits it rather than re-litigating it. RESERVED hardware scope
  (force/magnetics/pump/thermal) keeps LG-2 regardless (Ruling XXIII).

## 5.7 Contract (the Embodiment Loop)

```
Contract:
  name:            EmbodimentLoop        # a LAW binding every embodiment, not a faculty
  binds:           desktop avatar · game · robot · phone · AR · exhibition · hologram

MUST (body side):
  L1  Relay every perception UP on the canonical event channel, as a typed edge/state report.
  L2  Execute commands received DOWN on the canonical action channel.
  L3  ACK every commanded action — success, failure, or timeout. Silence is not an outcome.
  L4  Yield instantly and completely to any commanded state (WO-035).
  L5  Hold ONLY reflexes that pass R1–R4 (§5.4), and only from the enumerated register.

MUST NOT (body side):
  N1  Select a behaviour.                 N2  Classify or interpret a situation.
  N3  Consume a perception locally without relaying it.
  N4  Maintain private state the brain cannot read (ADR-Exec-002).
  N5  Self-fire a commanded behaviour (incl. leftover test/auto hooks).

MUST (brain side):
  M1  Assemble every relayed perception into the ONE frozen state (Ch.2) before deciding.
  M2  Decide the response to a body perception in the ONE decision (Ch.1) — never a
      dedicated per-perception handler that decides on the side.
  M3  Believe an action only on ACK (§5.5); speak only after belief (Ch.3).
  M4  Drive autonomous and commanded behaviour through the SAME capability (§5.1.7).
  M5  When a perception arrives that the brain has no policy for, decide SILENCE/no-op
      explicitly — never fall back to letting the body handle it.

Failure Modes:
  - condition: a body perception is dropped/never relayed
    fallback:  the brain simply does not know it — and must NOT act as if it did (Ch.3 UNKNOWN).
               A dropped relay is a test failure, not a degraded-but-fine state.
  - condition: no ACK within timeout
    fallback:  the state stays pending; eLo reports the non-confirmation (§5.5). Never claims it.
  - condition: the brain is unreachable (backend down)
    fallback:  the body holds its last commanded state and its reflexes. It does NOT improvise
               behaviour to fill the silence. A still eLo is honest; an improvising one is a
               second brain.
  - condition: a local driver is discovered deciding
    fallback:  it is a canon violation. Route it through the brain or justify it under R1–R4
               and enter it in the register.
```

## 5.8 Acceptance Tests

### Functional
```
FT-1  Perception relays UP
  Given the mouse goes idle past threshold, Then a typed edge event ({type:'user_idle',
  idle_secs, _ts}) appears on the UP channel — and NO local behaviour was selected.

FT-2  Brain decides, body executes
  Given the idle perception arrives, When the turn runs,
  Then the chosen idle behaviour appears in the ONE plan and travels DOWN the normal action
  path; the body plays what it was told.

FT-3  No local self-trigger
  Given the brain is running, Then no body behaviour with intent/valence fires without a
  preceding DOWN command. (WO-086 DoD, verbatim: "no local self-trigger".)

FT-4  Commanded owns the body
  Given a commanded sit and an autonomous urge, Then the commanded state holds; the
  autonomous behaviour yields.

FT-5  ACK before belief
  Given a sit command, Then the self-model shows pending until ACK; only after ACK does
  pose become verified and "I'm sitting" become sayable (Ch.3 FT-5).

FT-6  Reflex register
  Given each local behaviour in the register, Then it passes R1–R4; any that does not is
  listed as route-through-brain with an owner.
```

### Stability
```
ST-1  Brain unreachable
  Given the backend is down, Then the body holds last commanded state + reflexes only;
  it invents no behaviour.

ST-2  Retire-with, never retire-first
  Given the local calm driver is retired, Then the brain-decide half is live in the same
  change; idle never becomes a no-op regression. (WO-086 confirmation (d).)

ST-3  Loop latency is honest
  Given the round trip is slow, Then eLo is slower — not locally clever. No behaviour is
  moved back into the body for responsiveness.

ST-4  Cross-embodiment
  Given the same perception on desktop and on robot, Then it relays UP identically and the
  brain decides once; only the actuators differ (Invariant #1).
```

### Integration
```
IT-1  Closed loop, end to end (the WO-086 test)
  Inject an idle signal UP → assert it lands in UnifiedCognitiveState → assert the Executive
  emits an idle directive in the ONE plan → assert the body plays it → assert no local
  self-trigger occurred at any point.

IT-2  Audit compliance
  Given the enumerated local-driver register, Then every entry has a verdict
  (keep-as-reflex / route-through-brain) and no unlisted local decider exists in the build.

IT-3  Composition with WO-041 + WO-035
  Assert the loop composes: perception UP → decide → command DOWN → ACK UP → belief → speech,
  with commanded state owning the body throughout. (David's explicit ask in the verbatim source.)
```

## 5.9 Wiring to Live Anchors

- **UP channel:** `unity_events.json` (the presence emitter extended with typed edge events —
  `{type:'user_idle', idle_secs, _ts}` / `{type:'user_active', _ts}`, per WO-086 confirmation (b):
  *"REUSE + EXTEND, do NOT add a parallel contract"*). Also `blender_bridge/state_writer` (perch/
  surface), `desktop/file_drop_handler.py`, presence/`conversing` (WO-064 BP-1).
- **DOWN channel:** `blender_state.json` — the same action path meditation/sit/move already use;
  Unity `Receiver` executes.
- **Assembly:** `runtime/cognitive_snapshot.py` (`BodySchema`, `surface_type`,
  `surface_affordances`, `pending_intentions`) — where UP perceptions must land.
- **Decision + projection:** `runtime/executive.py` → `runtime/spine/spine.py`
  (`build_embodiment_state`, `_LED_FROM_EMOTIONAL_STATE`).
- **ACK/self-model:** `runtime/the_moment.py` (`pose_acked` → `pose_tier`),
  `self/elo_self_model.py`, the WO-041 sit chain.
- **Unity side (Designer lane — Architect does not edit):** `EloIdleBehaviour` (detection + publish +
  yield guard KEEP; the calm *decision* RETIRE), `EloEmojiReact` (REVIEW), `PresenceEngine` /
  `EloPresenceSignal` (UP emitters), `Receiver` (executor), `ArmWave`/`ArmReach` (confirm autoTest
  self-fire OFF).
- **Ambient repertoire (Builder lane):** extends WO-066 — the set of idle responses the brain may
  choose from.

## 5.10 Cross-Volume Interaction

| Volume | Boundary |
|---|---|
| **XVI Ch.3 (Faculty Bus)** | The UP leg travels the bus. The audit's recommendation was to write this rule into XVI Ch.3 as a MUST; it is stated here as law and XVI Ch.3 should carry the routing MUST that enforces it. Both, not either. |
| **XVI Ch.4** | Owns the DOWN projection ("no body re-decides", one plan → many surfaces). This chapter owns the UP relay and the reflex line. Together they close the loop. |
| **XII (Perception)** | Produces the transformed observations that the UP leg carries. Perception *transforms*; it does not decide either. |
| **XI (Motor Cortex)** | The DOWN leg's executor. Capability, not decision. |
| **XIII (Presence)** | Presence is a *cognitive state*, not an animation — which is this chapter's rule stated for one domain: the state is decided in the brain; movement only expresses it. |
| **VII Ch.3** | ACK is what promotes an action claim to VERIFIED. Without the UP leg, eLo can never truthfully say he did anything. |
| **VII Ch.4** | Body intents are committed here and satisfied by ACKs arriving UP. Absence-awareness (a body perception) feeds the internal lane. |
| **XXVIII (Learning)** | Verified consequences arrive UP. No UP leg ⇒ no verified consequences ⇒ nothing legitimate to learn from (ADR-Exec-005). |

## 5.11 Open Questions (for CA / David)

```
REQUIRES DECISION
  OQ-VII-5  RATIFY THE REFLEX TEST R1–R4 (§5.4). The verdicts in the table are already
            Architect-confirmed against WO-086; the four-part TEST that generalises them is
            the Architect's construction. Confirm it, so future local behaviours are judged
            by rule rather than case-by-case. Also: close the EloEmojiReact verdict
            (interprets valence ⇒ brain; mirrors decided emotion ⇒ keep).

  Q5-a      Should `brain > body > brain` be logged as its own ADR (extending ADR-Exec-003),
            given David's own note in WO-086: "Worth ratifying as a One-Brain invariant
            alongside the Situated-Self invariant"? Recommend YES — an invariant that lives
            only in a volume chapter is one reorganisation away from being lost again.
            Owner: David (L3) — it is an identity-level rule about what eLo IS.

  Q5-b      WO-086 greenlight (David). Steps 1–2 change autonomous behaviour and touch the
            DesktopBuddy avatar. Still awaiting. Note the hard sequencing: emit+retire lands
            WITH the brain-decide half, never before.

  Q5-c      Brain-unreachable posture (§5.7 failure mode). Proposed: the body holds last
            commanded state + reflexes and improvises nothing. Confirm — it is a feel call
            (a still eLo vs a fidgeting one) and it is the honest option.

  Q5-d      Does the reflex allowance differ for the ROBOT? A physical body has real safety
            reflexes (stop on force limit) that MUST be local for safety reasons. Proposed:
            safety reflexes are permitted local and are the ONLY category exempt from R1–R4 —
            and they report UP regardless. RESERVED scope: David L3 + LG-2.
```

## 5.12 References

- **`_intake/SOURCE_2026-08-10_brain_body_brain_loop.md` — VERBATIM PRIMARY SOURCE.** Quoted in full
  at §5.0. Canon references it; it is never paraphrased into shorter form (Rule 4b).
- `engineering/work_orders/WO-086_Mouse_Idle_Through_Brain.md` — the first application; the Designer
  local-driver audit + the four Architect confirmations (a)–(d); the sequencing rule.
- `DECISION_LOG.md` — ADR-Exec-003 (Embodied Truth: *Thought → Decision → Body → Confirmation →
  Belief → Speech*), ADR-Exec-001 (ACK before claim), ADR-Exec-002 (no modality invents private
  state), D-CONTINUITY.
- `ARCHITECTURAL_PRINCIPLES.md` — Invariant #1; Embodied Truth; Embodied Cognition; Affordance
  Before Action; Presence-is-a-cognitive-state; "Autonomous and commanded are one capability";
  "Life emerges from continuity, not complexity — never script the appearance of life."
- `Volume_XVI/04_…` §4.3 (the DOWN half, already canon) · `Volume_XVI/03_…` (the channel).
- `SITUATED_SELF_v1_assembly.md` — the self-aware sit loop (§5.5).
- `AUDIT_INTENT_core_brain_2026-08-10.md` — *"The UP leg of `brain > body > brain` is absent…
  This is the natural home and it is empty."*
- Code: `runtime/spine/spine.py` (`build_embodiment_state`), `runtime/cognitive_snapshot.py`
  (`BodySchema`), `runtime/the_moment.py` (`pose_acked` → tier), `blender_bridge/state_writer.py`,
  `desktop/file_drop_handler.py`.

---
```
Chapter 5 — brain > body > brain — The Closed Loop
Status: READY FOR REVIEW
CANONISATION: David's principle is moved out of WO-086 (which will close) into canon.
  His words are reproduced VERBATIM at §5.0 and referenced, never paraphrased (Rule 4b).
Grounded in live code: DOWN projection from one plan · sit-chain ACK + pending BodySchema ·
  pose_acked → epistemic tier · commanded-owns-body (EloIdleBehaviour yields to SitHeld) ·
  existing UP perceptions (presence/conversing, perch/surface, Chrome scope, file-drop)
Flagged PENDING: the UP-relay rule is unenforced (no test, no bus MUST); WO-086 steps 1–2
  AWAIT DAVID GREENLIGHT; the idle repertoire does not exist; EloEmojiReact verdict open;
  the robot body is not in the loop yet
Flagged INVENTION: the R1–R4 reflex test (OQ-VII-5); the brain-unreachable posture (Q5-c)
Loop Contract (L1–L5 · N1–N5 · M1–M5): Included · Acceptance Tests: FT×6 ST×4 IT×3
Open Questions: 5 (OQ-VII-5, Q5-a, Q5-b, Q5-c, Q5-d)
Implementation: PARTIAL
```

READY FOR REVIEW
