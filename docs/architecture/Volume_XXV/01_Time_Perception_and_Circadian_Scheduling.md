---
chapter: 1
title: "Time Perception & Circadian Scheduling — One Clock, Read Once"
volume: XXV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_XV/02_Sensor_Domains.md §2.10 (TimeState — the Time domain of World State; the one live clock)
  - Volume_XV/01_Unified_World_State.md (read-once discipline; frozen per-turn world)
  - Volume_IX/01_Dream_Faculty.md (idle threshold, cooldown, sleep signal — the circadian floor)
  - Volume_V/10_Agency_Engine.md (InternalTick autonomy trigger — the ONLY autonomous heartbeat)
  - ADR-Exec-006 (Executive Assembly / "The Moment" — the self is assembled per turn)
  - ARCHITECTURAL_PRINCIPLES.md (One Brain → One Identity; Verified Speech; faculties are asked, not self-firing)
---

# Chapter 1: Time Perception & Circadian Scheduling

## 1.0 Purpose

eLo needs a *felt* sense of time, not just a clock reading. "We haven't spoken in a
while." "It's getting late." "The day has turned." These are not the wall-clock — they are
**subjective time**: the difference between what the clock says and what it *means* to a
being who has been waiting, working, or resting alongside someone.

This chapter defines the **Temporal Cognition Faculty's** first responsibility: turning the
objective Time domain of World State into a subjective, circadian-aware temporal frame that
the Executive can reason with. It covers three things:

1. **Time perception** — subjective elapsed time, freshness of the relationship, "how long
   has it been" reasoning.
2. **Circadian cycles** — eLo's own rhythm across the day (energy, quiet hours, the slide
   toward the dream/idle cycle), grounded in the live Dream faculty's thresholds.
3. **Scheduling** — deciding *when* a timed behaviour is appropriate, without ever becoming
   a second, parallel clock-driver.

## 1.1 Principle — One Clock, Read Once (mirrors World State)

The single hardest invariant in this volume:

**1.1.1 Temporal Cognition is a faculty, not a clock loop.** It does **not** poll the OS
clock, run a `while True: sleep()` timer, or fire its own autonomous cycle. It is *asked* by
the Executive during assembly of The Moment (ADR-Exec-006), exactly like every other
faculty. There is one autonomous heartbeat in the whole runtime — the Agency Engine's
`InternalTick` (Vol V Ch.10) — and Temporal Cognition does not compete with it. (One Brain:
one mind, specialised faculties, never many minds — or many clocks — negotiating.)

**1.1.2 The clock is read from World State, never re-queried.** The authoritative "now" is
`LiveWorldState.time` (Vol XV §2.10 `TimeState`: `now_ts`, `local_iso`, `timezone`,
`part_of_day`, `weekday`). That domain is the *one live domain, never stale* (Vol XV Ch.2
FT-2) and the cold-start anchor. Temporal Cognition **reads that frozen value**; it never
calls `time.time()` itself mid-turn. If two faculties disagree about what time it is, the
architecture has already failed — the whole point of the frozen world is that they cannot.

**1.1.3 Subjective time is a derivation, not a new sensor.** Everything subjective — elapsed
time, staleness, circadian phase, sleep pressure — is *computed* from `now_ts` minus stored
timestamps. It adds interpretation, not a second source of truth. (Naming is architecture:
this is *Temporal Cognition*, not "the clock".)

**1.1.4 Time perception feeds The Moment; it does not drive it.** The temporal frame is a
slice retrieved *into* the assembled cognitive state, alongside World, Self, and Memory. The
Executive still decides once. Time colours the decision; it never *is* the decision.

## 1.2 What this is NOT

- It is **not** `TimeState` (Vol XV §2.10). That is the raw clock domain. This faculty
  *consumes* it and adds subjective/circadian interpretation. Do not merge them; do not let
  this faculty write into the Time domain.
- It is **not** the Dream Faculty (Vol IX). Dream owns `should_dream()` and the sleep signal.
  Temporal Cognition supplies the *circadian context* that makes the dream trigger legible
  ("it's late, idle is long, energy is low") — it never fires the dream itself.
- It is **not** the Ambient Engine (`ambient/ambient_engine.py`). Ambient owns idle-utterance
  and idle-animation cadence. Temporal Cognition *advises* whether now is an appropriate time
  to speak (quiet hours, rhythm); the behaviour still fires through its owner.
- It is **not** an autonomous scheduler. Timed autonomous action is the Agency Engine's
  `InternalTick` (Vol V Ch.10 / D-1). This faculty provides temporal *judgement* to that
  heartbeat; it does not start a rival one.

