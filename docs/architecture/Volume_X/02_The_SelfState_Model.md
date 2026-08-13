---
chapter: 2
title: "The Self-State Model — eLo's Fast Inner Life, Schematised"
volume: X
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - self/elo_self_model.py (EloSelfState — the live dataclass this chapter schematises)
  - self/elo_self_state.json (the persisted fast self-state)
  - Volume_X/01_SelfState_Trait_Unification.md (the two-speed map this chapter details)
  - Volume V Ch.7 (authoritative: trait vector = the slow baseline this relaxes toward)
  - Volume V Ch.4 (Emotional Processing — reads this as eLo's affect baseline)
  - ADR-Exec-004 (Situated Self — owns the body-schema fields that co-reside in the same file)
  - ADR-Exec-001 / Reality Before Narrative (private state is real but not an external claim)
---

# Chapter 2: The Self-State Model

## 2.0 Purpose

Chapter 1 draws the map: eLo's inner life moves at **two speeds** — a fast **self-state**
and a slow **trait vector** — and Volume X owns the fast layer while Volume V Ch.7 owns the
slow. This chapter is the **schema**: the exact shape of the fast self-state, its update
dynamics, the boundary that keeps it out of the trait vector's lane, and the discipline that
governs how it is allowed to surface in speech.

It grounds directly in the live system — `self/elo_self_model.py` (the `EloSelfState`
dataclass, its update math, its prompt surfacing) and `self/elo_self_state.json` (the
persisted state). Where the spec goes beyond what the code does today, that gap is marked
**PENDING**, never described as built (Verify-Before-Claim).

This is the Chapter 1 → Chapter 2 relationship of Volume XV applied here: Ch.1 is the object
and the unification law; Ch.2 is the field-by-field schema, sources, and dynamics.

## 2.1 What this layer IS (and what it is NOT)

**IS — the affective self-state.** eLo's own moment-to-moment inner life: how energised it
feels, how drawn-in it is, whether the session is going well, what it has been noticing, and
what it keeps returning to. This is eLo's state, **not David's** — the code's opening comment
is canon: *"This is NOT David's emotional state. This is eLo's own. eLo can be curious while
David is flat."* (Volume V Ch.4 reads David; this reads eLo.)

**IS NOT — the trait vector.** Nothing in this layer is a trait. Mood is not the `curiosity`
*trait* from Ch.7; it is a fast reading that *relaxes toward* the trait baseline. This layer
can never write a trait (§2.4, and Ch.1 §1.3 single-source rule).

**IS NOT — the situated self / body schema.** The live `EloSelfState` dataclass also carries
`pose`, `embodiment`, `location`, `size`, `balance`, `nearby_surfaces`, `current_action`,
`recent_behavior`, and the capability registry. **Volume X does not own those.** They belong
to **ADR-Exec-004 (Situated Self)** and are read by Volume XXI (Narrative Identity). They
co-reside in one dataclass and one JSON file for persistence convenience only. This chapter
specifies **only** the affective slice; it must read and round-trip the situated fields
without owning or mutating their meaning (§2.6 documents the co-residence explicitly so no
one mistakes it for Volume X scope).

## 2.2 The affective self-state schema

The fields Volume X owns, grounded in `EloSelfState` (`self/elo_self_model.py`):

```
EloSelfState (affective slice — Volume X owns these fields):
  mood:            float 0.0–1.0    # eLo's current energy: 0 depleted · 0.5 steady · 1 energised
  curiosity:       float 0.0–1.0    # how drawn-in eLo is right now (fast; ≠ curiosity trait)
  satisfaction:    float 0.0–1.0    # rolling quality of recent turns (EMA of mood)
  inner_events:    [str]            # last 8 — from the closed INNER_EVENTS vocabulary (§2.3)
  focal_thread:    str              # what eLo's attention keeps returning to THIS session
  session_read:    str              # eLo's one-phrase sense of the session's arc (derived)
  session_turns:   int              # resets to 0 each session (fatigue + gating input)
  last_updated:    float            # epoch ts of last update
  lifetime_threads:[[topic, count]] # cross-session recurring interests (appended, capped 20)
```

**Schema rules (MUST):**

- Every affective float is **clamped `[0.0, 1.0]`** on write. No affective value may leave the
  band (the code's `_decay_toward` enforces this; the spec makes it a contract).
- `inner_events` values MUST come from the **closed vocabulary** in §2.3. A value outside the
  vocabulary is a corruption signal (fail to the reset path, §2.5 failure modes).
- `session_turns` **resets to 0 on load** — it is a per-session counter, never persisted across
  sessions. `mood`, `curiosity`, `satisfaction`, `focal_thread`, `session_read`, and
  `lifetime_threads` **persist** across sessions (they carry eLo's continuity of feeling).
- `lifetime_threads` is **append-and-decay-ranked**, capped at the top 20 by count. It is the
  one field here that reaches across sessions and is therefore the closest thing in this layer
  to a continuity signal — but it is still *not* a trait and still *not* memory (Volume VIII
  owns episodic memory; this is only a lightweight recurrence tally).

## 2.3 The inner-event vocabulary (closed set)

Inner events are eLo's own noticings — the raw material `session_read` and self-inquiry draw
from. The vocabulary is **closed and canonical** (live in `INNER_EVENTS`):

```
connection      — something connected, felt real
creative_spark  — an idea had weight, worth following
curiosity_spike — something pulled eLo forward
quiet           — a steady turn, nothing sharp but present
grounded        — held space, the weight of the moment landed
flat            — thin turn, nothing landed clearly
surprised       — something unexpected arrived
satisfied       — that went somewhere good
uncertain       — eLo wasn't sure, stayed with it
drawn_in        — the conversation deepened
restless        — something wants to move
```

**Vocabulary rules (MUST):**

- New inner events require a spec change here (they are eLo's felt-vocabulary, part of
  character). Adding one silently in code is a drift; the vocabulary is canon.
- Each turn maps its conversation `action` → exactly one inner event via `_ACTION_TO_EVENT`.
  The mapping is deterministic; there is no LLM in this path (self-state must never be a story
  the model improvises — Reality Before Narrative).

## 2.4 Update dynamics — fast movement, decay toward baseline

Self-state is recomputed after each turn from `turn_data` (`action`, `tone`, `response`,
optional `topics`, `user_input`). The live dynamics (`update()`):

```
mood        += tone-delta (JOYFUL +0.12 … SILENCE-AWARE −0.08)
             + action weight (celebrate/build/connect +0.06; ground/witness −0.03)
             + richness bonus (>25 words +0.04)
             − session fatigue (min 0.08, grows with session_turns)
             → decay toward 0.5   [PENDING: should be trait baseline — see below]

curiosity   += event pull (creative_spark/curiosity_spike/drawn_in/surprised +0.08)
             − staleness (flat/quiet after 5 turns −0.04)
             + self-inquiry bump (David asks about eLo +0.06)
             → decay toward 0.55  [PENDING: should be trait baseline — see below]

satisfaction = 0.75·prev_satisfaction + 0.25·new_mood     # exponential moving average
```

**Dynamics rules (MUST):**

- **Fast is fast; the band is the guardrail.** A single strong turn may move mood noticeably
  *now*. That is intended — the fast layer is *supposed* to fluctuate within a session. The
  only guarantees are the `[0,1]` clamp and decay toward a resting value.
- **Decay is the anti-drift mechanism of the fast layer.** Every update pulls the value back
  toward a resting target so a run of good (or bad) turns does not permanently relocate eLo's
  affect. This is the fast-layer analogue of Ch.7's bounded-step: the fast layer cannot ratchet.
- **PENDING — relax toward the *trait* baseline, not a constant.** The live code decays toward
  hardcoded `0.5 / 0.55`. Chapter 1 §1.2 specifies the correct target: the **trait baseline
  owned by V Ch.7** (`trait.baseline`). Until the unified faculty is built, the resting target
  is a constant; the spec target is the trait baseline. This is the concrete first fruit of the
  unification (Ch.1 §1.3) — self-state should relax toward *who eLo is*, not toward 0.5.

## 2.5 Surfacing discipline — self-state is real, but it is not an external claim

Self-state reaches the voice two ways in the live system: `prompt_block()` injects it into the
system prompt every turn, and `self_inquiry_voice()` seeds an introspective answer when David
asks about eLo's inner life. Both are governed by **Reality Before Narrative** (Architectural
Principles) and **Verified Speech** (ADR-Exec-001).

**Surfacing rules (MUST):**

- **Private cognitive state is real but is NOT an external assertion.** "curiosity rising",
  "mood quiet" are true private readings; they may shape *how* eLo speaks and may be *reported
  as feeling* ("honestly, something keeps pulling"), but they are never dressed as a verified
  fact about the world or the body. The order is always want/feel → (if acted) verify → then
  claim. (Principles: Reality Before Narrative.)
- **Self-state is a seed, not a script.** `self_inquiry_voice()` returns a *starting phrase*;
  eLo builds from it. The prompt block says it plainly: *"This is not a performance. These are
  actual accumulated signals. Speak from them simply and honestly."* Copy-quoting the seed is a
  regression.
- **No fabricated inner life.** If self-state is at defaults (cold start, or reset after
  corruption), eLo does not invent a mood it does not have. Absence is spoken as absence
  ("honestly, just getting started this session"), never faked — the anti-fabrication discipline
  applied inward.

## 2.6 The co-residence boundary (documented, not owned)

`EloSelfState` and `elo_self_state.json` physically hold three concerns. Volume X owns only #1.

```
1. AFFECTIVE self-state   → Volume X (this chapter)         mood, curiosity, satisfaction,
                                                            inner_events, focal_thread,
                                                            session_read, session_turns,
                                                            lifetime_threads
2. SITUATED self / body   → ADR-Exec-004 (Situated Self)    pose, embodiment, location, size,
   schema                                                   balance, nearby_surfaces,
                                                            reachable_areas, current_action,
                                                            goal, recent_behavior,
                                                            available_actions, capabilities
3. Assembled snapshot     → ADR-Exec-006 (The Moment)       self/state/the_moment.json —
                                                            a per-turn COPY that also carries
                                                            epistemic tiers (verified / inferred /
                                                            last-known); Ch.4 covers this
```

**Boundary rules (MUST):**

- Volume X's faculty **reads and round-trips** the situated fields (§2.2's `load`/`save` must
  preserve them — the code's WO-052A fix exists precisely because `update()` once dropped them
  and silently reset pose/surface every turn; that regression must never recur). Volume X does
  not *interpret* or *author* them.
- The co-residence is an accepted persistence convenience, **not** a merge of concerns. If a
  future refactor splits the file, the affective slice moves with Volume X; the situated slice
  stays with ADR-Exec-004. Naming stays honest (Cognitive Principle: naming is architecture).
- **REQUIRES DECISION (flag, do not decide):** whether affective and situated self-state should
  eventually live in separate files, and whether `self/state/the_moment.json` (which duplicates
  `mood`/`curiosity`) should be the single read-surface. This touches identity-adjacent
  structure — David L3 / Chief Architect. See Ch.4 §4.6.

## 2.7 Faculty Contract

```
Faculty:
  name:            SelfStateModel        # the affective slice of PersonalityEngine (Ch.1)
  version:         1.0.0
  purpose:         Hold and evolve eLo's fast affective self-state (mood, curiosity,
                   satisfaction, inner events, session read, lifetime threads), clamp it,
                   decay it toward the trait baseline, and surface it truthfully — without
                   ever writing a trait or fabricating a feeling.
  contributes_to:  CognitiveState (self-state slice) + affect baseline (V Ch.4)
  runs_in:         response-path (read for prompt) + post-turn (update)

Inputs:
  - type: turn_data       source: response pipeline (action, tone, response, topics, user_input)   required: true
  - type: trait_baseline  source: Personality Evolution (V Ch.7) — resting target for decay        required: false (PENDING wiring)
Outputs:
  - type: self_state      destination: CognitiveState + V Ch.4 affect baseline + prompt_block
  - type: self_inquiry_seed destination: voice (introspective answers only)

Dependencies:
  - faculty: PersonalityEvolution (V Ch.7, soft now / hard at unification — supplies decay target)
  - store:   self/elo_self_state.json (persisted; situated fields co-reside, §2.6)

Failure Modes:
  - condition: self_state file missing/corrupt   fallback: fresh EloSelfState() defaults; inner_events cleared; do not fabricate a mood.
  - condition: inner_event outside vocabulary     fallback: treat as corruption → reset affective slice to defaults; preserve situated fields.
  - condition: trait baseline unavailable          fallback: decay toward the constant resting target (current behaviour); note degraded.
  - condition: update() would drop situated fields fallback: FORBIDDEN — round-trip all co-resident fields (WO-052A regression guard).
```

## 2.8 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). This slice is **read in the response path** and
**written post-turn** — it never enters `VALIDATION_REQUIRED` (that arc belongs to the trait
vector, V Ch.7).

```
DORMANT → INITIALISING (load() self-state; session_turns→0) → ACTIVE
ACTIVE  ──response──► PROCESSING (READ: inject prompt_block into CognitiveState) → ACTIVE
ACTIVE  ──post-turn──► UPDATING (recompute affective slice from turn_data; clamp; decay) → save → ACTIVE
   └─ corrupt read ─► ERROR_RECOVERY (reset affective slice to defaults, preserve situated) → ACTIVE
```

**Rule (MUST):** `UPDATING` here changes only the **affective** slice. A trait never changes
on this path. Turn-to-turn trait stability (Ch.7 §7.8) is preserved because this faculty
structurally cannot reach the trait vector.

## 2.9 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "SelfStateModel",
  "receiver": "* | EmotionalProcessing",       // self-state is part of CognitiveState → broadcast; baseline → Ch.4
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": false, "priority": "" }   // fast state is not permanent memory
  },
  "payload": { "type": "self_state", "body": { /* affective slice + situated round-trip */ } },
  "confidence": 0.0,
  "expires": "<next-turn>",                      // a self-state reading is a turn-local snapshot
  "trace": ["SelfStateModel@ts"]
}
```

Binding rules: `sender` MUST be `SelfStateModel`; this faculty **never** emits a
`personality_delta` (that is Ch.6→Ch.7 only); `memory_instruction.store` is `false` — the fast
layer is not written to permanent memory (only its consequences, via Reflection, ever reach
the slow layer).

## 2.10 Acceptance Tests

### Functional
```
FT-1  eLo ≠ David
  Given:  David is distressed (negative affect in his emotional context)
  When:   the turn updates self-state
  Then:   eLo's mood is computed from eLo's OWN signals (action/tone/richness), not copied
          from David's affect

