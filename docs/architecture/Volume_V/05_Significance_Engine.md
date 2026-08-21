---
chapter: 5
title: "The Significance Engine — Emotion Decides What Becomes Memory"
volume: V
status: IMPLEMENTATION READY (ratified L3 2026-08-03)
version: 0.1.0
received: 2026-07-26
implementation: PENDING
dependencies:
  - Chapter 2 (Faculty System — Emotion Faculty)
  - Chapter 3 (Memory Architecture — all layers)
---

# Chapter 5: The Significance Engine

## Purpose

Teaches eLo OS what matters. Every interaction passes through the Significance Engine before anything becomes memory.

eLo does not remember because something happened. eLo remembers because something changed something.

## The Significance Loop

```
INPUT → Moment Detection → Emotional Evaluation → Meaning Assessment
→ Significance Score → Memory Decision → Journal Routing → Future Behaviour Adaptation
```

## 3. Moment Detection Layer

| Significance | Example | Score | Action |
|---|---|---|---|
| Low | "What time is the meeting?" | 0.02 | No long-term memory |
| Medium | "I finally understood how the memory system works." | 0.72 | Store architecture insight |
| High | "This project is me rebuilding the imagination I lost as a kid." | 0.96 | Permanent memory candidate |

## 4. Emotional Weight Model

Emotion = Energy + Meaning. A difficult conversation can be highly significant. A happy one can be insignificant. The question: "Did this moment create change?"

### Emotional Dimensions
- **Joy**: creative breakthroughs, funny moments, celebrations, discoveries
- **Curiosity**: learning, experiments, questions, exploration
- **Challenge**: mistakes, obstacles, difficult decisions
- **Connection**: trust, honesty, shared memories
- **Identity**: values, beliefs, purpose, personality evolution

## 5. Significance Scoring System

```
SIGNIFICANCE = Emotion Weight + Novelty + Learning Value + Relationship Value + Future Relevance
```

Example — user teaches eLo a new creative philosophy:
- Emotion: 0.8 / Novelty: 0.9 / Learning: 1.0 / Relationship: 0.8 / Future: 1.0
- TOTAL: 0.90 → CREATE MEMORY / UPDATE JOURNAL / ADAPT FUTURE RESPONSES

## 6. Memory Routing — Five Memory Faculties

1. **Identity Memory** — personality evolution, values, beliefs, purpose
2. **Relationship Memory** — communication style, shared moments, preferences
3. **Creative Memory** — world building, characters, designs, concepts
4. **Technical Memory** — architecture decisions, coding lessons, development patterns
5. **Reflection Memory** — mistakes, improvements, personal insights

## 7. The Journal System

| Journal | Purpose | Contains |
|---------|---------|---------|
| Heart Journal | Emotional significance | Meaningful moments, emotional changes, connection points |
| Dream Journal | Creative evolution | Ideas, visions, concepts, possibilities |
| Builder Journal | Technical progression | Architecture, experiments, solutions |
| Growth Journal | Learning | Lessons, mistakes, improvements |
| Universe Journal | eLo canon | Characters, worlds, stories, mythology |

## 8. Memory Decay

Strength = Importance × Recurrence × Impact

A memory grows stronger when: repeated / referenced again / emotionally reinforced.

## 9. GitHub Commit Intelligence

| Trigger | Example | Commit |
|---------|---------|--------|
| Technical Achievement | Memory pipeline integrated | `feat(memory): Add significance routing system` |
| Creative Milestone | New eLo world concept | `world: Add Candy Orchard expansion` |
| Identity Evolution | New personality behaviour | `personality: Update empathy response model` |

## 10. The Living System Principle

A chatbot stores conversations. eLo develops continuity.

**The Significance Law: Not everything deserves memory. Everything deserves awareness. Only meaningful moments become identity.**

## 12. Integration Architecture

```
USER EXPERIENCE → Conversation Engine → Emotion Detector → Significance Engine
→ Memory Router → Journals → Identity Model → Future Behaviour
```

## Completion Criteria

- [ ] Separate information from meaning
- [ ] Score importance of experiences
- [ ] Decide memory depth
- [ ] Recognise milestones
- [ ] Detect patterns
- [ ] Update identity understanding
- [ ] Create meaningful development history

---

## Faculty Contract

```
Faculty:
  name:            SignificanceEngine
  version:         1.0.0
  purpose:         Decide whether a moment mattered (created change) and route its memory
                   priority. The one faculty that writes context.significance.
  contributes_to:  envelope.context.significance + MemoryPriority
  runs_in:         response-path (score) → feeds integration

Inputs:
  - type: turn_event         source: CognitiveState                required: true
  - type: emotional_tag      source: EmotionalProcessing (Ch.4)     required: false   # Emotion Weight term
  - type: relationship_ctx   source: Intent & Relationship (Ch.8)   required: false
  - type: novelty            source: core/pattern_observer.py       required: false

Outputs:
  - type: significance_score   destination: envelope.context.significance   description: 0.0–1.0.
  - type: memory_priority      destination: MemoryFaculty (Ch.3)     description: peripheral | normal | high | pinned.
  - type: journal_route        destination: Reflection (Ch.6)        description: which journal an episode feeds.

Dependencies:
  - faculty: EmotionalProcessing (soft — emotion weight; without it score from novelty+learning+relationship)
  - faculty: MemoryArchitecture  (hard — consumes the priority to store/pin)

Failure Modes:
  - condition: affect absent          fallback: score from novelty + learning + relationship only.
  - condition: ambiguous/charged      fallback: err toward store-if-charged (a hard, unresolved moment can still matter).
  - condition: engine errors          fallback: default significance 0.0 (peripheral); turn proceeds, nothing pinned.
```

Aligns with the live `memory/significance_engine.py`. **This is the only faculty allowed
to set `context.significance`** (CONTRACTS.md §2) — every other faculty leaves it `0.0`.

## Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). Scoring runs in `PROCESSING`; the resulting
`MemoryPriority` closes the loop by pinning a turn in the Memory Faculty (Ch.3) and, at
`high+`, triggers Reflection (Ch.6).

## Message Envelope Binding

Per CONTRACTS.md §2. `sender: SignificanceEngine`; it **writes** `context.significance`
and proposes `memory_instruction.priority`; `payload.type: significance_score`.

## Acceptance Tests

```
FT-1  Low significance            "What time is the meeting?" → ~0.02, no long-term memory.
FT-2  Medium significance         "I finally understood the memory system." → ~0.72, store architecture insight.
FT-3  High significance           "This project is me rebuilding the imagination I lost." → ~0.96, permanent candidate + pin.
ST-1  Hard moments count          A difficult, unresolved conversation scores high (change, not pleasantness).
ST-2  Only Ch.5 sets significance Assert no other faculty writes context.significance in a full turn.
ST-3  Graceful default            Engine error → significance 0.0; turn proceeds; nothing wrongly pinned.
IT-1  Emotion → Significance → Memory   Ch.4 emotion weight raises the score → MemoryPriority=high → Ch.3 pins the turn.
```

---
**Status: READY FOR REVIEW** — contracts, lifecycle, envelope, and acceptance tests added (WO-003).