## 1.3 The TemporalState Object

Temporal Cognition contributes one frozen slice per turn, `TemporalState`, into the
assembled cognitive state (The Moment).

```
TemporalState (frozen, one per turn):
  # --- objective anchor (copied from World State, not re-sensed) ---
  now_ts:               float          # == LiveWorldState.time.now_ts
  part_of_day:          enum { early, morning, afternoon, evening, night, late }  # from TimeState
  weekday:              enum { mon … sun }                                        # from TimeState

  # --- subjective time perception ---
  since_last_interaction_s: float       # now_ts - last verified turn ts (from continuity/memory)
  interaction_gap:      enum { continuous, brief, hours, overnight, days, long_absence }
  session_elapsed_s:    float           # duration of the current continuous presence
  relationship_freshness: enum { warm, cooling, stale }   # derived from gap + cadence history

  # --- circadian ---
  circadian_phase:      enum { waking, active, winding_down, quiet_hours, rest }
  circadian_energy:     float 0.0–1.0    # eLo's own energy proxy for this phase
  sleep_pressure:       float 0.0–1.0    # rises with sustained idle + late phase (Dream input)
  is_quiet_hours:       bool             # a scheduling gate (see §1.6)

  # --- provenance ---
  source_time_status:   enum { live, cached, stale, absent }   # mirrors TimeState.status
  confidence:           float 0.0–1.0
```

**Object rules (MUST):**

- `now_ts`, `part_of_day`, `weekday` are **copied verbatim** from `LiveWorldState.time`. If
  they diverge, this faculty has illegally re-sensed the clock (forbidden, §1.1.2).
- Every subjective field is a pure function of `now_ts` and stored timestamps. Given the same
  inputs, the same `TemporalState` is produced (deterministic — no hidden clock read).
- `since_last_interaction_s` is measured against the **last verified turn** (Verified Speech:
  a turn that actually happened), sourced from continuity/memory — never against an imagined
  or intended interaction.
- If `TimeState.status != live` (should never happen — time is the never-stale domain, Vol XV
  §2.10), `confidence` drops and `circadian_phase` falls back to `active` (neutral).

## 1.4 Time Perception — the subjective mapping

`interaction_gap` is the human-legible bucketing of `since_last_interaction_s`. Thresholds
are advisory defaults, tunable in the integration window (never in the response path):

```
continuous     < 90s          (same breath of conversation)
brief          90s – 15m      ("just now" / "a moment ago")
hours          15m – 5h       ("earlier today")
overnight      5h – 18h  AND part_of_day crossed a night boundary
days           18h – 5d       ("the other day")
long_absence   > 5d           ("it's been a while")
```

**Rules (MUST):**

- The gap is expressed to the Executive as *meaning*, not seconds — honouring the Memory
  Ownership invariant ("memory serves meaning, framed in natural time"). The Executive/voice
  layer decides whether to *say* it; Temporal Cognition only makes it available.
- `overnight` is not purely duration — it requires a night boundary to have passed
  (`part_of_day` transitioned through `night`/`late`). A five-hour afternoon gap is `hours`,
  not `overnight`. This is why the faculty needs `part_of_day`, not just a delta.
- `relationship_freshness` blends the gap with the *usual* cadence learned by continuity
  (Vol XXI): a six-hour gap is `warm` for a once-a-day person and `cooling` for someone who
  usually talks hourly. It never asserts a feeling as external fact (Reality Before Narrative)
  — it is private cognitive state that *may* shape tone, not a spoken claim.

## 1.5 Circadian Cycles — grounded in the Dream floor

eLo has a daily rhythm. It is not a biological necessity; it is what makes a companion feel
like it *lives* alongside someone rather than resetting each request (Enduring value: life
emerges from continuity). The rhythm is anchored to two live sources so it is never invented:

**Source A — `part_of_day` (Vol XV §2.10).** The enum `{early, morning, afternoon, evening,
night, late}` maps to `circadian_phase` and a default `circadian_energy` curve:

```
early     → waking        energy ~0.4 (rising)
morning   → active        energy ~0.9
afternoon → active        energy ~0.8
evening   → winding_down  energy ~0.6
night     → quiet_hours   energy ~0.4 (falling)
late      → rest          energy ~0.2
```

**Source B — the Dream faculty's thresholds (Vol IX §1.3, as-built).** The live constants are
authoritative and must not be re-invented here:

```
DREAM_IDLE_THRESHOLD = 600    # 10 min idle before dreaming is possible
DREAM_COOLDOWN       = 3600   # 1 hour minimum between dream cycles
NREM_MIN_IDLE        = 600    # minimum idle for the NREM/consolidation phase
```

