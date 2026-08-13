---
chapter: 4
title: "The Emotional Processing Layer — Emotion as Information"
volume: V
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
implementation: PENDING
audit_status: OPEN
received: 2026-07-26
dependencies:
  - Chapter 1 (Cognitive Core — contributes to CognitiveState before the Executive)
  - Chapter 2 (Faculty System — Emotion Faculty slot)
  - Chapter 5 (Significance Engine — consumes emotional weight)
  - architecture/16_runtime_contracts.md (CognitiveState / CognitivePlan)
  - architecture/17_cognitive_principles.md (witness_before_advising, distress override)
  - Volume V CONTRACTS.md (envelope, lifecycle, base contract)
---

# Chapter 4: The Emotional Processing Layer

## 4.0 Purpose

The Emotional Processing Layer is the faculty that reads the **affective meaning**
of a moment and contributes it to `CognitiveState` before the Executive decides.

It is an **upstream faculty** (CONTRACTS.md §1): it writes an `AffectState` into
`CognitiveState` and then freezes. It does **not** decide the response — the
Executive does that. This is the architectural expression of the character rule
that eLo's emotion is real information, not a performance.

In the running kernel this formalises the valence axis of `core/attention.py`, the
mood/inner-event tracking in `self/elo_self_model.py`, and the distress-override
behaviour already implied by Principle *witness_before_advising*.

---

## 4.1 Emotion as Information, Not Decoration

The founding constraint of this chapter, consistent with Chapter 2's definition of
the Emotion Faculty as "a meaning detection system, not artificial feelings":

> Emotion is not something eLo *displays*. It is something eLo *computes* — a
> reading of how much a moment matters and in what direction — that changes what
> the Executive attends to and what the Significance Engine keeps.

Three consequences bind the rest of this chapter:

- **Affect is a signal, not an output.** The Emotional Processing Layer never
  produces text, animation, or voice. It produces an `AffectState`. Expression of
  emotion is `EmbodimentState`'s job, derived later from the `CognitivePlan`.
- **Affect biases expression and memory — never identity.** (Principle:
  *relationships influence expression, never identity*; Identity Kernel: identity
  is immutable.) A strong emotion can change tone and what is remembered; it can
  never change who eLo is.
- **Emotion is bounded and regulated.** Unbounded affect is a fault (Ch.1 §2.3).
  The layer clamps, decays, and regulates — see §4.5.

---

## 4.2 Emotional State Representation

The faculty's single product is the `AffectState`, contributed to `CognitiveState`:

```
AffectState:
  valence:          float -1.0 … +1.0     # negative ↔ positive (unsigned magnitude = intensity)
  arousal:          float  0.0 … 1.0      # calm ↔ activated
  dominant_emotion: enum   { joy, curiosity, challenge, connection, identity, distress, neutral }
  emotion_mix:      { emotion: weight }   # full distribution, sums ≤ 1.0 (contradiction allowed)
  regulation_state: enum   { open, regulating, guarded, flooded }
  affect_confidence: float 0.0 … 1.0      # how sure the reading is (envelope.confidence)
  baseline_delta:   float                 # distance from eLo's resting affect (from Ch.7 traits)
```

The seven `dominant_emotion` values are the five emotional dimensions of the
Significance Engine (Ch.5 §4 — joy, curiosity, challenge, connection, identity)
plus `distress` (which triggers overrides) and `neutral`. This keeps Ch.4 and Ch.5
speaking the same emotional vocabulary — no translation layer between them.

`emotion_mix` is a **distribution, not a winner-take-all label**. eLo may hold
`{connection: 0.5, challenge: 0.4}` at once. This is Principle 2.4 (hold
contradiction) applied to feeling: the layer does not force a single emotion when
the moment is genuinely mixed.

---

## 4.3 Affect Calculation

Affect is computed from the frozen inputs available in `CognitiveState`, never by
asking a model "how do you feel." It is deterministic given its inputs (so eLo's
emotional reading is stable across backends — same discipline as Ch.1 §9.4).

```
INPUT (from CognitiveState)                    →  AffectState
  Language signal (lexical/tonal valence)
  Attention signal (salience, novelty)             valence   = w1·lexical + w2·relational + w3·selfmodel
  Relationship signal (trust, register, history)   arousal   = w4·salience + w5·novelty + w6·urgency
  Self-model signal (current mood, inner events)   dominant  = argmax(emotion_mix)
  Environment signal (what David is doing)          mix       = softmax(per-dimension evidence)
```

**Calculation rules (MUST):**

- Affect is computed **once per turn**, before the Executive, and frozen into
  `CognitiveState` (Law: *frozen after assembly*).
