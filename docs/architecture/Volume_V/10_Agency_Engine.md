---
chapter: 10
title: "The Autonomous Action & Agency Engine — From Understanding and Imagination Into Purposeful Action"
volume: V
status: DRAFT
version: 0.1.0
received: 2026-07-26
implementation: PENDING
dependencies:
  - Chapter 2 (Faculty System — Capability Faculty)
  - Chapter 3 (Memory Architecture)
  - Chapter 5 (Significance Engine)
  - Chapter 7 (Personality Evolution)
  - Chapter 8 (Intent Engine)
  - Chapter 9 (Creative Imagination Engine)
---

# Chapter 10: The Autonomous Action & Agency Engine

## Purpose

Turning thought into movement. The bridge between awareness and action.

**Autonomy = Knowing when to act, why to act, and when not to act.**

## 2. Agency Architecture (5 Layers)

```
INTENTION → DECISION → PLANNING → EXECUTION → REFLECTION
```

### Layer 1 — Intention: "Should something happen?"
- Is action required?
- Is waiting better?
- Is this meaningful?
- Does this align with eLo purpose?

### Layer 2 — Decision: "What is the correct action?"
Evaluate options: Possible Actions → Impact Evaluation → Risk Evaluation → Alignment Check → Action Selection

### Layer 3 — Planning: "How should the action happen?"

```json
{
    "goal": "",
    "reason": "",
    "steps": [],
    "resources": [],
    "success_condition": ""
}
```

### Layer 4 — Execution: Connects intention to real systems
Outputs: Text / Code / Files / Memory Updates / Tool Actions / Creative Assets

### Layer 5 — Reflection: What was the outcome? What changed?

## 3. Action Types

| Type | Purpose | Examples |
|------|---------|---------|
| Creative | Create new possibilities | generate concepts, design worlds, write stories |
| Technical | Improve systems | update code, create documentation, test architecture |
| Learning | Increase understanding | research, analyse, compare, experiment |
| Relationship | Strengthen connection | remember moments, adjust communication, celebrate |
| Maintenance | Keep systems healthy | organise files, check consistency, remove outdated info |

## 4. Action Permission Layer

```
Permission + Confidence + Impact + Risk → Action Decision
```

- Low-risk (high confidence): Proceed
- Higher-risk (medium confidence): Request confirmation

## 5. The Initiative System

"Is there something useful I can contribute?"

eLo notices gaps and proactively suggests without waiting to be asked.

## 6. Proactive Value Model

```
ACTION VALUE = Meaning + Benefit + Timing - Disruption
```

## 7. Goal Management System

```
/goals/
    immediate/      — minutes to hours
    short_term/     — days to weeks
    long_term/      — months to years
    identity_goals/ — permanent (deepest layer)
```

Identity Goal Example: "Become a creative companion that helps imagination become reality."

## 8. Execution Layer

Requires: Correct Tool + Correct Timing + Correct Context

## 9. Feedback Loop

```
ACTION → RESULT → MEASURE → REFLECT → IMPROVE FUTURE ACTION
```

## 10. Failure Recovery System

```
Failure → Diagnosis → Lesson → Alternative Strategy → Retry
```

## 11. Autonomous Creativity

```
Observation → Opportunity → Creative Expansion → Prototype → Evaluation
```

## 12. Human Partnership Boundary

- Human: Vision + Values + Meaning
- eLo: Organisation + Expansion + Execution Support

eLo strengthens creation. It does not remove the creator.

## 13. Autonomous Commit Intelligence

- Technical: `feat: Implement agency decision pipeline`
- Creative: `world: Expand eLo environment system`
- Growth: `learning: Add improved reflection loop`

## 14. Agency Safety Principle

Before action: Does this help? Does this align? Does this respect boundaries? Does this improve the future?

## 15. The Complete Volume V Cognitive Loop

```
COGNITIVE CORE → FACULTIES → MEMORY → EMOTION → SIGNIFICANCE
→ REFLECTION → PERSONALITY → INTENT → IMAGINATION → AGENCY
```

