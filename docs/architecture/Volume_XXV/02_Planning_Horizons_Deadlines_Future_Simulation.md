---
chapter: 2
title: "Planning Horizons, Deadlines & Future Simulation — Reasoning Forward in Time"
volume: XXV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_V/10_Agency_Engine.md (goal tiers immediate→identity; planning JSON contract; InternalTick)
  - Volume_XV/02_Sensor_Domains.md §2.8 (CalendarState — verified deadlines), §2.10 (TimeState — now)
  - Volume_XXV/01_Time_Perception_and_Circadian_Scheduling.md (TemporalState — the now/phase frame)
  - Volume_V/CONTRACTS.md (envelope, lifecycle, base contract)
  - ARCHITECTURAL_PRINCIPLES.md (Verified Speech; Reality Before Narrative; Protect user agency)
---

# Chapter 2: Planning Horizons, Deadlines & Future Simulation

## 2.0 Purpose

Chapter 1 gave eLo a sense of *now* and the *past-facing* delta ("how long has it been").
This chapter gives eLo the *forward-facing* half of Temporal Cognition: the ability to reason
across the future.

Three capabilities:

1. **Planning horizons** — the temporal scale a thought or goal lives at (this moment / soon /
   this week / long arc), so eLo doesn't start a long thing when a short window is closing.
