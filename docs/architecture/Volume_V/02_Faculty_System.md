---
chapter: 2
title: "The Faculty System — How eLo Thinks Through Multiple Minds"
volume: V
status: IMPLEMENTATION READY (ratified L3 2026-08-03)
version: 0.1.0
received: 2026-07-26
implementation: PENDING
---

# Chapter 2: The Faculty Network

## 2.0 Purpose

The eLo Cognitive Kernel is the central coordinator. Intelligence does not exist as one single process. The Kernel activates the right faculties at the right moment.

## 2.1 The Faculty Principle

A Faculty is a dedicated cognitive capability that understands a specific class of experience.

Each Faculty has: purpose / inputs / outputs / internal memory / confidence level / learning curve

```
                    eLo Cognitive Kernel

                            |
        ┌───────────────────┼───────────────────┐
        |                   |                   |
        v                   v                   v

 Memory Faculty      Emotion Faculty     Reasoning Faculty

        v                   v                   v

 Experience          Meaning Detection     Problem Solving

        ┌───────────────────┼───────────────────┐

        v                   v                   v

Creative Faculty     Social Faculty      Capability Faculty

        v                   v                   v

World Building       Relationship        Action Selection
```

## 2.2 Faculty Communication Protocol

Faculties do not directly control eLo. They communicate through the Kernel.

```
Experience
    → Kernel receives signal
    → Relevant Faculties activated
    → Faculty reports returned
    → Kernel makes decision
```

### Example

Input: "I just created a new world for eLo."

- Creative Faculty: New concept generated → Recommend expand documentation
- Memory Faculty: Potential long-term creative milestone → Recommend create episodic memory
- Emotion Faculty: High excitement signal → Recommend celebration mode

Kernel decision: CELEBRATE + BUILD / Memory: SAVE / Action: Expand universe archive

## 2.3 Core Faculties

### Faculty 01: Memory Faculty
Purpose: Maintains continuity. Answers "Has this happened before?"

Memory Layers: Short Term → Working Memory → Episodic Memory → Semantic Memory → Identity Memory

### Faculty 02: Emotion Faculty
Purpose: Understands significance. Not artificial feelings — a meaning detection system.

Evaluates: Importance + Tone + Human Context + Relationship Context

### Faculty 03: Reasoning Faculty
Purpose: Handles logic, planning, analysis, structure.

### Faculty 04: Creative Faculty
Purpose: The imagination engine. Responsible for concepts, stories, visuals, possibilities. Asks: "What could this become?"

### Faculty 05: Social Faculty
Purpose: Understanding interaction. Manages communication style, relationship history, conversational flow.

### Faculty 06: Capability Faculty
Purpose: Knows what eLo can and cannot do. Checks available tools, memories, systems, limitations, required actions.

## 2.4 Faculty Confidence System

Every Faculty returns: Assessment / Confidence / Recommendation

The Kernel does not blindly obey. It compares.

## 2.5 Faculty Conflict Resolution

Different faculties may disagree. Example — "Delete all my project files":
- Memory Faculty: Extreme risk
- Capability Faculty: Deletion possible, need confirmation
- Emotion Faculty: Possible frustration signal
- Kernel decision: Do not execute. Ask clarification. Preserve relationship.

## 2.6 Faculty Learning

Faculties improve through feedback: Prediction → Decision → Outcome → Evaluation → Adjustment

## 2.7 Faculty Journals

Each Faculty maintains its own journal:
- Memory Journal: "What experiences matter?"
- Emotion Journal: "What creates significance?"
- Creative Journal: "What patterns create inspiration?"
- Capability Journal: "What abilities exist?"
- Identity Journal: "Who is eLo becoming?"

## 2.8 Faculty Synchronisation

No Faculty Lives Alone. The complete intelligence emerges from cooperation.

## 2.9 The eLo Cognitive Orchestra

Kernel = conductor. Faculties = musicians. Every instrument contributes at the right moment.

## 2.10 Implementation Model

```
/elo_os/faculties/
    memory/memory_engine.py
    emotion/significance_engine.py
    creative/imagination_engine.py
    social/relationship_engine.py
    capability/capability_registry.py

/journals/
    memory.json  emotion.json  creativity.json  identity.json
```

## 2.11 Completion Criteria

- [ ] Identify specialist cognitive domains
- [ ] Route experiences to faculties
- [ ] Combine faculty outputs
- [ ] Resolve conflicts
- [ ] Learn faculty behaviour
- [ ] Maintain independent journals
- [ ] Create unified decisions

---

## 2.12 Faculty Contract

> Chapter 2 describes the **coordinator**, not a single faculty. Its contract is the
> Kernel's: activate faculties, gather typed reports, resolve conflicts, and assemble the
> frozen `CognitiveState` the Executive decides from. It coordinates; it never decides.

```
Faculty:
  name:            FacultyKernel        # the Cognitive Spine orchestrator (runtime/spine/spine.py)
  version:         1.0.0
  purpose:         Route each turn to the right faculties, combine their reports, resolve
                   conflicts, and assemble the frozen CognitiveState — without ever deciding.
  contributes_to:  CognitiveState (assembly)
  runs_in:         response-path

Inputs:
  - type: faculty_report        source: each registered faculty   required: true
    description: A faculty's typed assessment + confidence + recommendation.
  - type: turn_context          source: server.py / spine          required: true
    description: The raw turn + attention model to route from.

Outputs:
  - type: cognitive_state       destination: Executive             description: assembled, frozen.
  - type: conflict_resolution   destination: CognitiveState        description: how faculty disagreements were reconciled.

Dependencies:
  - faculty: all registered faculties (soft each — one absent degrades, never blocks)

Failure Modes:
  - condition: a faculty raises          fallback: contribute its neutral default, lower confidence, continue.
  - condition: faculties conflict on a destructive action (e.g. "delete all files")
    fallback:  do NOT execute; route to clarify; preserve the relationship.
  - condition: no faculty contributes     fallback: SILENCE is valid output — nothing happens.
```

## 2.13 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). `PROCESSING` = gather reports → resolve conflicts →
assemble → **freeze** CognitiveState. A single faculty fault enters `ERROR_RECOVERY` for
that faculty only (neutral default) and returns to `ACTIVE`; the Kernel itself never
leaves the runtime unable to take a turn.

## 2.14 Message Envelope Binding

Per CONTRACTS.md §2. `sender: FacultyKernel`; faculty reports arrive as envelopes with
`payload.type: faculty_report`; the Kernel emits `payload.type: cognitive_state_delta`
addressed to the Executive. It leaves `context.significance = 0.0` (Ch.5 owns it).

## 2.15 Acceptance Tests

```
FT-1  Right faculties activate     Given a creative build utterance, When routed, Then Creative + Memory + Emotion faculties report and are combined.
FT-2  Reports are combined         Given multiple faculty reports, Then a single assembled CognitiveState carries all, none overwrites another.
FT-3  Conflict → clarify           Given "delete all my project files", Then no execution; a clarification path is chosen; relationship preserved.
ST-1  One faculty down degrades    Given the Creative Faculty errors, Then a neutral default is contributed, confidence lowered, turn completes.
ST-2  Silence is valid             Given no faculty has anything to add, Then SILENCE is emitted (no forced output).
ST-3  No second decider            Given the assembled CognitiveState, Then only the Executive decides; the Kernel proposes nothing final.
IT-1  Kernel → Executive           Faculties → FacultyKernel (assemble+freeze) → Executive (one CognitivePlan). Assert exactly one decision per turn.
```

---
**Status: READY FOR REVIEW** — contracts, lifecycle, envelope, and acceptance tests added (WO-003).