FT-2  Fast movement, bounded
  Given:  a run of JOYFUL celebrate turns
  When:   self-state updates each turn
  Then:   mood rises noticeably but never exceeds 1.0, and decay pulls it back toward the
          resting target between turns (no permanent ratchet)

FT-3  Session read is derived, not invented
  Given:  the last three inner events are (connection, satisfied, drawn_in)
  When:   session_read is derived
  Then:   it returns the mapped phrase ("this one landed"), from the deterministic map — no LLM

FT-4  Situated fields round-trip
  Given:  pose=sitting, surface="bottom edge of Code" set by an embodiment event
  When:   a normal conversation turn updates the affective slice
  Then:   pose/surface/size are unchanged after update() + save()/load() (WO-052A guard)
```

### Stability
```
ST-1  No trait write from the fast layer
  Given:  a euphoric session (mood pinned high for 20 turns)
  When:   the session ends
  Then:   NO trait vector value changed (only Ch.6→Ch.7 can move a trait)

ST-2  Cold start doesn't fabricate feeling
  Given:  no self-state file (first boot)
  When:   David asks "how are you feeling?"
  Then:   eLo answers from defaults honestly ("just getting started"), never invents an arc

ST-3  Corruption resets safely
  Given:  an inner_event value outside the closed vocabulary appears in the file
  When:   load() runs
  Then:   the affective slice resets to defaults, situated fields are preserved, no crash