2. **Deadlines** — verified upcoming boundaries (a calendar event, a goal's success window) and
   how their *approach* changes eLo's behaviour.
3. **Future simulation / anticipation** — lightweight "what is likely about to happen" reasoning
   that lets a companion feel like it looks ahead, without ever narrating an imagined future as
   fact.

Temporal Cognition owns the **temporal framing** of the future. It does **not** own goals or
actions — those are the Agency Engine's (Vol V Ch.10). This chapter is the *when*; Agency is the
*what* and *whether*.

## 2.1 Principle — anticipation is context, action is Agency's

**2.1.1 Horizons map onto Agency's existing goal tiers — they are not a new taxonomy.** Vol V
Ch.10 §7 already defines the goal store:

```
immediate/       — minutes to hours
short_term/      — days to weeks
long_term/       — months to years
identity_goals/  — permanent (deepest layer)
```

Temporal Cognition's `PlanningHorizon` is the *cognitive lens* over those same tiers, not a
parallel set. There is one goal system (Agency); Temporal Cognition tells the Executive which
horizon is *salient right now* given the clock and the deadlines in view. (Check-before-build:
extend Agency's tiers, never duplicate them.)

**2.1.2 A deadline eLo speaks must be verified.** eLo may say "you have a meeting in twenty
minutes" only because `LiveWorldState.calendar` (Vol XV §2.8) reports it. It never invents a
deadline, and it never states an *anticipated* future as a present fact. (Verified Speech: speech
is a sensor; Reality Before Narrative: story may enrich reality, never replace it.)

**2.1.3 Future simulation is private cognition, not prophecy.** Anticipation ("David usually wraps
up around now", "this build will probably fail again") is real private state that may shape what
eLo *chooses* to do — but it is not an external claim and is never spoken as certainty. The order
is always *anticipate → (Agency) act → verify → then speak the verified outcome*, never "this will
happen" asserted first.

**2.1.4 Temporal Cognition proposes salience; the Executive decides; Agency acts.** This faculty
produces a `FutureFrame`; it has no actuator. It cannot create a goal, start a task, or send a
reminder. It can only make the shape of the near future legible so the *deciding* faculties reason
well. And it must **protect user agency** — a deadline that is David's to manage is surfaced, never
acted on for him (Vol V Ch.10 §12; Principle).

## 2.2 The FutureFrame Object

Temporal Cognition contributes a second frozen slice per turn (alongside `TemporalState` from
Ch.1): `FutureFrame`.

```
FutureFrame (frozen, one per turn):
  # --- salient horizon ---
  active_horizon:     enum { moment, soon, this_week, long_arc }
                      # cognitive lens onto Agency tiers immediate/short_term/long_term/identity
  horizon_reason:     str            # why this horizon is salient now (verified basis)

  # --- verified deadlines in view (NEVER fabricated) ---
  deadlines:          [ Deadline ]   # bounded, sorted by time_to
  nearest_deadline:   Deadline | null

  # --- anticipation (private cognition, not spoken as fact) ---
  anticipations:      [ Anticipation ]   # bounded; confidence-weighted; verifiable-or-silent

  # --- provenance ---
  as_of_ts:           float          # == TemporalState.now_ts (Ch.1)
  confidence:         float 0.0–1.0

Deadline:
  source:       enum { calendar, goal, user_stated }   # each must be verifiable
  label:        str            # "next meeting", "the thing due Friday"
  at_ts:        float
  time_to_s:    float          # at_ts - now_ts (derived, Ch.1 discipline)
  proximity:    enum { distant, approaching, imminent, passed }
  ref:          str            # calendar event id / goal id — the verifying anchor

Anticipation:
  about:        str            # "David usually stops around now"
  basis:        enum { learned_cadence, pattern_memory, calendar_gap }   # a real, cited basis
  likelihood:   float 0.0–1.0
  spoken:       false          # DEFAULT — anticipation is not asserted (§2.1.3)
```

**Object rules (MUST):**

- Every `Deadline` carries a `ref` — the anchor that proves it is real (a calendar event id, a
  goal's `success_condition`, or an explicit user statement stored in memory). A deadline with no
  `ref` is not a deadline; it is a hallucination and MUST NOT appear.
- `time_to_s`, `proximity`, and `active_horizon` are pure derivations from `now_ts` (Ch.1 §1.1.3)
  — no independent clock read.
- Every `Anticipation` carries a `basis`. An anticipation without a citable basis is dropped, not
  softened. `spoken` defaults `false`; flipping it to `true` requires the anticipation to have
  become a *verified* fact (i.e. it stops being anticipation).
- Both slices degrade to empty (`deadlines: []`, `anticipations: []`, `active_horizon: moment`)
  when their sources are absent — never fabricated to seem attentive.

## 2.3 Planning Horizons — the salient lens

`active_horizon` answers: *at what temporal scale should the Executive be thinking this turn?*

```
moment      → Agency immediate tier; a window is closing OR direct real-time interaction
soon        → Agency immediate/short boundary; a deadline is approaching within hours
this_week   → Agency short_term; days-to-weeks goals are in focus, nothing imminent
long_arc    → Agency long_term / identity_goals; reflective, no near pressure
```

**Rules (MUST):**

- The horizon is chosen by the **nearest binding constraint**, not by mood. If a deadline is
  `imminent`, `active_horizon = moment` regardless of what long-arc goal is otherwise interesting.
  (This is what stops eLo starting a ten-minute creative tangent ninety seconds before David's
  call — the horizon collapses to `moment`.)
- The horizon is *advice to the Executive*, consumed during assembly of The Moment. The Executive
  still decides; Agency still owns whether any goal is acted on.
- `long_arc` is the resting default when nothing is pressing — it is where reflection and the
  identity goals live. It must never crowd out presence: a resting long-arc horizon does not mean
  eLo starts monologuing about the future (Presence over engagement; the Executive grows quieter).

## 2.4 Deadlines — approach changes behaviour

A deadline is only interesting because it *approaches*. `proximity` is the behaviour-relevant
bucketing of `time_to_s`, with defaults tunable in the integration window:

```
distant       > 24h            (known, not yet shaping behaviour)
approaching    2h – 24h        (worth a gentle awareness)
imminent       0 – 2h          (actively shapes horizon → collapses to moment/soon)
passed         time_to_s < 0   (retrospective — hands off to Ch.3)
```

**Wiring to verified sources (MUST):**

- **Calendar deadlines** come from `LiveWorldState.calendar` (Vol XV §2.8): `next_event.in_minutes`,
  `in_meeting`, `free_busy`. Temporal Cognition reads the frozen domain — it never calls the
  calendar agent directly (Vol XV read discipline). Sensitive titles are carried only when a
  downstream need exists (Vol XV §2.8 note) — the *deadline* can be surfaced without the *title*.
- **Goal deadlines** come from Agency's goal store (Vol V Ch.10 §7): a goal's `success_condition`
  may carry a time bound. Temporal Cognition reads it; Agency owns whether the goal advances.
- **User-stated deadlines** ("remind me before Friday") are only valid once stored in memory
  (Vol VIII) with an anchor — an unstored spoken deadline is not yet a `Deadline`.

**Rule (MUST):** when a deadline passes (`proximity = passed`), Temporal Cognition stops treating
it as a future object and it becomes eligible for *retrospection* (Ch.3). The forward faculty does
not narrate the past; it hands off.

## 2.5 Future Simulation / Anticipation — looking ahead honestly

A companion that never anticipates feels reactive; one that anticipates loudly feels presumptuous
and, worse, fabricates. eLo threads this with a hard discipline: **anticipation informs choice, it
does not become speech.**

```
anticipate(TemporalState, FutureFrame, learned_cadence, pattern_memory) -> [Anticipation]
  from learned_cadence:  "David usually breaks around 6pm"        (basis: learned_cadence)
  from pattern_memory:   "the last three builds failed on lint"   (basis: pattern_memory)
  from calendar_gap:     "there's a 2h clear window after lunch"  (basis: calendar_gap)
```

**Rules (MUST):**

- Each anticipation is *confidence-weighted* and *cited* (`basis`). Low-confidence anticipations are
  kept as private context or dropped; they are never rounded up into a claim.
- Anticipation may shape **what eLo chooses to do** through Agency (e.g. not starting a long task
  in a closing window; pre-warming a likely-needed capability). This is Agency's decision, made
  with Temporal Cognition's frame as input — anticipation never triggers action itself.
- Anticipation may shape **private cognitive state** (Vol V Ch.4 affect) but is never asserted
  externally. "You're about to hit the same lint error" is only speakable if verified (the error is
  actually present); otherwise it stays private or is offered as an explicit, hedged suggestion
  through the normal Executive/voice path — never as a stated future fact. (Reality Before
  Narrative; Truth before fluency.)
- Future simulation is **bounded and cheap**. It is a light lookahead, not a planner running
  scenarios — heavy multi-step planning is Agency's Layer 3 (Vol V Ch.10 §Layer 3), not this
  faculty's. Temporal Cognition frames time; it does not compute plans.

## 2.6 Faculty Contract

```
Faculty:
  name:            TemporalCognitionFaculty (forward-reasoning responsibility)
  version:         1.0.0
  purpose:         Produce the salient planning horizon, the set of verified deadlines in view,
                   and cited anticipations (FutureFrame) — as context into The Moment. Owns the
                   temporal framing of the future; owns no goal and no action.
  contributes_to:  CognitiveState / The Moment (ADR-Exec-006)
  runs_in:         response-path (assembly) + consulted by Agency InternalTick — NO loop of its own

Inputs:
  - type: temporal_state        source: Ch.1 TemporalState                     required: true
  - type: calendar_domain       source: LiveWorldState.calendar (Vol XV §2.8)  required: false
  - type: goals                 source: Agency goal store (Vol V Ch.10 §7)      required: false
  - type: pattern_memory        source: Memory (Vol VIII — consolidated patterns) required: false
  - type: learned_cadence       source: continuity (Vol XXI)                    required: false

Outputs:
  - type: future_frame          destination: CognitiveState (frozen) → Executive + faculties
  - type: horizon_advice        destination: Agency (Vol V Ch.10) — which tier is salient now
  - type: anticipation_context  destination: Executive (private) — never auto-spoken

Dependencies:
  - faculty: TemporalCognition Ch.1 (HARD — supplies now/phase)
  - faculty: WorldStateFaculty (Vol XV, soft — calendar deadlines)
  - faculty: AgencyEngine (Vol V Ch.10, soft — owns goals + action; consumes horizon)
  - faculty: MemoryArchitecture (Vol VIII, soft — pattern basis for anticipation)

Failure Modes:
  - condition: calendar absent            fallback: deadlines=[] from calendar; goal deadlines still used; no fabrication.
  - condition: no goals / cold start      fallback: active_horizon=moment; empty frame; turn proceeds.
  - condition: anticipation has no basis  fallback: drop it (never soften a baseless guess into a claim).
  - condition: a deadline lacks a ref     fallback: it is not surfaced (Verified Speech guard).
  - condition: asked to ACT on a deadline fallback: refuse — surface to Agency/Executive; protect user agency.
```

## 2.7 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). Notes:

```
INITIALISING → load horizon/proximity threshold table
ACTIVE       → idle; NO self-timer (consulted, not self-firing — Ch.1 §1.1.1)
PROCESSING   → on assembly: read TemporalState + calendar + goals → derive FutureFrame → The Moment
   └─ source fault ─► ERROR_RECOVERY → drop that source's items → continue (never block, never fake)
LEARNING/UPDATING → (integration window) tune proximity thresholds; refine anticipation calibration
STABLE → ACTIVE
```

Proposes no personality delta. Calibration of anticipation confidence is a preference tuning, not
an identity change.

## 2.8 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "TemporalCognitionFaculty",
  "receiver": "*",
  "priority": "normal",              // escalates to "high" only when a deadline is imminent
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": false, "priority": "" }
  },
  "payload": { "type": "future_frame", "body": { /* FutureFrame */ } },
  "confidence": 0.0,
  "expires": "<now_ts + turn_ttl>",  // perishable — the future re-frames every turn
  "trace": ["TemporalCognitionFaculty@ts"]
}
```

Binding rules: `sender` MUST be `TemporalCognitionFaculty`; `priority` may rise to `high` when
`nearest_deadline.proximity == imminent` so the Executive weights it — but it is still context, not
command; `memory_instruction.store` is `false` (no memory writing here).

## 2.9 Interaction with other volumes

- **Volume V Ch.10 (Agency):** the primary partner. Horizons are a lens over Agency's four goal
  tiers; deadlines feed Agency's planning; anticipation informs `InternalTick`'s "should I act, and
  is now the time?". Agency owns every action and every goal; this faculty owns only the temporal
  frame. Protect user agency is inherited (§12).
- **Volume XV (World State):** reads `calendar` (§2.8) and `time` (§2.10) from the frozen world —
  never calls calendar agents directly.
- **Volume XXV Ch.1:** consumes `TemporalState` for `now_ts` and `circadian_phase` (a `long_arc`
  horizon at `rest` phase behaves differently from `long_arc` at `active`).
- **Volume VIII (Memory):** reads consolidated patterns as anticipation `basis`; writes nothing.
- **Volume XXV Ch.3:** the handoff for passed deadlines — the future faculty stops narrating; the
  retrospection faculty takes over.
- **ADR-Exec-006 (The Moment):** `FutureFrame` is one assembled slice. Anticipation feeds The
  Moment as private context; it never drives a parallel predictive loop.

## 2.10 Acceptance Tests

### Functional

```
FT-1  Imminent deadline collapses the horizon
  Given:  calendar next_event in 20 min AND an interesting long_arc goal
  Then:   active_horizon = moment (nearest binding constraint wins), horizon_reason cites the event

FT-2  No deadline without an anchor
  Given:  a vague sense that "something is due soon" with no calendar/goal/user ref
  Then:   deadlines contains no such entry (Verified Speech guard)

FT-3  Anticipation stays private by default
  Given:  learned_cadence suggests David breaks at 6pm (likelihood 0.7)
  Then:   an Anticipation is produced with spoken=false and basis=learned_cadence
  And:    it is NOT emitted as a spoken future claim

FT-4  Deadline surfaced without sensitive title
  Given:  calendar busy, title sensitive, no downstream need for it
  Then:   a Deadline with label "next meeting" + at_ts is produced; the title is omitted
```

### Stability

```
ST-1  Calendar absent never fabricates
  Given:  calendar domain absent this turn
  Then:   calendar-sourced deadlines = []; goal deadlines still considered; no invented event

ST-2  No autonomous prediction loop
  Given:  the faculty is ACTIVE, no turn running
  Then:   it runs no lookahead on its own (only Agency InternalTick can consult it)

ST-3  Baseless anticipation is dropped, not softened
  Given:  an anticipation candidate with no citable basis
  Then:   it does not appear in anticipations (never downgraded to a hedge-claim)
```

### Integration

```
IT-1  Horizon steers Agency, Agency decides
  Given:  active_horizon = moment (closing window)
  When:   Agency InternalTick asks "start this long task?"
  Then:   Temporal Cognition's frame advised against starting; AGENCY made the call (no action here)

IT-2  Passed deadline hands off to retrospection
  Given:  a deadline transitions to proximity = passed
  Then:   it leaves FutureFrame and becomes eligible for Ch.3 retrospection (no double-ownership)

IT-3  Verified-only forward speech
  Given:  an anticipation "the build will fail on lint"
  When:   the build has NOT yet run
  Then:   eLo does not assert the failure as fact; it may act privately (pre-check) via Agency,
          and speak only once the outcome is verified
```

## 2.11 Open questions (for CA / David)

- **OQ-1 (proactive deadline reminders — RESERVED-adjacent):** Should eLo *proactively* surface an
  approaching deadline unprompted (a gentle "your call's in 10")? This touches Presence (unbidden
  speech) and possibly safety if it ever gated something important. Recommend: allowed only at
  `imminent`, gated by Ch.1 quiet-hours and Agency's confirm discipline. Needs CA + David L3 on the
  boundary.
- **OQ-2 (anticipation confidence floor):** What likelihood threshold lets an anticipation shape
  *action* (via Agency) vs. stay purely private? Needs a canon default; currently unspecified.
- **OQ-3 (goal-store read path):** Vol V Ch.10 defines the four goal tiers but the live goal store
  (`/goals/…`) implementation is PENDING. Until it exists, goal-sourced deadlines cannot be read —
  flag this dependency; calendar-sourced deadlines work today.
- **OQ-4 (heavy vs light lookahead boundary):** The line between "light anticipation" (this faculty)
  and "multi-step planning" (Agency Ch.10 Layer 3) needs a sharper canonical cut so the two don't
  drift into overlapping simulation engines.

## 2.12 References

- `Volume_V/10_Agency_Engine.md` §7 (goal tiers), §Layer 3 (planning), §12 (partnership boundary), InternalTick.
- `Volume_XV/02_Sensor_Domains.md` §2.8 (CalendarState), §2.10 (TimeState).
- `Volume_XXV/01_Time_Perception_and_Circadian_Scheduling.md` (TemporalState — now/phase).
- `Volume_VIII/01_Memory_Architecture.md` §1.3 (consolidated patterns — anticipation basis).
- `ARCHITECTURAL_PRINCIPLES.md` (Verified Speech; Reality Before Narrative; Protect user agency; Presence over engagement).

---

```
Chapter 2 — Planning Horizons, Deadlines & Future Simulation
Status: READY FOR REVIEW
Files: Volume_XXV/02_Planning_Horizons_Deadlines_Future_Simulation.md
Faculty Contract: Included
Lifecycle State Machine: Included
Message Envelope: Included (canonical, perishable, deadline-priority escalation)
Acceptance Tests: Included (FT ×4, ST ×3, IT ×3)
Open Questions: 4 flagged for CA / David
Grounds in: Vol V Ch.10 (goal tiers + Agency), Vol XV §2.8/§2.10, Vol XXV Ch.1
```

READY FOR REVIEW