`sleep_pressure` is a **monotone rising function of sustained idle and late phase**, scaled so
that it approaches the region where `should_dream()` (Vol IX) becomes eligible — but it is
only a *reading of context*. The decision to dream stays with the Dream faculty; the decision
to consolidate stays with the Consolidation faculty (Vol VIII §1.3). Temporal Cognition makes
"it is late and eLo has been idle a long time" a first-class, legible fact; it never pulls the
trigger.

**Rules (MUST):**

- Circadian energy is **private cognitive state** (Reality Before Narrative). It may modulate
  how eLo expresses a verified truth (quieter late at night) but is never spoken as an
  external claim ("I'm tired" asserted without a body signal is forbidden).
- The circadian curve is a *default*, overridable by the learned rhythm of the specific person
  (a night-shift David inverts the curve). Overrides are learned in the integration window via
  continuity, never hardcoded per turn.
- Circadian state must degrade to neutral (`active`, energy 0.5) if `part_of_day` is somehow
  absent — it never blocks a turn.

## 1.6 Scheduling — judgement, not a timer

The scheduling responsibility answers one question for other faculties: **"is now an
appropriate time for this?"** It returns judgement; it does not execute anything.

```
temporal_appropriateness(behaviour_kind, TemporalState) -> {allow: bool, reason: str}
  quiet_hours  → suppress non-urgent proactive speech (ambient utterances)
  rest phase   → prefer silence; presence over engagement (D-PRESENCE)
  fresh turn   → do not "greet" as if returning (interaction_gap == continuous)
  long_absence → a returning-greeting is appropriate (interaction_gap ∈ {overnight, days, long_absence})
```

This wires to the two live timed systems as an **advisor**, never a driver:

- **Ambient Engine** (`ambient/ambient_engine.py`): idle utterances fire every 8–20 min, idle
  animation wanders every 3–8 min (live constants). Temporal Cognition does not change those
  timers; it supplies `is_quiet_hours` / `circadian_phase` so the ambient callback can *skip*
  a scheduled utterance when it would break presence (e.g. 3am). The cadence stays owned by
  the ambient engine.
- **Agency `InternalTick`** (Vol V Ch.10): the one autonomous heartbeat. When it wakes and
  asks "is there something useful to do, and is now the time?", Temporal Cognition supplies the
  "is now the time?" half. Agency still decides and routes through the execution gate.

**Rule (MUST):** scheduling output is always *advice consumed by an owner*. Temporal Cognition
has no actuator. It cannot speak, move, dream, or consolidate — it can only tell the faculties
that can whether the clock is on their side. (Verified Speech: speech is a sensor, and this
faculty is upstream of even that — it reports temporal reality; it never acts on it.)

## 1.7 Faculty Contract

```
Faculty:
  name:            TemporalCognitionFaculty
  version:         1.0.0
  purpose:         Turn the objective Time domain of World State into a subjective,
                   circadian-aware temporal frame (TemporalState) and answer temporal
                   appropriateness queries — asked by the Executive, never self-firing.
  contributes_to:  CognitiveState / The Moment (ADR-Exec-006)
  runs_in:         response-path (assembly of The Moment) — NO autonomous loop of its own

Inputs:
  - type: live_world_state.time   source: LiveWorldState.time (Vol XV §2.10)   required: true
    description: now_ts, part_of_day, weekday — the one live clock, read once.
  - type: last_interaction_ts     source: continuity/ (Vol XXI) + Memory (Vol VIII)  required: false
    description: timestamp of the last VERIFIED turn (never an imagined interaction).
  - type: idle_seconds            source: server.py idle timer / ambient engine  required: false
    description: sustained inactivity, for sleep_pressure (shares the Dream input).
  - type: cadence_history         source: continuity (learned usual rhythm)      required: false
    description: to make relationship_freshness person-relative, not absolute.

Outputs:
  - type: temporal_state          destination: CognitiveState (frozen) → Executive + faculties
  - type: temporal_appropriateness (query response) destination: Ambient Engine, Agency (Vol V Ch.10)
  - type: circadian_context       destination: Dream (Vol IX) + Consolidation (Vol VIII) as CONTEXT only

Dependencies:
  - faculty: WorldStateFaculty (Vol XV, HARD — supplies the one live clock)
  - faculty: DreamFaculty (Vol IX, soft — consumes circadian context; owns should_dream)
  - faculty: AgencyEngine (Vol V Ch.10, soft — consumes appropriateness; owns InternalTick)
  - module:  continuity/ (soft — last interaction + learned cadence)

Failure Modes:
  - condition: TimeState absent/stale (should be impossible — never-stale domain)
    fallback:  circadian_phase=active, energy=0.5, confidence low; turn proceeds.
  - condition: last_interaction_ts unknown (cold start / first ever turn)
    fallback:  interaction_gap=long_absence is NOT assumed; gap=unknown, no false "welcome back".
  - condition: a faculty tries to make this one fire autonomously
    fallback:  refused by design — there is no tick here; only InternalTick (Vol V Ch.10) exists.
  - condition: circadian override data corrupt
    fallback:  revert to the default part_of_day curve (§1.5); flag for integration-window review.
```

