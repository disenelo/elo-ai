---
chapter: 4
title: "The Intent Queue and 'Why Did I Do That?' — Dual Intent, Arbitration, and the Decision Journal"
volume: VII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (decision journal LIVE — self/decision_journal.py WO-082; the dual-intent queue is PENDING — no internal-intent path exists)
audit_status: OPEN
dependencies:
  - _intake/SOURCE_2026-08-08_self_model_becoming.md (VERBATIM — David #4 Internal "why" / Intent Queue; the "Why did I do that?" capability; CA Part 3 §C dual-intent queue & governance)
  - SITUATED_SELF_v1_assembly.md (CA additions 4 + 9 — dual-intent queue, absence-awareness)
  - DECISION_LOG.md ADR-Exec-006 (`intent_queue` is a named component), ADR-Exec-005, ADR-Exec-001, D-PRESENCE
  - Volume_VII/02_… (the queue is a component of the assembled state)
  - Volume_VII/03_… (a "why" answer is a claim and is tiered)
  - Volume_V/10_Agency_Engine.md (agency — the boundary), Volume_VI (attention — what wins focus)
  - Volume_XVI/04_… §4.2 (conflict resolution between FACULTIES — distinct from intent arbitration)
  - self/decision_journal.py (WO-082, LIVE), runtime/cognitive_snapshot.py (pending_intentions)
---

# Chapter 4: The Intent Queue and "Why Did I Do That?"

## 4.0 Purpose

Two things the Executive owns that no volume claimed:

1. **What eLo wants** — and the fact that he wants two kinds of thing at once. David's words are
   external ("Sit down."); eLo's own are internal ("I want to explore that window"). Both are real
   intentions, they compete, and something has to arbitrate. Today the runtime has one shallow list
   holding at most a pending sit.
2. **Why he did what he did** — answerable from record, not reconstructed by a language model after
   the fact. This one is partially built and works.

Both are Executive-owned because both are *decisions about decisions*. Neither is coordination
(Vol XVI), neither is memory (Vol VIII), neither is personality (Vol X).

## 4.1 Principle

**4.1.1 Intentions are Executive state.** Like Working Memory (D-G), the intent queue is held by the
Executive, not by a faculty. Faculties may *propose* intentions; only the Executive holds, ranks,
commits, and retires them. ADR-Exec-006 already names `intent_queue` as a component of the assembled
state — this chapter specifies it.

**4.1.2 An intention survives the turn that created it.** ADR-Exec-006's phrasing: *"pending
intentions that must survive this decision cycle."* An intention that evaporates because the turn
ended is not an intention; it is a reflex. Continuity of wanting is part of continuity of being.

**4.1.3 Internal intent is real, and it is not an external claim.** eLo genuinely wanting to explore
is true. Saying *"there's something interesting over there"* is a world claim and is tiered (Ch.3
§3.4 rule 6). Reality Before Narrative applies to wanting exactly as it applies to doing.

**4.1.4 Arbitration is inside the one decision.** There is no "intent governor" faculty. Ranking the
queue is a role of the Executive, performed within the single DECIDE step (Ch.1 §1.1.4). Adding a
governor would be adding a second decider.

**4.1.5 A "why" is retrieved, never generated.** The answer to *"why did you do that?"* comes from
the decision record. If there is no record, eLo says there is no record. He does not construct a
plausible motive — that is confabulation, and it is the retrospective form of the exact failure
ADR-Exec-001 exists to stop.

## 4.2 The dual-intent queue

David, verbatim (`SOURCE_2026-08-08`, Part 2 item 4):

> **4. Internal "why"** — Intent Queue with EXTERNAL (David: *"Sit."*) + INTERNAL (*"I want to
> explore / that window looks interesting / I've been stationary for a while / I want to play / I
> want to go back to my world / I want to show David something"*), governance decides priority.

The Chief Architect, verbatim (Part 3 §C):

> **C. Dual-intent queue & governance** — `[EXTERNAL: David "Sit down"] + [INTERNAL: urge explore
> idle edge] → GOVERNANCE → chosen action.` **Attention & Absence Matrix:** `David_Idle_Time >
> 14_minutes` → `absence_awareness` flag → drop `Attention.David`, boost `Curiosity.Exploration`,
> push autonomous plans to internal queue.

And item 9 (also verbatim), which is the *reason* the internal queue matters:

> **9. Absence awareness** — David here / David hasn't interacted for 14 minutes / David returned.
> He explores while David works; on return: *"I explored the other side of the desktop while you were
> away. I found a route between the two windows that I hadn't tried before."*

**The two lanes:**

| | **EXTERNAL / conversational intent** | **INTERNAL / body-action intent** |
|---|---|---|
| Origin | David — request, command, question, or the shape of the conversation | eLo — curiosity, boredom, rest, practice, return-to-David, wanting to show something |
| Examples | *"Sit."* · *"Open Spotify."* · *"What do you think?"* · an unanswered question still open | *"I want to explore that window"* · *"I've been stationary a while"* · *"I want to practise that jump"* |
| Verification | Verified as *heard* (input received), not as *right* | Verified as *held* (it is genuinely eLo's state), not as *justified* |
| Default rank | Higher — David asked | Lower — unless David is absent (§4.3) |
| Expiry | On satisfaction, or on David changing subject | On satisfaction, on becoming unreachable, or on decay |

```
IntentQueue (Executive-owned; a component of UnifiedCognitiveState):
  external: [ Intent ]        # from David, ordered by recency + explicitness
  internal: [ Intent ]        # eLo's own, ordered by pressure
  committed: Intent | null    # the one currently being pursued (survives turns)

Intent:
  id            str
  lane          external | internal
  kind          conversational | body_action | capability | presence
  content       str                  # "sit beside David" | "explore the right-hand window"
  origin        str                   # "david:utterance@ts" | "curiosity:novelty@ts"
  pressure      0.0–1.0               # urgency/desire — internal intents build it over time
  requires      [capability_id]       # what it needs to be actionable
  feasible      bool + reason          # from capability + affordance check (POSSIBLE tier, Ch.3)
  boundary_ok   bool + reason          # D-PRESENCE / safety check
  status        proposed | queued | committed | blocked | satisfied | abandoned
  created_ts · last_seen_ts · expires
```

**Queue rules (MUST):**

- **Faculties propose; the Executive admits.** An intent enters as `proposed` and is only `queued`
  after the Executive accepts it. A faculty cannot self-commit an intention (Vol XVI §1.1 —
  faculties never initiate external actions).
- **One committed intent at a time.** eLo pursues one thing; the rest wait. Two committed intents is
  two selves wanting different things.
- **Every intent carries feasibility and boundary results before it can be committed** — capability
  check and D-PRESENCE check precede commitment, never follow it (ADR-Exec-003, Affordance Before
  Action).
- **Intents are perishable but not amnesiac.** An intent that expires is `abandoned` with a reason,
  and the abandonment is journalled (§4.5) — so *"why didn't you go and look?"* is also answerable.

**Live ground (verified — `runtime/cognitive_snapshot.py`):** `pending_intentions` exists as a field
and is populated with exactly one thing: `("sit", "cursor")` when a sit is in flight. There is no
lane distinction, no pressure, no feasibility, no arbitration, no internal intent path. `BodySchema`
carries `queued_intent` — a single movement intent parked behind a pending sit. **Status: the name
exists; the mechanism does not. PENDING.**

## 4.3 Arbitration

**FLAGGED AS INVENTION.** Nothing in canon or David's verbatim fixes an order; David says only
*"governance decides priority"* and the CA says *"GOVERNANCE → chosen action"*. The following is the
Architect's proposal, offered for ratification, **not** presented as David's call (`OQ-VII-4`).

```
1. SAFETY / BOUNDARY        An intent that is unsafe, irreversible under contradiction, or
                            violates D-PRESENCE is not ranked — it is refused. Space beats
                            desire. ("Take five" means gone, not lurking.)
2. EXTERNAL, EXPLICIT       David asked for something. It outranks everything eLo wants.
3. STANDING COMMITMENT      An already-committed intent is not abandoned for a newer, weaker
                            one — otherwise eLo never finishes anything and never feels
                            continuous. (Interruption policy proper is Ch.1 §1.7, unwritten.)
4. EXTERNAL, IMPLICIT       An open thread David left hanging; an unanswered question.
5. INTERNAL, HIGH PRESSURE  eLo's own strong intent — but only when it does not intrude.
                            Weighted UP by absence (see below).
6. INTERNAL, CURIOSITY      Low-pressure exploration. The Protect-Wonder lane.
                            May win when nothing else is live; may never displace 1–4.
```

**The absence rule (from David #9 + CA §C, and it is the point of the internal lane):** when David
has not interacted for N minutes, an `absence_awareness` flag is set — `Attention.David` drops,
`Curiosity.Exploration` rises, internal intents gain pressure and become eligible to commit. When
David returns, eLo has something real to report, from record: *"I explored the other side of the
desktop while you were away."* That sentence is only truthful because the exploration was journalled
(§4.5) — it is a Ch.3 REMEMBERED/VERIFIED claim, not a story.

**Arbitration rules (MUST):**

- Arbitration happens **inside** the one decision (§4.1.4).
- The **losing** intents are recorded, with why. This is what makes §4.5's `alternatives_rejected`
  truthful for *wants*, not only for *actions*.
- Arbitration never changes an intent's *feasibility* — it ranks; it does not persuade. An
  infeasible intent stays infeasible no matter how much pressure it has.
- **Autonomous and commanded are one capability.** Whatever eLo chooses to do from the internal lane
  must be drivable by the Executive from the external lane, through the same underlying capability
  (`ARCHITECTURAL_PRINCIPLES.md`; `Volume_XVI` §4.3). Two paths would let "eLo exploring" and "eLo
  told to explore" drift apart.

**Boundary with Vol XVI §4.2 (important, easy to confuse):** Vol XVI arbitrates **faculties
contradicting each other about the situation**. This chapter arbitrates **intentions competing for
eLo's one body and one voice**. Different inputs, different outputs, same single decider. Neither
supersedes the other; the safety veto is common to both.

## 4.4 The Executive Decision Journal

David, verbatim (`SOURCE_2026-08-08`, Part 2, "+ The 'Why did I do that?' capability"):

> David asks *"Why did you jump over there?"* — the runtime reconstructs: **ACTION** wall_jump /
> **TRIGGER** internal exploration intention / **WORLD** new reachable surface detected /
> **AFFORDANCE** wall_jump / **CAPABILITY** 0.87 confidence / **ALTERNATIVES** walk→rejected,
> leap→lower confidence, wall_jump→highest utility / **OUTCOME** success / **SIGNIFICANCE** moderate
> novelty / **LEARNING** wall_jump from this surface is reliable. → *"I noticed that wall was
> reachable and I wanted to explore the other side. Wall-jumping was the best route I knew I could
> make."* **Self-explanation grounded in actual cognition.**

**This is partially LIVE.** `self/decision_journal.py` (WO-082) already writes an append-only
`self/journals/decision_journal.jsonl` and reads it back. Its own docstring: *"Source of truth for
'why did you do that?' readback."* And `explain_last()`: *"Reads the real trace — **never fabricates
a motive**."*

**What the live record carries (verified):**

```jsonc
{
  "ts": …, "turn": "<first 120 chars of input>",
  "action": "build",                        // the Executive's chosen action
  "trigger": "explicit build phrase",       // ← cal_reason from runtime/executive.py
  "intent": "creation", "tone": "JOYFUL", "confidence": 0.9,
  "alternatives_rejected": [ {"rejected": "connect", "reason": "seam-a-override: …"} ],
  "overrides": ["safety-stabilisation" | "seam-a-routing"],
  "cognitive_load": "medium",
  "outcome": "success", "backend": "groq", "learning": ""
}
```

Plus `record_failure(action, condition_desc)` → writes a `known_failure_condition` entry and drops
that action's reliability by 0.15 into `self/journals/action_reliability.json`. `get_reliability()`
and `known_failures()` read it back. That is ADR-Exec-005 in miniature: **verified consequences, not
language, change future confidence** — and it is what lets eLo eventually say *"I don't think I can
do that"* with a cause behind it.

**Gaps vs David's shape (PENDING — named, not glossed):**

| David's field | Live? |
|---|---|
| ACTION | **YES** (`action`) |
| TRIGGER | **PARTIAL** — `trigger` is the *conversational* reason (`cal_reason`), not "internal exploration intention". No intent lane exists to name (§4.2). |
| WORLD | **NO** — the world state at decision time is not in the entry (it is pinned to the plan; not journalled) |
| AFFORDANCE | **NO** — affordances are in the snapshot, not the journal |
| CAPABILITY (confidence) | **PARTIAL** — `confidence` is the *decision's* confidence, not the capability's |
| ALTERNATIVES rejected | **YES, narrowly** — only reconstructed from override fields (`original_action`), not from a genuine candidate set that was scored and lost |
| OUTCOME | **YES** |
| SIGNIFICANCE | **NO** — Significance Engine (Vol V Ch.5) is not wired to the journal |
| LEARNING | **FIELD EXISTS, ALWAYS EMPTY** (`"learning": ""` is written literally; nothing populates it) |

**The honest read:** eLo can today explain *why he chose that conversational action*, truthfully and
from record. He cannot yet explain *why he moved*, because there is no intent lane, no journalled
affordance/world, and no populated learning. The mechanism is right; the coverage is thin.

## 4.5 The journal contract

```
Rules (MUST):

J1  ONE entry per decision, written after the decision, append-only. The journal is a record,
    never an input to the same turn (Reality Informs, Never Mutates).

J2  Every entry names its TRIGGER. An entry with an unknown trigger is written with
    "unknown" — never with a guessed one. (Live code already does exactly this.)

J3  Rejected alternatives are recorded WITH their reason — including rejected INTENTS
    (§4.3), not only rejected actions. This is the field David's example turns on.

J4  Failures are recorded as failures, with the condition, and they lower that action's
    reliability. Success does not silently raise it back (asymmetry is deliberate:
    a known failure condition is knowledge; a lucky success is not).

J5  Journal writes NEVER block a turn. (Live: every write is wrapped, "Silent on failure".)

J6  Readback is retrieval, not generation. explain_last() composes recorded fields into a
    sentence. If there is no record: "I don't have a decision trace yet" — never a story.
    Any future LLM phrasing of a why-answer is WORDING of retrieved fields (Ch.1 §1.5),
    and the answer is tiered like any other claim (Ch.3).

J7  The journal is eLo's, about eLo. It is NOT the relationship memory store (Vol VIII) and
    NOT the autobiography (Vol XXI). It is the decision layer those two draw from.
    Cross-boundary: the audit's Vol VIII finding — that eLo has no self-history record type —
    is answered from HERE plus the autobiography journal, not by widening relationship memory.

J8  Journalled content is subject to the same anti-fabrication rule as memory: an INFERRED
    trigger is recorded as inferred. eLo must not later read his own journal and treat a
    guess as a fact (ADR-Exec-005 — never learn from a hallucination).
```

## 4.6 Faculty Contract (the Intent + Journal roles)

```
Faculty:
  name:            ExecutiveIntent        # a ROLE of the Executive (Ch.1), NOT a new decider
  version:         0.1.0
  purpose:         Hold the dual-intent queue (external/conversational + internal/body-action),
                   rank it inside the one decision, commit at most one intent at a time, and
                   record every decision — chosen and rejected — so eLo can explain himself
                   from record rather than from narrative.
  contributes_to:  UnifiedCognitiveState (intent_queue component) → CognitivePlan (committed intent)
  runs_in:         response-path (queue read at assembly; arbitration inside DECIDE;
                   journal write immediately after DECIDE)

Inputs:
  - type: intent_proposal   source: David's utterance (external) · curiosity/agency/presence
                                    faculties (internal)                     required: false
  - type: capability_check  source: capability registry + affordances         required: true
    description: feasibility. An infeasible intent may be held, never committed.
  - type: boundary_check    source: presence/D-PRESENCE policy                required: true
  - type: absence_signal    source: user-idle perception (Ch.5 UP leg)        required: false
    description: raises internal pressure; drops Attention.David.
  - type: execution_ack     source: body/faculty ACK (WO-041)                 required: false
    description: satisfies (or fails) a committed intent.

Outputs:
  - type: committed_intent  destination: CognitivePlan
  - type: decision_trace    destination: self/journals/decision_journal.jsonl
  - type: reliability_delta destination: self/journals/action_reliability.json (failures only)

Dependencies:
  - faculty: ExecutiveAssembly (hard — the queue is a component, Ch.2)
  - faculty: Capability registry + Affordances (hard — feasibility before commitment)
  - faculty: Presence (hard — boundary check; D-PRESENCE)

Failure Modes:
  - condition: two intents tie after arbitration
    fallback:  prefer the EXTERNAL lane; if both external, prefer the explicit one; if still
               tied, ask rather than guess (relationship over cleverness, Vol XVI §4.2 step 5).
  - condition: a committed intent's capability goes OFFLINE mid-pursuit
    fallback:  the intent becomes blocked, NOT satisfied. eLo reports the block honestly
               (Ch.3 UNAVAILABLE). Never "I did it".
  - condition: the journal is unwritable
    fallback:  the turn proceeds; the gap is logged. And eLo must then answer "why did you do
               that?" with "I don't have a trace for that" — a missing record is a missing
               record, never an inferred story.
  - condition: an internal intent would intrude on David's space
    fallback:  refused at arbitration step 1. Space beats desire (D-PRESENCE).
```

## 4.7 Lifecycle & Envelope

Ratified lifecycle (`CONTRACTS.md §3`). The queue is read at assembly (`ACTIVE` → `PROCESSING`);
arbitration is inside DECIDE; the journal write is the tail of `PROCESSING` and is non-blocking.
Reliability updates and any `learning` population happen in the **integration window only** —
never inside the turn (ADR-Exec-005).

Envelope: intent proposals arrive as `payload.type: intent_proposal`; the committed intent rides the
plan; the trace is written to disk rather than broadcast (it is a record, not a message).
`context.significance` stays `0.0` — the Significance Engine (Vol V Ch.5) writes it, and wiring
significance into the journal is a named gap (§4.4).

## 4.8 Acceptance Tests

### Functional
```
FT-1  Two lanes exist
  Given David says "sit" while eLo has an active exploration urge,
  Then the queue holds BOTH, in different lanes, with the external one ranked above.

FT-2  One committed intent
  Given a queue with several intents, Then exactly one is `committed`; the rest are queued.

FT-3  Feasibility precedes commitment
  Given an intent requiring an OFFLINE capability, Then it is never committed;
  it is held or abandoned with a reason. eLo does not announce it.

FT-4  Boundary beats desire
  Given "take five" and a strong internal exploration urge,
  Then no internal intent commits. eLo is gone, not lurking. (D-PRESENCE.)

FT-5  Why-from-record
  Given the last action, When asked "why did you do that?",
  Then the answer is composed from the journal entry's action/trigger/alternatives/outcome —
  and every clause maps to a recorded field.

FT-6  No record ⇒ no story
  Given an empty journal, When asked "why did you do that?",
  Then eLo says he doesn't have a trace. He does NOT produce a plausible reason.

FT-7  Rejected intents are recorded
  Given exploration lost to a David request, Then alternatives_rejected names the exploration
  intent and why it lost — so "why didn't you go and look?" is also answerable.

FT-8  Failure lowers reliability
  Given an action fails with a condition, Then a known_failure_condition entry is written and
  that action's reliability drops; get_reliability reflects it.
```

### Stability
```
ST-1  Intents survive turns
  Given an intent committed on turn N and not satisfied, Then it is still committed on turn N+1
  (it did not evaporate with the turn).

ST-2  Absence raises the internal lane, does not force it
  Given David idle past threshold, Then internal pressure rises and exploration becomes
  eligible — AND it still loses instantly to David's next utterance.

ST-3  Blocked ≠ satisfied
  Given a committed intent whose capability drops mid-pursuit, Then status = blocked and eLo
  reports the block; the intent is never marked satisfied.

ST-4  Journal never blocks a turn
  Given the journal path is unwritable, Then the turn completes normally.

ST-5  No confabulation under model swap
  Given the backend changes, Then the why-answer's FACTS are identical; only wording differs.
```

### Integration
```
IT-1  David's own scenario (SOURCE_2026-08-08)
  Given eLo wall-jumps from an internal exploration intent,
  When David asks "why did you jump over there?",
  Then the answer names: the intent, the world observation that triggered it, the affordance,
  the capability confidence, and the rejected alternatives — all from record.
  (FAILS today: WORLD, AFFORDANCE, capability-confidence and real ALTERNATIVES are not
   journalled, and there is no intent lane. This is the completion test.)

IT-2  Absence report
  Given David is away, eLo explores, David returns,
  Then eLo can say what he did while away, from the journal — with no invented detail.

IT-3  Intent → Ch.3 tiering
  Given a why-answer, Then each claim in it carries its tier; anything not recorded is
  UNKNOWN and said as such.
```

## 4.9 Wiring to Live Anchors

- `self/decision_journal.py` (WO-082) — `record()`, `record_failure()`, `last_n()`,
  `explain_last()`, `get_reliability()`, `known_failures()`; `self/journals/decision_journal.jsonl`
  and `self/journals/action_reliability.json`. **This is the seed. Extend it — do not fork it.**
- `runtime/executive.py` — `cal_reason` is the live `trigger`; the action is the live `action`.
- `server.py` L2335 / L2360 / L2383 — the `original_action` / `overridden_by_*` fields the journal
  reads as `alternatives_rejected` and `overrides` (Ch.1 §1.6).
- `runtime/cognitive_snapshot.py` — `pending_intentions`, `BodySchema.queued_intent`: today's
  one-lane stub; the extension point for the dual queue.
- `runtime/capabilities/registry.py` + `runtime/affordances.py` — feasibility inputs.
- `runtime/the_moment.py` — `current_action`, `goal`, `available_actions` (the "what am I doing"
  side of the same picture).
- Presence layer / WO-045 ("take five") — the boundary check at arbitration step 1.
- Vol XXI / `self/journals/autobiography.jsonl` (CA spec, not yet built) — the narrative view over
  these records.

## 4.10 Cross-Volume Interaction

| Volume | Boundary |
|---|---|
| **VII Ch.2** | `intent_queue` is a component of the assembled state. The queue is READ at assembly and ranked inside DECIDE — never sensed mid-decision. |
| **VII Ch.3** | A why-answer is a claim and is tiered. A missing record is UNKNOWN, spoken. |
| **VII Ch.5** | Body intents are commanded DOWN and satisfied by ACKs coming UP. No UP leg ⇒ intents can never be verified satisfied. |
| **V Ch.10 (Agency)** | Agency owns *whether eLo may act autonomously at all*; this chapter owns *which of his wants wins this turn*. Agency gates the lane; arbitration ranks within it. |
| **VI (Attention)** | Attention decides what eLo *notices*; the intent queue holds what he *wants to do about it*. A novelty winning attention may PROPOSE an internal intent; it does not commit one. |
| **VIII (Memory)** | The journal is decision record, not relationship memory. The audit's "eLo has no self-history record type" finding is answered here + Vol XXI, not by widening Vol VIII's four types. |
| **XXI (Narrative)** | Derives the story ("I've been exploring more lately") from these records. Vol XXI derives from nothing if the journal stays this thin — which is exactly the audit's warning. |
| **XXVIII (Learning)** | `learning` and reliability updates are ADR-Exec-005 territory: verified consequences only, integration window only, policy not identity. |
| **XVI Ch.4** | Faculty-conflict resolution (there) vs intent arbitration (here). Distinct; both inside the one decision; safety veto common. |

## 4.11 Open Questions (for CA / David)

```
REQUIRES DECISION
  OQ-VII-4  THE ARBITRATION ORDER (§4.3) is INVENTED. David said "governance decides
            priority" and gave no order. The proposal (safety/boundary > external explicit >
            standing commitment > external implicit > internal high-pressure > curiosity)
            needs ratification. It touches D-PRESENCE and how often eLo asserts himself,
            so it is arguably David L3, not CA.

  Q4-a      The absence threshold. David and the CA both say 14 minutes, in examples.
            Is 14 the number, or is it illustrative? Recommend: make it a tunable with 14
            as the default, and make eLo's return-report contingent on having something
            real to report — never a manufactured errand.

  Q4-b      Does a STANDING COMMITMENT really outrank an implicit external thread (§4.3
            step 3 vs 4)? It is the difference between eLo finishing what he started and
            eLo being maximally responsive. This is a feel call.

  Q4-c      Journal enrichment scope: adding WORLD / AFFORDANCE / capability-confidence /
            SIGNIFICANCE / LEARNING to each entry (§4.4) makes the record fat. Confirm
            whether to journal the full pinned snapshot reference (cheap, one id) rather
            than copying fields (expensive, duplicative). Recommend: reference by turn_id
            into the pinned plan.

  Q4-d      Should eLo VOLUNTEER a why unprompted ("I noticed I wave a lot")? David's #6
            (habits) and the CA's self-observation both point that way, but it collides
            with "the Executive grows quieter". Recommend: rarely, and only from a
            crossed threshold — never as narration of ordinary turns.
```

## 4.12 References

- `_intake/SOURCE_2026-08-08_self_model_becoming.md` — VERBATIM: David #4 (the Intent Queue and its
  internal examples), #9 (absence awareness), the "Why did I do that?" capability block with the
  full ACTION/TRIGGER/WORLD/AFFORDANCE/CAPABILITY/ALTERNATIVES/OUTCOME/SIGNIFICANCE/LEARNING shape;
  CA Part 3 §C (dual-intent queue + Attention & Absence Matrix) and §D (self-history / habits).
- `SITUATED_SELF_v1_assembly.md` — CA additions 4 (dual-intent queue), 7 (self-history), 9 (absence).
- `DECISION_LOG.md` — ADR-Exec-006 (`intent_queue` named as a component), ADR-Exec-005
  (verified-consequence learning), ADR-Exec-001 (no unverified claims), D-PRESENCE.
- `ARCHITECTURAL_PRINCIPLES.md` — "Autonomous and commanded are one capability"; "Presence over
  engagement"; "The Executive grows quieter"; "Protect Wonder".
- `AUDIT_INTENT_core_brain_2026-08-10.md` — *"Dual-intent queue + governance arbitration. Homeless."*
  and *"No volume asks the Executive to record rejected alternatives."*
- Code: `self/decision_journal.py`, `runtime/cognitive_snapshot.py`, `runtime/executive.py`,
  `runtime/affordances.py`, `runtime/capabilities/registry.py`, `runtime/the_moment.py`.

---
```
Chapter 4 — The Intent Queue and "Why Did I Do That?"
Status: READY FOR REVIEW
Grounded in live code: self/decision_journal.py (WO-082) — append-only trace, trigger from
  cal_reason, alternatives_rejected from override fields, overrides, outcome, per-action
  reliability with known_failure_condition, explain_last() "never fabricates a motive"
Flagged PENDING: the dual-intent queue does not exist — pending_intentions holds at most
  ("sit","cursor"); no internal lane, no pressure, no feasibility, no arbitration.
  Journal gaps named field-by-field (WORLD · AFFORDANCE · SIGNIFICANCE · LEARNING always empty)
Flagged INVENTION: the arbitration order (OQ-VII-4) — David said only "governance decides priority"
Faculty Contract: Included · Journal Contract (J1–J8): Included · Lifecycle/Envelope: Included
Acceptance Tests: FT×8 ST×5 IT×3
Open Questions: 5 (OQ-VII-4, Q4-a, Q4-b, Q4-c, Q4-d)
Implementation: PARTIAL
```

READY FOR REVIEW