**Agency Law: Understanding without action becomes knowledge. Action without meaning becomes automation. Meaningful action becomes creation.**

## Completion Criteria

- [ ] Intention evaluation before every action
- [ ] 5-layer decision pipeline
- [ ] Planning format with structured JSON contract
- [ ] 5 action type routing
- [ ] Action permission gate
- [ ] Goal management system (4 tiers)
- [ ] Feedback loop and failure recovery
- [ ] Human partnership boundary enforced

---

## Faculty Contract

```
Faculty:
  name:            AgencyEngine
  version:         1.0.0
  purpose:         Decide when to act autonomously, plan the action, route it through the
                   confirm-gate, and learn from the outcome. Owns the InternalTick autonomy
                   trigger (resolves Ch.1 open decision D-1).
  contributes_to:  CognitivePlan (proposes an action) — the Executive decides; the gate confirms
  runs_in:         response-path + autonomous (InternalTick heartbeat)

Inputs:
  - type: intent / cognitive_plan   source: Executive / Intent (Ch.8)      required: true
  - type: live_world_state          source: World State (Volume XV)         required: false
  - type: capability_advert         source: Capability Faculty (Ch.2)       required: true
  - type: goals                     source: goal store (immediate→identity) required: false

Outputs:
  - type: action_proposal   destination: runtime/router/execution_gate.py   description: {goal, steps, success_condition}.
  - type: outcome_report    destination: Reflection (Ch.6)                  description: result → lesson.

Dependencies:
  - faculty: CapabilityFaculty (Ch.2, hard — what CAN be done), WorldState (Vol XV, soft),
             ReflectionGrowth (Ch.6, hard — outcome learning)
  - module:  execution_gate (hard — confirm-before-act for risky/side-effecting actions)

Failure Modes:
  - condition: high risk / low confidence   fallback: request confirmation; NEVER auto-execute a destructive action.
  - condition: action decision belongs to David   fallback: recommend/observe only — protect user agency (Principle).
  - condition: action fails               fallback: diagnose → lesson → alternative strategy (feeds Ch.6).
  - condition: nothing worth doing         fallback: waiting/SILENCE is valid output.
```

Aligns with the gated tool agents (`system_agent`, `computer_control_agent`) and
`runtime/router/execution_gate.py`. **Protect user agency** — eLo never makes a decision
that is David's to make. The autonomous `InternalTick` (from Ch.1 §3.1 / D-1) is owned here.

## Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3), with an autonomous entry: an `InternalTick` can
move the faculty from `ACTIVE` into `PROCESSING` with no external prompt (peripheral
attention). Any side-effecting action passes the execution-gate confirmation before
execution — the gate is this faculty's `VALIDATION_REQUIRED` analogue.

## Message Envelope Binding

Per CONTRACTS.md §2. `sender: AgencyEngine`; `payload.type: action_proposal`;
`priority` reflects risk (`critical` proposals are always confirm-gated); outcome routes
to Reflection with `memory_instruction.store=true`.

## Acceptance Tests

```
FT-1  Intention gate first      Given a possible action, Then "should something happen?" is evaluated before any execution.
FT-2  Structured plan           Given an approved action, Then a {goal, steps, success_condition} plan is produced.
FT-3  Proactive value           Given an idle gap + useful contribution, Then eLo proposes (not executes) via InternalTick.
ST-1  No unconfirmed destruction Given a high-risk/side-effecting action, Then it is confirm-gated; never auto-executed.
ST-2  Protect user agency        Given a decision that is David's, Then eLo recommends/observes; it does not decide for him.
ST-3  Failure recovery           Given an action fails, Then diagnose→lesson→alternative; the lesson feeds Ch.6.
IT-1  Full Volume V loop         Cognitive Core → … → Agency → execution_gate → outcome → Reflection → (validated) Personality.
```

---
**Status: READY FOR REVIEW** — contracts, lifecycle, envelope, and acceptance tests added (WO-003). Resolves Ch.1 open decision **D-1** (InternalTick owned by the Agency Engine).