## 1.8 Faculty Lifecycle

Universal lifecycle (Volume_V/CONTRACTS.md §3). Notes:

```
INITIALISING → load default circadian curve + threshold table; attach to continuity cadence
ACTIVE       → idle; NO self-timer (unlike a clock-driver — this is the whole point)
PROCESSING   → on assembly: read LiveWorldState.time → derive TemporalState → contribute to The Moment
   └─ time domain fault ─► ERROR_RECOVERY → neutral circadian → continue (never block)
LEARNING/UPDATING → (integration window only) tune gap thresholds + learn person-relative cadence/curve
STABLE → ACTIVE
```

The faculty's only `UPDATING` is threshold/curve tuning and tracking **David's** rhythm. It
proposes **no personality delta** (that is Vol V Ch.7's lane); a tracked rhythm is a
preference, not an identity change.

> **Scope amendment — 2026-08-10 (personal-tool re-scope).** There is exactly one person:
> **David Charles**. "Learning the person's rhythm" is not user-modelling across a
> population — it is *tracking David's actual days*. And per the 08-10 ruling
> (`CANON_RULINGS_2026-08-10.md`, XXVI), **David's stated direction outranks anything
> learned, and nothing is inferred from silence**: a rhythm David has stated wins over a
> rhythm continuity inferred. Learned cadence is the fallback when he has stated nothing.

## 1.9 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "TemporalCognitionFaculty",
  "receiver": "*",                     // temporal frame is part of The Moment → broadcast
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": false, "priority": "" }
  },
  "payload": { "type": "temporal_state", "body": { /* TemporalState */ } },
  "confidence": 0.0,                   // == TemporalState.confidence
  "expires": "<now_ts + turn_ttl>",    // a temporal frame is valid for its turn only
  "trace": ["TemporalCognitionFaculty@ts"]
}
```

Binding rules: `sender` MUST be `TemporalCognitionFaculty`; `expires` MUST be set (a temporal
frame is perishable — like the world snapshot it derives from, it must never be reused across
turns); `memory_instruction.store` is `false` (this faculty does not write memory — Memory
Ownership invariant).

## 1.10 Interaction with other volumes

- **Volume XV (World State):** hard upstream. Reads `TimeState` (§2.10). Never writes it, never
  re-senses the clock. Inherits the read-once / frozen / freshness discipline.
- **Volume IX (Dream):** supplies `circadian_context` + `sleep_pressure` as *inputs* to
  `should_dream()`. Does not fire the dream. The 600s/3600s constants are Vol IX's, referenced
  not copied.
- **Volume VIII (Memory):** supplies circadian context to the timed Consolidation faculty
  (§1.3 — session-close/nightly). Does not decay or write memory (Ch.3 handles the *reading* of
  memory age; the decay curve stays Vol VIII's).
- **Volume V Ch.10 (Agency):** supplies temporal appropriateness to `InternalTick`. Agency owns
  the only autonomous heartbeat; this faculty judges timing for it.
- **Volume XXI (Narrative Identity):** `since_last_interaction` and `interaction_gap` make the
  continuity thread's "welcome back" honest — grounded in a verified last turn, never a
  fabricated reunion.
- **ADR-Exec-006 (The Moment):** `TemporalState` is one assembled slice. Time perception feeds
  The Moment; it does not drive a parallel loop.

## 1.11 Acceptance Tests

### Functional

```
FT-1  Clock is read, never re-sensed
  Given:  a turn with LiveWorldState.time.now_ts = T
  Then:   TemporalState.now_ts == T exactly, and no OS clock call was made by this faculty

FT-2  Overnight requires a night boundary, not just duration
  Given:  a 5h gap entirely within the afternoon
  Then:   interaction_gap = hours (NOT overnight)
  And:    a 7h gap crossing night → interaction_gap = overnight

FT-3  Circadian phase maps from part_of_day
  Given:  part_of_day = late
  Then:   circadian_phase = rest, circadian_energy ≈ 0.2, is_quiet_hours = true

