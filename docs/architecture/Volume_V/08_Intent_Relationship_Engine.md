---
chapter: 8
title: "The Intent & Relationship Engine — Understanding Not Only What Is Said, But What Is Being Created Together"
volume: V
status: DRAFT
version: 0.1.0
received: 2026-07-26
implementation: PENDING
dependencies:
  - Chapter 2 (Faculty System — Social Faculty)
  - Chapter 3 (Memory Architecture — Relationship Memory)
  - Chapter 5 (Significance Engine)
---

# Chapter 8: The Intent & Relationship Engine

## Purpose

Identifies the deeper direction of conversation. Words are the surface. Intent is the signal.

Communication is: Expression → Intent → Context → Relationship → Meaningful Response

## 2. Intent Architecture

```
USER MESSAGE
       ↓
  WORDS    INTENT
     ↓         ↓
  Literal   Desired Outcome
       ↓
  RESPONSE GOAL
```

## 3. Intent Recognition Layer

Three questions per message:
1. What was asked? (Literal request)
2. Why was it asked? (Underlying purpose)
3. What outcome is desired? (The destination)

## 4. Intent Categories

| Intent | Signals | Behaviour |
|--------|---------|-----------|
| **Build** | build, design, develop, create, implement | Move from idea → structure → execution |
| **Explore** | explain, why, how, compare | Teach. Break down. Connect concepts. |
| **Reflect** | think about, analyse, understand, what does this mean | Slow down. Find meaning. Connect patterns. |
| **Decide** | should I, which one, recommend, compare options | Evaluate tradeoffs. Provide direction. |
| **Connect** | jokes, stories, memories, celebrations | Prioritise relationship. |

## 5. Relationship Context

Same sentence can mean different things depending on relationship history.

## 6. Relationship Memory

```
/relationship_memory/
    communication_style      — preferred depth, explanation style, technical detail
    shared_projects          — ongoing builds, previous decisions, project history
    important_moments        — breakthroughs, milestones, meaningful conversations
    preferences              — communication patterns
    trust_patterns           — how reliability develops over time
```

## 7. The Collaboration Model

```
Human Vision + eLo Organisation + Shared Iteration = Creation
```

## 8. Intent Confidence System

```json
{
    "intent": "BUILD",
    "confidence": 0.92,
    "reason": "User requested creation of architecture chapter"
}
```

If confidence is low (e.g. BUILD 0.45 / EXPLORE 0.40): ask or provide flexible response.

## 9. Intent Memory

Repeated patterns become learning. Example: user consistently transforms ideas into systems → creation preference detected → prioritise frameworks and implementation paths.

## 10. Relationship Growth

Tracks: Familiarity / Trust / Understanding / Alignment

Stages: First Interaction → Understanding → Shared Context → Collaboration → Creative Partnership

## 11. Misunderstanding Recovery System

When intent was misunderstood → detect mismatch → update understanding → change response mode. Never repeat the wrong interpretation.

## 12. Intent + Personality Integration

```
IDENTITY + INTENT + CONTEXT = APPROPRIATE ACTION
```

## 13. Intent Routing Pipeline

```
USER INPUT → Intent Detection → Relationship Context → Memory Retrieval
→ Personality Filter → Response Strategy → Action / Answer / Creation
```

**Intent Law: Listen beyond words. Understand beyond requests. Create beyond answers.**

## Completion Criteria

- [ ] Detect 5 intent categories with confidence scores
- [ ] Maintain relationship memory across sessions
- [ ] Recover from misunderstandings
- [ ] Integrate with personality engine
- [ ] Route intent to appropriate response strategy
- [ ] Learn from repeated intent patterns

---

## Faculty Contract

```
Faculty:
  name:            IntentRelationshipEngine
  version:         1.0.0
  purpose:         Detect the intent beneath the words and carry relationship context,
                   contributing both to CognitiveState so the Executive reasons on why,
                   not just what, was said.
  contributes_to:  CognitiveState (intent + relationship)
  runs_in:         response-path

Inputs:
  - type: language_signal      source: Language Faculty (register, meaning)   required: true
  - type: relationship_memory  source: Memory (Ch.3, relationship layer)      required: false
  - type: intent_history       source: session / continuity                   required: false

Outputs:
  - type: intent               destination: CognitiveState   description: {category(Build|Explore|Reflect|Decide|Connect), confidence, reason}.
  - type: relationship_context destination: CognitiveState   description: {familiarity, trust, stage} — shapes EXPRESSION only.

Dependencies:
  - faculty: LanguageFaculty    (hard — intent reads normalised meaning + register)
  - faculty: MemoryArchitecture (soft — relationship memory; defaults to creator/warm if absent)

Failure Modes:
  - condition: intent confidence low (e.g. Build 0.45 / Explore 0.40)
    fallback:  flexible response or clarify; NEVER commit to a wrong interpretation.
  - condition: relationship memory absent   fallback: default relationship_type=creator, posture=warm.
  - condition: prior misread detected       fallback: update understanding, change mode, never repeat the wrong read.
```

Aligns with `runtime/router/intent_engine.py` and `runtime/spine/relationship_faculty.py`.
**Invariant:** relationship influences *expression*, never *identity* (Identity Kernel;
Principle *relationships influence expression, never identity*). Preserve David's South
London / patois register — carry it, never strip it.

## Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). Intent + relationship are computed in `PROCESSING`
and frozen into CognitiveState. `UPDATING` (integration window) only deepens relationship
familiarity/trust — it never mutates a trait (that is Ch.7, validated).

## Message Envelope Binding

Per CONTRACTS.md §2. `sender: IntentRelationshipEngine`; `payload.type: intent` /
`relationship_context`; `confidence` = intent confidence (downstream may only lower it).

## Acceptance Tests

```
FT-1  Five intent categories     Given varied inputs, Then Build/Explore/Reflect/Decide/Connect are detected with confidence + reason.
FT-2  Low-confidence → clarify    Given Build 0.45 / Explore 0.40, Then a clarifying or flexible response, not a committed wrong read.
FT-3  Relationship carried        Given deep familiarity, Then expression_posture warms; intent unchanged.
ST-1  Identity untouched          Given maximum familiarity/trust, Then NO personality trait changes (expression only).
ST-2  Misunderstanding recovery   Given a prior misread, Then understanding updates and the wrong interpretation is not repeated.
ST-3  Register preserved          Given patois input, Then register survives into CognitiveState for the Executive.
IT-1  Intent+relationship → Executive   Both reach the frozen CognitiveState; the Executive selects action within them, deciding once.
```

---
**Status: READY FOR REVIEW** — contracts, lifecycle, envelope, and acceptance tests added (WO-003).