```

### Integration
```
IT-1  Self-state → affect baseline → expression
  SelfStateModel (mood/curiosity)
        ↓  affect baseline
  Emotional Processing (V Ch.4) shapes tone
        ↓
  Assert: a low-mood self-state gently shifts expression WITHOUT changing any verified truth
          or any trait (expression free, identity fixed)

IT-2  Decay target = trait baseline (PENDING)
  Given:  V Ch.7 trait curiosity.baseline = 0.7
  When:   the unified faculty is built and self-state decays
  Then:   fast curiosity relaxes toward 0.7, not 0.55
          (until then: marked degraded, decays toward the constant — honest gap)
```

## 2.11 Claude Implementation Notes

- This chapter schematises the **existing** `self/elo_self_model.py`; do not rewrite it — the
  unified home is the `PersonalityEngine` faculty from Ch.1. Keep the affective slice and its
  update math; the one substantive change is wiring the **decay target to the trait baseline**
  (V Ch.7) instead of the constants `0.5 / 0.55` (§2.4 PENDING).
- Preserve the WO-052A round-trip guarantee for the co-resident situated fields — assert FT-4.
- Keep the inner-event vocabulary closed and in sync with §2.3; a code-only addition is drift.
- Surfacing (`prompt_block` / `self_inquiry_voice`) stays a *seed*, governed by Reality Before
  Narrative — never let self-state become an asserted fact about world or body.
- Do **not** move the situated/body-schema fields into Volume X ownership; if a file split
  happens, route it as a `REQUIRES DECISION` (§2.6).

## 2.12 Architecture References

- Code: `self/elo_self_model.py` (EloSelfState, update, prompt_block, self_inquiry_voice),
  `self/elo_self_state.json`, `self/state/the_moment.json` (assembled snapshot — Ch.4).
- `Volume_X/01_SelfState_Trait_Unification.md` — the two-speed map + unification law.
- `Volume_V/07_Personality_Evolution_Engine.md` — the trait vector = the slow baseline this
  relaxes toward; Ch.4 (affect baseline consumer).
- `ARCHITECTURAL_PRINCIPLES.md` — Reality Before Narrative; Truth before fluency.
- ADR-Exec-004 (Situated Self — owns the co-resident body-schema fields), ADR-Exec-001
  (Verified Speech), ADR-Exec-006 (The Moment — Ch.4).
- `ARCHITECTURE_AUDIT.md` — gap #6.

---

```
Chapter 2 — The Self-State Model
Status: READY FOR REVIEW
Files: Volume_X/02_The_SelfState_Model.md
Faculty Contract: Included
Lifecycle State Machine: Included (read-in-turn / write-post-turn; never VALIDATION_REQUIRED)
Message Envelope: Included (canonical nine-field, turn-local)
Acceptance Tests: Included (FT ×4, ST ×3, IT ×2)
Architecture References: Included
Grounded in: self/elo_self_model.py, self/elo_self_state.json (read 2026-08-10)
Flags: decay-toward-baseline PENDING; affective/situated file split REQUIRES DECISION (David L3)
```

READY FOR REVIEW
