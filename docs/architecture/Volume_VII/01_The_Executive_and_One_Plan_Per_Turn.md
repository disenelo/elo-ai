---
chapter: 1
title: "The Executive and One Plan Per Turn"
volume: VII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (runtime/executive.py live + FROZEN; three post-decision override sites outside it)
audit_status: OPEN
dependencies:
  - ARCHITECTURAL_PRINCIPLES.md (Invariant #2 Executive Authority · #3 Verified Speech · #4 Single Cognitive Truth)
  - Volume_V/01_Cognitive_Core.md §1.4 (the three contracts) · §1.6 (CognitivePlan) · §1.8 (the eight laws)
  - Volume_V/CONTRACTS.md §1 (where faculties sit — "the Executive (Ch.1 / Vol VII) is the only decider")
  - Volume_XVI/01_Coordination_Under_One_Executive.md (Executive decides, never vote)
  - Volume_XVI/04_… §4.2 (the conflict-resolution ORDER lives there, not here)
  - DECISION_LOG.md ADR-Exec-001 (Verified Executive Authority), ADR-Exec-002 (Single Cognitive Truth)
  - runtime/executive.py (decide() + Conversation Action Layer — LIVE, FREEZE_V1_LOCK)
  - runtime/spine/executive_faculty.py, runtime/spine/spine.py, runtime/spine/plan.py
---

# Chapter 1: The Executive and One Plan Per Turn

## 1.0 Purpose

Volume V Ch.1 says *"only the Executive decides"* and stops there. Volume XVI says *"a role of the
Executive (Vol VII), NOT a new decider"* three times and stops there. Nothing said **what the
Executive is**, what its decision is made of, or what constrains it.

This chapter does that. It defines Executive Authority as an operating rule rather than a slogan;
it specifies the one `CognitivePlan` per turn; it canonises the **Conversation Action Layer** that
already runs in `runtime/executive.py`; and it states the load-bearing architectural commitment
underneath all of it — **the Executive is deterministic, and the language model is the voice, not
the seat of self.**

## 1.1 Principle — Executive Authority

**1.1.1 The Executive is the sole authority for externally visible assertions.** Faculties advise.
The Executive decides. Nothing else in eLo may originate an outward claim, an action, or a silence.
(`ARCHITECTURAL_PRINCIPLES.md` Invariant #2; `Volume_XVI` §1.1.)

**1.1.2 The Executive may only assert VERIFIED reality.** Intent is not execution. The canonical
ordering, ADR-Exec-001 verbatim:

```
Observe → Assess Faculty Health → Plan → Execute → Verify → Update World State → Speak
```

Speech is the **last** step and it is a *sensor* — it reports what the Executive knows; it does not
create reality. Actions create reality. (ADR-Exec-001 principle 6.) Chapter 3 makes this a gate.

**1.1.3 One decision, one plan, one truth.** The Executive emits exactly one `CognitivePlan` per
turn, and every word, tone, posture, motion, LED colour, and system action derives from *that* plan.
No modality invents private state downstream (ADR-Exec-002). This is One Brain expressed at runtime.

**1.1.4 There is no vote.** Faculties disagreeing is normal; resolving by consensus is forbidden.
The Executive decides unilaterally and **logs the rationale**. The resolution *order* is specified
in `Volume_XVI` §4.2 (and still needs D-XVI-C ratification); this chapter only fixes that arbitration
is a **role of the one decision**, never a second decider.

**1.1.5 The Executive grows quieter.** As capability rises, narration falls. A silent correct
behaviour beats a spoken one; `SILENCE` is a first-class Executive action, not a failure to respond.
(`ARCHITECTURAL_PRINCIPLES.md` — "The Executive grows quieter"; "Silence is part of the interface.")

## 1.2 What the Executive Is (and is not)

| The Executive IS | The Executive is NOT |
|---|---|
| A deterministic decision function over one frozen assembled state | A language generator that happens to orchestrate faculties |
| The single place `what to do` is chosen | A place `what is true` is chosen (truth is not arbitrated — `Volume_XVI` §4.1.2) |
| The owner of Working Memory (D-G) and of the intent queue (Ch.4) | The owner of long-term memory (Vol VIII, D-F) or personality (Vol X) |
| The gate on speech (Ch.3) | The producer of speech — the Language layer + LLM produce wording |
| Where arbitration, allocation, and interruption *happen* | A "coordination faculty" separate from the deciding faculty |
| Adaptable in its *policies* (ADR-Exec-005) | Adaptable in its *identity, values, or truth* — those are immutable |

ADR-Exec-001's Context names the exact failure this table exists to prevent, verbatim:

> *"the Executive was acting as a language generator that happened to orchestrate faculties — it
> described *intended* reality (narrated a sit/wave/memory that never executed), looped on a dead
> backend, leaked foreign snippets, and oscillated on memory."*

## 1.3 The Conversation Action Layer (grounded — this is live code)

`runtime/executive.py` already implements the Executive's outward decision as a **Conversation
Action Layer**: a determination of *what to do this turn*, not merely what to say. Its own docstring:
*"Sits between attention and response generation. Determines WHAT TO DO, not just what to say."*

**The nine actions, in the live priority order:**

```
ANSWER    — factual question → direct answer
BUILD     — idea presented or explicit "build on this" → contribute
CONNECT   — multiple concepts → show relationships
CELEBRATE — positive momentum / breakthrough → acknowledge progress
REFLECT   — exploring meaning → gentle perspective
GROUND    — overwhelm / distress → stabilise
CHALLENGE — stuck assumption → gentle alternative view
WITNESS   — personal/emotional share → presence only
SILENCE   — nothing useful to add
```

**Live rules that are already law in code and are hereby canon:**

- **The POSITIVE EMOTION RULE** (verbatim from `runtime/executive.py`): *"Positive valence must NEVER
  trigger grounding. Positive high energy + building momentum → CELEBRATE or BUILD. Never route joy
  into stabilisation responses."* This is a permanent behavioural invariant, not a heuristic.
- **Loop protection always wins.** `decide()` short-circuits to `DIRECT` / one sentence /
  `stability: True` when `loop_detected` or `intent == "stabilise"`. Stability is part of the ONE
  decision, not a second decider (`Volume_XVI` §2.4).
- **An explicit pause is an input.** Input consisting only of `. , … -` routes to `SILENCE` with
  confidence 1.0. eLo treats a pause as a signal, not as an empty prompt.
- **Session closure routes to WITNESS regardless of valence** — "good session", "done for today",
  "signing off" are not questions to answer.
- **Action determines tone, and tone determines length.** Five tones
  (`CHILDLIKE-WISE · SILENCE-AWARE · DIRECT · JOYFUL · WITTY`) with a per-tone `max_sentences` cap;
  `CELEBRATE` is hard-capped at one sentence. Length is an Executive decision, not a style choice.
- **MOON mode.** High energy + low tension + a creative/conversational intent shifts
  `build/connect/reflect` to `WITTY` — the mechanism by which play and surprise are *allowed* to
  surface. (Sits with **Protect Wonder**; see also Vol VI §4.5.)

**Canonical rule (MUST):** the action set is a **closed vocabulary**. A new outward behaviour is
added by adding an action to this layer, never by a faculty or a surface producing behaviour
directly. Adding an action is a canon change (Vol XXVII), not a code change.

**Gap (PENDING).** The live layer decides from `intent`, `valence`, `momentum` and lexical phrase
tables over the raw input. It does **not** yet read the assembled state — the self-model, capability
health, affordances, world, or the intent queue are not inputs to `_conversation_action()`. That is
the Ch.2 ordering fix stated behaviourally: today the Executive decides *how to talk*; canon requires
it to decide *what to do, situated*. Marked PENDING, not claimed.

## 1.4 The One Plan

```
CognitivePlan (one per turn, immutable once produced):
  # --- the decision (runtime/executive.py) ---
  conversation_action  ANSWER|BUILD|CONNECT|CELEBRATE|REFLECT|GROUND|CHALLENGE|WITNESS|SILENCE
  tone                 CHILDLIKE-WISE|SILENCE-AWARE|DIRECT|JOYFUL|WITTY
  max_sentences        int (per-tone cap; CELEBRATE = 1)
  response_goal        answer|create|reflect|stabilise|clarify|explore
  stability            bool     # stabilisation override applied
  cognitive_load       low|medium|high
  cal_reason           str      # WHY this action — feeds the decision journal (Ch.4)

  # --- the situation it was decided against (pinned, not re-decided) ---
  snapshot             UnifiedCognitiveState   # frozen (Ch.2)
  cognitive_state      CognitiveState          # frozen
  world                LiveWorldState          # frozen (Vol XV)
  working_memory       WorkingMemory           # frozen (Vol VI)

  # --- what it becomes (projection, never re-decision) ---
  emotional_vector     EmotionalVector   # runtime/spine/executive_faculty.py
  presence_plan        …                 # light engine → presence faculty
  embodiment_state     EmbodimentState   # text · emotional_state · motion_command · robot_led_state
  system_action/arg    …                 # gated capability invocation
  capabilities         [(agent, meaning)]
```

**Plan rules (MUST):**

- **Immutable after production** (Vol V Ch.1 Law: *Immutable Plans*). Enrichment
  (`executive_faculty.enrich()`, light engine, presence faculty) may **add derived projections** to
  the plan; it may never change the decision — `conversation_action`, `tone`, `max_sentences`,
  `response_goal` are closed once decided.
- **Everything outward traces to it.** `build_embodiment_state(plan)` derives text, emotional state,
  motion, and robot LED from the same plan — that is ADR-Exec-002 in code, and it is the reason a
  desktop eLo and a robot eLo cannot disagree (`Volume_XVI` §4.3).
- **The plan carries its own situation.** `plan.snapshot`, `plan.cognitive_state`, `plan.world`,
  `plan.working_memory` are pinned so that any later question — including *"why did you do that?"*
  (Ch.4) — is answered from the state that was actually in front of the Executive, not a reconstruction.

## 1.5 Why the Executive is deterministic, and the LLM is the voice

This is the load-bearing commitment of the whole volume. David and the Chief Architect, verbatim
(`SITUATED_SELF_v1_assembly.md`, the Capstone Principle):

> *"When David asks **'eLo, who are you?'**, the Executive does NOT hand the question to the LLM and
> hope. It ASSEMBLES the answer from state — identity · current embodiment · location · state ·
> capabilities · relationships · memories · preferences · active intentions · recent experiences ·
> learned patterns · narrative continuity · current development → one cognitive state → **eLo
> speaks.** The language model is the VOICE through which eLo expresses his assembled self, **not the
> place the self exists.** Every self-claim has a cause… **We are not making eLo claim consciousness
> — we are building a system where self-knowledge has causes.**"*

And the Chief Architect on why the runtime, not the model, must hold the "I"
(`_intake/SOURCE_2026-08-08_self_model_becoming.md`, verbatim):

> *"At the moment, a lot of your transcript shows the language model talking about eLo. We need the
> runtime to know: I am eLo. I am currently in desktop embodiment… Then the LLM isn't inventing an
> identity every turn. It is reading itself."*

**The division of labour (MUST):**

| Layer | Owns | Never |
|---|---|---|
| **Executive** (deterministic) | What to do · whether to speak at all · what may be claimed · tone · length · which capability to invoke | Produce wording |
| **Language / LLM** (generative) | *How* a decided, permitted truth is worded | Decide the action · introduce a claim the Executive did not license · assert state |
| **Personality** (a lens, Vol V §1.7) | How a confirmed truth *sounds* | Change *what* is true |

**Consequences of determinism (why we pay for it):**

1. **The decision is reproducible and testable.** The same assembled state yields the same action.
   A generative decider cannot be regression-tested; `runtime/executive.py` can, and is.
2. **The decision is explainable.** `cal_reason` exists because a deterministic branch *has* a
   reason. Ch.4's "why did I do that?" is only truthful because of this.
3. **The decision survives the model.** Swapping Groq → Cerebras → Ollama → Mock
   (`runtime/backend_router.py`, Vol XX) changes the *voice*, not the *self*. eLo on a local 8B model
   is still eLo. If the Executive lived in the model, it would not be.
4. **The self cannot be prompted away.** A jailbreak, a weird phrasing, or a hallucination cannot
   move the decision, because the decision was not made by the thing that hallucinates.

**Rule (MUST):** no Executive decision may be delegated to an LLM call. The LLM may be *invoked by*
a plan (to word a response, to summarise, to propose); its output is **input to the next turn**, never
the current decision. A future "LLM proposes, Executive disposes" path is permitted only as an
advisory faculty contributing to the assembled state — subject to the same verification rules as any
other faculty, and it does not decide.

## 1.6 The single-decision boundary (and the live violations of it)

**Rule (MUST):** `decide()` is the only place the outward action is chosen, and it is called **once**
per turn.

**Verified live state (2026-08-10, read from source — stated honestly):**

- `server.py:2322` calls `exec_decide(...)` **once**. Good.
- `server.py` then **mutates the returned decision at three sites**:
  - **L2335** — stabilisation forced by the state machine → `overridden_by_safety: True`,
    preserving `original_action` / `original_tone`.
  - **L2360** — WO-020 "Seam A": a plain imperative that routed to CONNECT/REFLECT/WITNESS is
    re-routed to ANSWER → `overridden_by_routing: True`. The in-code comment is explicit about why
    it lives outside: *"executive.py is frozen, so we post-process here."*
  - **L2383** — WO-029: the "all good" greeting family, absent from the frozen `_HOW_ARE_YOU` set →
    `overridden_by_routing: True`.
- `spine._executive_faculty()` then **reads** that decision from `attention["_exec_decision"]` and
  wraps it into the one `CognitivePlan`. It does not re-decide. Good.

**Assessment (honest).** These are not a second brain — each preserves the original decision and
labels itself, and `self/decision_journal.py` reads exactly those fields, so the overrides are
*auditable* rather than hidden. But structurally they are Executive policy executing outside the
Executive, and they exist because the module is frozen. Two of the three (safety-stabilisation,
imperative routing) are genuinely Executive concerns and belong inside the one decision.

**Canonical position:** an override is legitimate **only if** it (a) preserves `original_action`,
(b) sets a typed `overridden_by_*` reason, (c) is recorded in the decision journal, and (d) is
registered here as Executive policy. Anything meeting all four is *the Executive deciding*, wherever
the lines physically sit. Anything not meeting all four is a second decider and is forbidden.
Whether to fold them back into `decide()` when the freeze lifts is `OQ-VII-2`.

## 1.7 Deliberately unwritten (the Bible's remaining VII scope)

`ARCHITECTURE_BIBLE.md` scopes four more things to Volume VII that have **no canon anywhere** and no
verbatim source from David to write from. They are named here so they are not lost, and left unwritten
rather than invented (`OQ-VII-7`):

- **Thinking modes** — deliberative vs reactive vs peripheral reasoning depth. Partially anticipated
  by Vol VI §4.4's attention `mode` and by `cognitive_load` in the live decision; unspecified as an
  Executive policy.
- **Interruption policy** — when an internal intent or a world event may interrupt an in-flight
  intention. Touches D-PRESENCE ("never clamour for attention") and is therefore likely David L3.
- **Goal management** — goal lifecycle above the per-turn intent queue (Ch.4 covers the queue, not
  long-lived goals). Overlaps Vol V Ch.10 Agency and Vol XXI narrative threads; the boundary needs
  drawing before drafting.
- **Scheduling / resource allocation** — Vol XX owns cost tiers as *a policy of the Executive*;
  attention budget is Vol VI. What remains genuinely VII's is unclear and should be scoped before
  it is written.

## 1.8 Faculty Contract (the Executive)

```
Faculty:
  name:            Executive               # runtime/executive.py + runtime/spine/executive_faculty.py
  version:         1.0.0 (FREEZE_V1_LOCK)
  purpose:         Decide once per turn, against one frozen assembled state, what eLo does —
                   including whether to speak at all — and emit exactly one CognitivePlan that
                   every surface renders and nothing re-interprets.
  contributes_to:  CognitivePlan (sole producer)
  runs_in:         response-path (exactly once per turn, AFTER assembly — Ch.2)

Inputs:
  - type: unified_cognitive_state   source: ExecutiveAssembly (Vol XVI Ch.2)        required: true
    description: The one frozen object. If a fact is not in it, the Executive does not know it.
  - type: intent_queue              source: Executive-owned (Ch.4)                  required: false
  - type: safety_flag               source: Capability/Health components             required: false

Outputs:
  - type: cognitive_plan            destination: projection (embodiment, language, capability)
    description: ONE plan. Immutable. Carries its own pinned situation + cal_reason.
  - type: decision_trace            destination: self/journals/decision_journal.jsonl (Ch.4)
  - type: speech_licence            destination: Language layer (Ch.3 — what may be claimed, and at
                                                 which epistemic tier)

Dependencies:
  - faculty: ExecutiveAssembly (hard — no assembled state, no decision; Ch.2)
  - faculty: FacultyHealth (hard — health influences planning AND speech, ADR-Exec-001 principle 3)
  - faculty: FacultyBus (hard — all inbound contributions arrive as envelopes, Vol XVI Ch.3)
  - faculty: WorkingMemory/Attention (soft — D-G, Executive-owned; Vol VI)

Failure Modes:
  - condition: assembly degraded (a component absent)
    fallback:  decide on what is present at lowered confidence; SPEAK differently — the degradation
               must surface honestly (Ch.3 §3.5). Never fabricate continuity (ADR-Exec-001 §5).
  - condition: assembly entirely unavailable
    fallback:  last safe CognitivePlan, reduced mode; if every faculty fails, the static safe
               response (Vol V §1.10) — "Take a breath. I'll be right here."
  - condition: loop detected / stabilisation forced
    fallback:  DIRECT · 1 sentence · stability=True. Part of the ONE decision, never a second one.
  - condition: a faculty attempts an outward action directly
    fallback:  rejected at the bus. Faculties advise; only the Executive acts (Vol XVI §1.1).
  - condition: a downstream surface would re-decide
    fallback:  architecturally disallowed (ADR-Exec-002).
```

## 1.9 Lifecycle & Envelope

Ratified lifecycle (`Volume_V/CONTRACTS.md §3`, D-B).

```
INITIALISING → load tone/action tables, capability registry, health registry; subscribe to the bus
ACTIVE       → awaiting the assembled state (the loop runs even when silent — Vol V §1.3)
PROCESSING   → read frozen UnifiedCognitiveState → DECIDE ONCE → emit one CognitivePlan + trace
   └─ fault ─► ERROR_RECOVERY → last safe plan / reduced mode / static safe response → ACTIVE
LEARNING     → NEVER on the response path. Policy adaptation runs in the integration window only
               (ADR-Exec-005; Reinforcement & Adaptation Faculty, Vol XXVIII — sits AFTER Verify)
VALIDATION_REQUIRED → any change touching identity/values is proposal-only, David L3 (Ruling XXI)
UPDATING     → apply ratified policy deltas between turns, never mid-turn
STABLE → ACTIVE
```

**Rule (MUST):** the Executive **never learns inside a turn.** Learning is post-verification and
post-reflection (ADR-Exec-005: *"Learning never modifies TRUTH — only future DECISION-MAKING"*).

Envelope (`CONTRACTS.md §2`): the Executive emits `payload.type: cognitive_plan` with
`receiver: "*"` (every surface renders the same plan) and `expires` set to the turn TTL — a plan is
perishable and must never be replayed into a later turn. `priority` is set by the Executive;
`critical` is reserved for safety-veto traffic. `trace` is append-only and is what makes the single
decision auditable end to end.

## 1.10 Acceptance Tests

### Functional
```
FT-1  One decision per turn
  Given a turn, When it completes,
  Then decide() was invoked exactly once AND exactly one CognitivePlan exists.

FT-2  Closed action vocabulary
  Given any input, Then conversation_action ∈ the nine canonical actions; no surface,
  faculty, or LLM output introduces an outward behaviour outside that set.

FT-3  Positive emotion rule
  Given positive_high valence + building momentum,
  Then the action is CELEBRATE or BUILD — never GROUND.

FT-4  Silence is a decision
  Given input consisting only of "…", When the Executive decides,
  Then action = SILENCE with a recorded reason — not an empty ANSWER.

FT-5  Plan immutability
  Given a produced plan, When enrichment/light-engine/presence run,
  Then conversation_action, tone, max_sentences, response_goal are unchanged;
       only derived projections were added.

FT-6  Override discipline (§1.6)
  Given any post-decision override, Then it preserves original_action, sets a typed
  overridden_by_* reason, and appears in the decision journal. Otherwise: FAIL.
```

### Stability
```
ST-1  Loop protection inside the one decision
  Given loop_detected, Then DIRECT / 1 sentence / stability=True, produced by the SAME
  single decision — no second decider ran.

ST-2  Degraded honesty
  Given a faculty is OFFLINE, Then the plan reflects it and speech is constrained (Ch.3);
  eLo does not narrate a capability it does not have.

ST-3  Model swap invariance
  Given the backend changes (Groq → Cerebras → Ollama → Mock),
  Then the decision for identical assembled state is IDENTICAL; only wording differs.

ST-4  All-faculties-fail
  Given every faculty fails, Then the static safe response is returned; no crash, no fabrication.
```

### Integration
```
IT-1  Assemble → Decide → Project
  ExecutiveAssembly (frozen, Ch.2) → Executive (ONE plan) → EmbodimentState across surfaces.
  Assert: text, emotional_state, motion_command and robot_led_state all derive from the same
  plan object (ADR-Exec-002); no surface re-interprets.

IT-2  Trace completeness
  Given any turn, Then the decision journal entry names the action, its trigger (cal_reason),
  any rejected alternative, and any override — sufficient to answer "why did you do that?"
  from record alone (Ch.4).
```

## 1.11 Wiring to Live Anchors

- `runtime/executive.py` — `decide()`, `_conversation_action()`, `_INTENT_TONE`,
  `_ACTION_TONE`, `_MAX_SENTENCES`, the POSITIVE EMOTION RULE, the loop-protection branch.
  **FROZEN** (`FREEZE_V1_LOCK.md`) — extend via policy registered in this volume, never by editing
  around it silently.
- `runtime/spine/executive_faculty.py` — wraps the decision into the one plan; computes the
  `EmotionalVector`. Its docstring already states this chapter's law.
- `runtime/spine/spine.py` — `run()`; `_executive_faculty()` (the single call site);
  `build_embodiment_state()` + `_LED_FROM_EMOTIONAL_STATE` (projection, not decision).
- `runtime/spine/plan.py` — `CognitivePlan`, `EmotionalVector`, `EmbodimentState`.
- `server.py:2322` (the single `decide()` call) and L2335 / L2360 / L2383 (the three override sites
  audited in §1.6).
- `self/decision_journal.py` — consumes `cal_reason`, `original_action`, `overridden_by_*` (Ch.4).
- `runtime/state_machine.py` — stabilisation forcing; feeds the override at L2335.

## 1.12 Cross-Volume Interaction

| Volume | Boundary |
|---|---|
| **V (Cognitive Core)** | V Ch.1 states the three contracts and the eight laws; VII specifies the decider those laws constrain. `CONTRACTS.md §1` already points here. |
| **VI (WM & Attention)** | The Executive **owns** WM (D-G) and reads the attention winner + mode; VI owns the object and the competition. Vol VI §4.4 is the counterpart of this chapter. |
| **XV (World State)** | The world is *context, not command* — it informs the decision; it never is the decision. |
| **XVI (Coordination)** | XVI Ch.1 (allocation), Ch.2 (assembly mechanism), Ch.3 (bus), Ch.4 (conflict order + projection) are **roles and mechanisms of this Executive**. VII legislates; XVI mechanises. |
| **XX (Cognitive Economy)** | Tier choice and escalation are an Executive *policy*; XX owns the policy's content. Resolves XX `OQ-1` in XX's favour: the gate is Executive-owned, specified in XX. |
| **XXVIII (Learning)** | Adaptation sits AFTER Verify and may change policy weights, never identity, truth, or Executive Authority (ADR-Exec-005). |
| **X (Personality)** | Personality shapes *how* a decided truth is expressed; it never changes the decision or the truth. |

## 1.13 Open Questions (for CA / David)

```
REQUIRES DECISION
  OQ-VII-2  The three post-decision override sites (§1.6). Fold into decide() when
            FREEZE_V1_LOCK lifts, or ratify as permanent registered Executive policy?
            Recommend: ratify now under the four-part rule in §1.6; fold in later.
  OQ-VII-7  Thinking modes · interruptions · goal management · scheduling (§1.7) — confirm
            these are Vol VII Ch.6–8 and not absorbed by XVI/XX, before anyone drafts them.
            Interruption policy touches D-PRESENCE and is likely David L3.
  Q1-a      [INVENTED — flag] Is the nine-action set CLOSED as canon (§1.3), meaning a new
            outward behaviour requires a canon change? Recommend yes; it is the single
            strongest guard against behaviour leaking back into surfaces.
  Q1-b      Should an advisory LLM faculty ever be permitted to CONTRIBUTE to the assembled
            state (§1.5)? Recommend: permitted as a faculty with normal verification rules,
            never as a decider. Confirm before anyone builds it.
```

## 1.14 References

- `ARCHITECTURAL_PRINCIPLES.md` — Invariants #1–#5; "The Executive grows quieter";
  "Cognition is objective; personality shapes expression, not truth"; "Reality Before Narrative".
- `DECISION_LOG.md` — ADR-Executive-001 (full text incl. the six principles and the canonical
  ordering), ADR-Executive-002, ADR-Exec-003/004/005/006; D-LANES; D-FREEZE.
- `Volume_V/01_Cognitive_Core.md` §1.4, §1.6, §1.8 · `Volume_V/CONTRACTS.md` §1–§3.
- `Volume_XVI/01…`, `…/02…`, `…/04…` — the coordination roles of this Executive.
- `FREEZE_V1_LOCK.md` — why `runtime/executive.py` is not edited casually.
- Code: `runtime/executive.py`, `runtime/spine/executive_faculty.py`, `runtime/spine/spine.py`,
  `runtime/spine/plan.py`, `runtime/state_machine.py`, `server.py` (L2322, L2335, L2360, L2383).

---
```
Chapter 1 — The Executive and One Plan Per Turn
Status: READY FOR REVIEW
Grounded in live code: nine-action Conversation Action Layer · POSITIVE EMOTION RULE · loop
  protection · five tones + per-tone sentence caps · SILENCE on explicit pause · one plan
  (executive_faculty) · plan-pinned snapshot/world/WM · three audited override sites
Flagged PENDING: the action layer does not yet read the assembled state (§1.3)
Flagged INVENTION: the four-part override legitimacy rule (§1.6); closed-vocabulary rule (§1.3)
Faculty Contract: Included · Lifecycle/Envelope: Included · Acceptance Tests: FT×6 ST×4 IT×2
Open Questions: 4 (OQ-VII-2, OQ-VII-7, Q1-a, Q1-b)
Implementation: PARTIAL
```

READY FOR REVIEW