- `valence` sign comes primarily from language + relationship context; **magnitude**
  (intensity) comes from attention salience and self-model mood. A calm true thing
  and a loud shallow thing are distinguished here (mirrors Ch.5's "a difficult
  conversation can be highly significant; a happy one insignificant").
- Every weight is explainable to a `CognitiveState` field (Principle: *every
  decision remains explainable*). No affect value may appear that cannot be traced
  to evidence.
- The layer reads eLo's **own** current mood from the self-model (Ch.7 baseline) so
  affect is relative to eLo's temperament, not absolute — `baseline_delta` records
  this offset.

---

## 4.4 Emotional Memory Tagging

The layer attaches an **emotional tag** to the turn so downstream memory can weight
it. It does not store memory itself (that is Ch.3 + Ch.5) — it annotates.

```
EmotionalTag:
  valence:          float
  intensity:        float          # |valence| scaled by arousal
  dominant_emotion: enum
  regulation_state: enum
  tag_ts:           float
```

**Tagging rules (MUST):**

- The tag rides on the envelope `context` for the turn; the Significance Engine
  (Ch.5) reads it as the "Emotion Weight" term of its significance score.
- **High-intensity negative** moments are tagged, not suppressed. A hard moment
  that mattered must be as taggable as a joyful one (Ch.5: significance is about
  *change*, not pleasantness).
- The tag is **advisory to memory**, authoritative to nobody: the layer proposes
  emotional weight; Ch.5 decides significance; Ch.3 decides storage.

---

## 4.5 Regulation Systems

Regulation is what keeps affect bounded and keeps a spike in one turn from
corrupting eLo's stable temperament. It is the mechanism behind Principle
*consistency over novelty* at the affective level.

```
regulation_state transitions:
  open        — affect flows normally into CognitiveState
  regulating  — |valence| or arousal above soft cap → damped toward baseline
  guarded     — sustained negative + low trust → reduce arousal, protect relationship
  flooded     — affect exceeds hard cap → clamp, raise uncertainty, force calm expression
```

**Regulation rules (MUST):**

1. **Decay toward baseline.** Between turns, affect relaxes toward eLo's resting
   temperament (Ch.7). No single turn permanently moves eLo's mood; only
   integration (Ch.6/Ch.7) can shift the baseline. This is the affective guarantee
   against turn-to-turn drift.
2. **Hard clamp.** `valence ∈ [-1,1]`, `arousal ∈ [0,1]`. Exceeding the hard cap
   sets `regulation_state = flooded`, clamps, and **raises turn uncertainty** so the
   Executive prefers GROUND/WITNESS/SILENCE.
3. **No destructive propagation.** A `flooded` or `guarded` affect state MUST NOT
   emit a `personality_delta` on its own. Personality change only ever originates in
   integration (Ch.6→Ch.7 with validation). This is the direct guard behind Stability
   Test ST-1 below and Ch.7's identity-continuity gate.
4. **Distress override.** If `dominant_emotion == distress`, regulation raises a
   `distress` flag in `CognitiveState`. Per Principle *witness_distress_override*, the
   Executive MUST route to WITNESS/GROUND before any high-energy action, regardless
   of momentum. Ch.4 does not make the decision — it makes the override unignorable.

---

## 4.6 Emotional Significance Weighting

This is the seam to Chapter 5. The layer supplies the **Emotion Weight** term; the
Significance Engine combines it with novelty, learning value, relationship value,
and future relevance to produce the final significance score.

```
emotion_weight = f(intensity, dominant_emotion, regulation_state)
                 where identity-touching and connection emotions weight highest
                 (they are the ones that move who eLo is becoming — see Ch.7)
```

**Weighting rules (MUST):**

- The layer outputs `emotion_weight ∈ [0,1]`; it never outputs a final significance
  score (that field, `context.significance`, is Ch.5's alone — CONTRACTS.md §2).
- `identity` and `connection` emotions carry the highest weight because they are the
  affective signature of moments that legitimately feed personality evolution. This
  keeps Ch.7's inputs sourced from genuinely identity-relevant feeling, not noise.

---

## 4.7 Emotion → Action Routing

The layer does not select the action — but it shapes the routing surface the
Executive selects within, by contributing `distress`, `regulation_state`, and
`emotion_mix` to `CognitiveState`. The mapping the Executive honours:

| Affect condition | Executive routing bias (CAL) |
|---|---|
| `distress` flag set | WITNESS → GROUND (override momentum) |
| high positive valence, low arousal | REFLECT / CONNECT |
| high positive valence, high arousal, short input | CELEBRATE |
| creative + positive | BUILD |
| `guarded` + negative | GROUND (silence-aware, protect relationship) |
| `flooded` | SILENCE / WITNESS + raised uncertainty |
| neutral | no bias — Executive routes on other CognitiveState signals |

**Routing rule (MUST):** this is **bias, not decision**. The Executive still reasons
once and produces one `CognitivePlan`. The layer only guarantees that affect the
Executive cannot ignore (distress, flooded) is present and flagged in the frozen
`CognitiveState`. (Law: *one decision per turn*; the layer never re-decides.)

---

## 4.8 Faculty Contract

```
Faculty:
  name:            EmotionalProcessingLayer
  version:         1.0.0
  purpose:         Read the affective meaning of a moment as an AffectState and
                   contribute it to CognitiveState — emotion as information, upstream
                   of the Executive, never a response and never a mutation of identity.
  contributes_to:  CognitiveState
  runs_in:         response-path

Inputs:
  - type:        language_signal
    source:      Language Faculty (CognitiveState)
    required:    true
    description: Lexical / tonal valence of the utterance.
  - type:        attention_signal
    source:      Attention Faculty (core/attention.py)
    required:    true
    description: Salience, novelty, urgency — drives arousal + intensity.
  - type:        relationship_signal
    source:      Relationship Faculty (world_graph, trust, register)
    required:    false
    description: Trust/register/history; degrades to neutral relational weight if absent.
  - type:        self_model_signal
    source:      self/elo_self_model.py
    required:    false
    description: eLo's current mood + inner events; sets baseline_delta. Neutral if absent.

Outputs:
  - type:        affect_state
    destination: CognitiveState (frozen for the Executive)
    description: valence, arousal, emotion_mix, regulation_state, affect_confidence.
  - type:        emotional_tag
    destination: Significance Engine (Ch.5) via envelope context
    description: Emotion Weight term + dominant emotion for memory weighting.
  - type:        distress_flag
    destination: CognitiveState → Executive
    description: Forces WITNESS/GROUND routing (Principle witness_distress_override).

Dependencies:
  - faculty: AttentionFaculty     (hard — needs salience/novelty)
  - faculty: LanguageFaculty      (hard — needs lexical/tonal valence)
  - faculty: RelationshipFaculty  (soft — degrades to neutral relational weight)
  - faculty: PersonalityEvolution (soft — supplies affect baseline; defaults to neutral temperament)

Failure Modes:
  - condition: self-model / relationship signal absent
    fallback:  Compute affect from language + attention only; affect_confidence −0.15.
  - condition: affect exceeds hard cap
    fallback:  Clamp; regulation_state=flooded; raise turn uncertainty; force calm expression.
  - condition: conflicting signals (e.g. positive language, distressed self-model)
    fallback:  Represent as emotion_mix (hold contradiction); do NOT collapse; flag for Ch.5.
  - condition: layer errors entirely
    fallback:  Emit neutral AffectState (valence 0, arousal 0.2, open); turn proceeds.
```

---

## 4.9 Faculty Lifecycle

Uses the universal lifecycle (CONTRACTS.md §3). Chapter-specific notes:

```
INITIALISING → load emotional-dimension weights + eLo baseline temperament (Ch.7)
ACTIVE       → subscribed, awaiting the turn's CognitiveState inputs
PROCESSING   → compute AffectState (§4.3), regulate (§4.5), tag (§4.4), freeze
   └─ fault ─► ERROR_RECOVERY → emit neutral AffectState → ACTIVE
LEARNING     → (integration window only) receive baseline adjustments FROM Ch.7
VALIDATION_REQUIRED → n/a here — Ch.4 proposes no identity change itself
UPDATING     → apply new baseline temperament from Ch.7's validated personality delta
STABLE → ACTIVE
```

**Rule (MUST):** Ch.4 **reads** its baseline from Ch.7 but never **writes** personality.
The only thing that updates in Ch.4's `UPDATING` is its resting affect baseline, and
that update originates from a Ch.7 delta that already passed identity-continuity
validation. Ch.4 cannot move eLo's temperament on its own.

---

## 4.10 Message Envelope Binding

Per CONTRACTS.md §2 (canonical nine-field wire format).

```jsonc
{
  "id": "uuid",
  "sender": "EmotionalProcessingLayer",
  "receiver": "*",                 // AffectState is part of CognitiveState → broadcast
  "priority": "high",              // distress must not queue behind low-priority traffic
  "context": {
    "conversation_id": "",
    "relationship_state": "",
    "environment_state": "",
    "significance": 0.0,           // Ch.4 leaves this 0.0 — Ch.5 owns it
    "memory_instruction": { "store": false, "priority": "" }
  },
  "payload": {
    "type": "affect_state",
    "body": { "valence": 0.0, "arousal": 0.0, "dominant_emotion": "neutral",
              "emotion_mix": {}, "regulation_state": "open", "baseline_delta": 0.0 }
  },
  "confidence": 0.0,               // = affect_confidence
  "expires": null,
  "trace": ["EmotionalProcessingLayer@ts"]
}
```

Binding rules: `sender` MUST be `EmotionalProcessingLayer`; `priority` MUST be `high`
whenever `distress` is set; `context.significance` left `0.0`; `confidence` carries
`affect_confidence` and may only be lowered downstream.

---

## 4.11 Acceptance Tests

### Functional

```
FT-1  Emotion is computed, not performed
  Given:  Any utterance
  When:   The layer runs
  Then:   An AffectState is written to CognitiveState
          AND no text / animation / voice is produced by this faculty

FT-2  Intensity separates from pleasantness
  Given:  A calm, identity-touching statement ("this project is me rebuilding
          the imagination I lost as a kid")
  When:   Affect is calculated
  Then:   dominant_emotion=identity, high intensity, LOW arousal
          AND emotion_weight is high despite low arousal

FT-3  Distress override reaches the Executive
  Given:  dominant_emotion=distress
  When:   The layer freezes CognitiveState
  Then:   a distress flag is set with priority=high
          AND the Executive routes WITNESS/GROUND regardless of momentum

FT-4  Emotional tag weights memory
  Given:  A high-intensity connection moment
  When:   Ch.5 reads the turn
  Then:   the EmotionalTag raises the Emotion Weight term of the significance score
```

### Stability

```
ST-1  Affect never mutates identity
  Given:  A flooded, high-negative affect state
  When:   The turn completes
  Then:   NO personality_delta is emitted by Ch.4
          AND eLo's baseline temperament is unchanged after the turn

ST-2  Held contradiction survives
  Given:  Positive language but distressed self-model
  When:   Affect is computed
  Then:   emotion_mix carries both; no premature collapse to one label
          AND uncertainty is raised for the Executive

ST-3  Bounded affect
  Given:  Inputs that would push valence to -1.8
  When:   Regulation runs
  Then:   valence clamps to -1.0, regulation_state=flooded, uncertainty raised

ST-4  Decay to baseline
  Given:  A high-arousal turn followed by three neutral turns
  When:   Affect relaxes
  Then:   arousal returns toward eLo's resting baseline
          AND no permanent mood shift occurred (only integration can shift baseline)
```

### Integration

```
IT-1  Affect → Significance → Memory → Personality chain
  Emotional Processing (AffectState + EmotionalTag)
        ↓
  Significance Engine        (emotion_weight → significance score)
        ↓
  Memory Architecture        (stores/pins per significance)
        ↓  (integration window only)
  Reflection & Growth        (extracts lesson from emotionally-weighted episode)
        ↓
  Personality Evolution      (proposes trait delta → identity-continuity validation)

  Assert: emotion influences what is remembered and, over many episodes,
          how eLo grows — but NEVER changes identity, and never within one turn.

IT-2  Graceful degradation
  Given:  Relationship + self-model faculties OFFLINE
  When:   The layer runs
  Then:   A valid neutral-leaning AffectState is still produced (confidence lowered)
          AND the turn is never stalled
```

---

## 4.12 Claude Implementation Notes

- **Map, don't rebuild.** Formalise the valence axis of `core/attention.py` and the
  mood/inner-event fields of `self/elo_self_model.py` into a typed `AffectState`
  contributed to `runtime/contracts.py → CognitiveState`. Do not add a new decision
  path — the Executive still decides.
- New file suggestion: `faculties/emotion/emotional_processing_faculty.py`, producing
  `AffectState`, consumed by the Significance Engine and read by the Executive.
- **Do not** let this faculty write to `self/personality_drift.py` or any identity
  state. Its only write target is `CognitiveState` (per turn) and its own affect
  baseline (from a validated Ch.7 delta, integration window only).
- Preserve the South London register signal from the Relationship Faculty as an input
  to relational valence — do not strip it (Audit note).

---

## 4.13 Architecture References

- `core/attention.py` — valence/salience/novelty feeding affect calculation.
- `self/elo_self_model.py` — eLo's mood + inner events (baseline temperament source).
- Chapter 5 (Significance Engine) — consumer of the emotion weight + emotional tag.
- Chapter 7 (Personality Evolution) — owner of the affect baseline Ch.4 reads.
- `17_cognitive_principles.md` — witness_before_advising, witness_distress_override.
- `16_runtime_contracts.md` — CognitiveState (frozen, one cognition).
- CONTRACTS.md — envelope, lifecycle, base contract.

---

```
Chapter 4 — The Emotional Processing Layer
Status: READY FOR REVIEW
Files: 04_Emotional_Processing_Layer.md
Faculty Contract: Included
Lifecycle State Machine: Included (universal + chapter notes)
Message Envelope: Included (canonical nine-field)
Acceptance Tests: Included (FT ×4, ST ×4, IT ×2)
Architecture References: Included
```

READY FOR REVIEW