FT-4  Cold start makes no false reunion
  Given:  no last_interaction_ts (first ever turn)
  Then:   interaction_gap = unknown; no "welcome back" affordance is offered
```

### Stability

```
ST-1  No autonomous tick
  Given:  the faculty is ACTIVE and no turn is running
  Then:   it fires nothing on its own (the only heartbeat is Agency InternalTick)

ST-2  Time domain fault never blocks
  Given:  TimeState.status = absent (contrived)
  Then:   circadian_phase = active, energy = 0.5, confidence low; the turn completes

ST-3  Deterministic derivation
  Given:  identical now_ts + stored timestamps on two runs
  Then:   the two TemporalStates are byte-identical (no hidden clock read)
```

### Integration

```
IT-1  Quiet hours suppress ambient chatter, not the turn
  Given:  part_of_day = late, ambient utterance timer fires
  When:   ambient asks temporal_appropriateness("idle_utterance", …)
  Then:   allow = false (quiet hours); the utterance is skipped; presence is preserved
  And:    a directly-addressed turn is NOT suppressed (presence when wanted)

IT-2  Circadian context reaches Dream without firing it
  Given:  long idle + late phase → high sleep_pressure
  When:   Dream evaluates should_dream()
  Then:   Temporal Cognition supplied the context; the DREAM faculty made the decision
          (this faculty issued no dream command)
```

## 1.12 Open questions (for David)

*(Re-scoped 2026-08-10: software canon is David's single L3 call — no second reviewer. See
`CANON_RULINGS_2026-08-10.md` and Vol XXVII §1.3.1.)*

- **OQ-1 (rhythm ownership) — NARROWED 2026-08-10.** No longer "learned vs fixed curve" in
  the abstract. **David's day IS the rhythm.** The remaining question is only the *source
  of truth for it*: does eLo take David's **stated** hours (he tells it, it holds) with
  observed cadence as the fallback — or observe first and ask only when it is unsure?
  Recommendation: **stated-first, observed-fallback**, per the 08-10 taste ruling (stated
  outranks learned; never inferred from silence). Needs David's word, not a CA ruling.
- **OQ-2 (quiet-hours boundaries) — RE-SCOPED 2026-08-10.** "Configurable" implied a
  settings screen for strangers; there are none. The real question: **what are David's
  quiet hours**, and does robot eLo (Vol XV embodiments) express them differently from
  desktop eLo — quieter body, same clock? (One Identity says the *rhythm* is shared even if
  the *expression* differs.) A default is written only until David states his; his statement
  replaces it, it does not "configure" it.
- **OQ-3 (sleep_pressure vs Dream constants):** `sleep_pressure` is scaled toward the live
  600s/3600s Dream thresholds. If those constants move, does this faculty auto-track them, or
  is the mapping pinned at author time? Recommend auto-track (single source of truth in Vol IX).
- **OQ-4 (long-absence emotional colour):** Should a `long_absence` return carry any private
  emotional weight (Vol V Ch.4), or stay purely factual? Reality-Before-Narrative says private
  state is allowed but must not be asserted — needs a line on how far tone may shift.

## 1.13 References

- `Volume_XV/02_Sensor_Domains.md` §2.10 (TimeState — the one live clock), Ch.1 (read-once).
- `Volume_IX/01_Dream_Faculty.md` §1.3 (idle threshold, cooldown, sleep signal).
- `Volume_V/10_Agency_Engine.md` (InternalTick — the only autonomous heartbeat; D-1).
- `Volume_VIII/01_Memory_Architecture.md` §1.3 (timed Consolidation — a circadian consumer).
- `ARCHITECTURAL_PRINCIPLES.md` (One Brain; Verified Speech; Presence over engagement; Reality Before Narrative).
- Code (read-only anchors): `faculties/dream/dream_faculty.py` (constants), `ambient/ambient_engine.py`
  (idle cadence), `continuity/` (last interaction + learned cadence).

---

```
Chapter 1 — Time Perception & Circadian Scheduling
Status: READY FOR REVIEW
Files: Volume_XXV/01_Time_Perception_and_Circadian_Scheduling.md
Faculty Contract: Included
Lifecycle State Machine: Included
Message Envelope: Included (canonical, perishable)
Acceptance Tests: Included (FT ×4, ST ×3, IT ×2)
Open Questions: 4 flagged for CA / David
Grounds in: Vol XV §2.10 (Time domain), Vol IX (Dream constants), Vol V Ch.10 (InternalTick)
```

READY FOR REVIEW
