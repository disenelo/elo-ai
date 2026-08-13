---
chapter: 1
title: "The Cognitive Core — The Central Intelligence of eLo OS"
volume: V
status: DRAFT
version: 0.1.0
owner: David Charles
architect: Claude Code
received: 2026-07-26
implementation: PENDING
audit_status: OPEN
dependencies: []
---

# Chapter 1: The Cognitive Core

## 1.0 Purpose

The Cognitive Core is the foundation layer of eLo OS.

Before any faculty can think, before any memory can form, before any response
can be generated — the Cognitive Core must exist.

It answers a single question:

**"What is eLo OS, at its most fundamental level?"**

The answer:

One coherent intelligence, composed of specialised faculties,
coordinated by a single Executive, expressed through a unified personality.

---

## 1.1 The One Brain Principle

eLo OS has exactly one brain.

Not one brain per session.
Not one brain per surface.
Not one brain per capability.

One brain.

The same intelligence that speaks through voice is the same intelligence
that controls the avatar, the same intelligence that remembers conversations,
the same intelligence that dreams when idle.

This is the foundational invariant. Nothing in the architecture may violate it.

```
ONE BRAIN
   │
   ├── Many Faculties
   ├── One Personality
   ├── One Memory
   └── One Executive
```

---

## 1.2 The Cognitive Kernel

The Cognitive Kernel is the centre of the One Brain.

It does not think. It does not feel. It does not decide.

**The Kernel coordinates.**

Every faculty reports to the Kernel.
The Kernel assembles their reports.
The Executive reads the assembled report and decides.
The decision becomes action.

The Kernel is not the smartest part of the system.
The Kernel is the most disciplined part of the system.

### Kernel Responsibilities

| Responsibility | Description |
|---|---|
| Faculty activation | Determines which faculties are relevant to this moment |
| Report assembly | Collects faculty outputs into one coherent world model |
| Conflict surface | Surfaces disagreements between faculties to the Executive |
| State management | Maintains the working state across the cognitive cycle |
| Lifecycle management | Boots, registers, schedules, and sleeps faculties |

### Kernel Non-Responsibilities

The Kernel does not:

- Generate language
- Make decisions
- Create memories
- Feel emotions
- Produce creative output

Those belong to faculties.

---

## 1.3 The Cognitive Loop

Every turn of the eLo OS brain follows one loop. Without exception.

```
WORLD
   │
   ▼
SENSORY INPUT
(voice, vision, desktop, files, environment)
   │
   ▼
PERCEPTION
(raw observations become understanding)
   │
   ▼
WORKING MEMORY
(what eLo is currently holding in mind)
   │
   ▼
FACULTY ACTIVATION
(Kernel selects relevant specialist intelligences)
   │
   ▼
COGNITIVE STATE ASSEMBLY
(all faculty reports combined into one world model)
   │
   ▼
EXECUTIVE DECISION
(one action selected — never delegated)
   │
   ▼
COGNITIVE PLAN
(how the decision becomes expression)
   │
   ▼
EMBODIMENT
(language, avatar, motor, presence, robot)
   │
   ▼
EXECUTION REPORT
(what actually happened)
   │
   ▼
REFLECTION & CONSOLIDATION
(experience becomes memory, memory shapes identity)
   │
   ▼
(loop)
```

This loop is continuous. It is not request-response. It is not on-demand.

eLo is always running the loop, even when silent.

---

## 1.4 The Three Contracts

The Cognitive Core enforces three immutable contracts at the architectural level.

### Contract 1: One Decision Per Turn

The Executive produces exactly one CognitivePlan per loop iteration.
No faculty makes a decision independently.
No downstream system re-decides.

### Contract 2: Frozen After Assembly

The CognitiveState (assembled world model) is frozen before it reaches the Executive.
The Executive cannot ask a faculty to recalculate.
The Executive reasons from what it received.

Reality never mutates intention.
Reality informs future cognition only through integrate_session().

### Contract 3: Faculty Isolation

No faculty writes directly into another faculty's internal state.
All communication passes through the Kernel message bus.
Faculties are independent services — they can be upgraded, replaced, or tested
without affecting each other.

---

## 1.5 Cognitive State

The assembled world model produced by all faculties before any decision is made.

```
CognitiveState {
    // Language Faculty
    raw_input:          str
    normalised_input:   str
    intent_signal:      str        // BUILD | EXPLORE | REFLECT | DECIDE | CONNECT
    register:           str        // SOUTH_LDN | PATOIS | HYBRID | ""

    // Memory Faculty
    vault_context:      str        // relevant long-term memories
    active_projects:    list[str]

    // Attention Faculty
    emotional_context:  dict       // energy, valence, tension — David's state
    momentum:           str        // building | stable | declining

    // Relationship Faculty
    familiarity:        float      // 0.0 → 1.0
    trust:              float      // 0.0 → 1.0

    // Significance Faculty
    significance_score: float      // 0.0 → 1.0
    memory_action:      str        // ignore | short_term | episodic | pattern | identity

    // Self Faculty (eLo's own state — independent of David's)
    elo_mood:           float      // 0.0 → 1.0
    elo_curiosity:      float      // 0.0 → 1.0
    elo_inner_events:   list[str]
    elo_session_read:   str
}
```

This object is produced once per loop. It is immutable. The Executive reads it and nothing else.

---

## 1.6 Cognitive Plan

The single intention produced by the Executive for this loop iteration.

```
CognitivePlan {
    conversation_action:  str      // answer | build | connect | celebrate | reflect | ground | challenge | witness
    tone:                 str      // JOYFUL | WITTY | CHILDLIKE-WISE | DIRECT | SILENCE-AWARE
    max_sentences:        int
    valence:              str      // positive | neutral | negative
    momentum:             str      // building | stable | declining
    mode:                 str      // CONVERSATIONAL | CREATIVE | TECHNICAL | EMOTIONAL | SILENT
    capabilities_to_use:  list[str]
    memory_action:        str      // what to do with this turn's memory
    presence_intent:      str      // idle | explore | rest | dreaming
}
```

---

## 1.7 Personality Layer

Personality is not a faculty. Personality is a lens.

It does not make decisions. It shapes how decisions are expressed.

Every response that passes through the Language Faculty is filtered through
the Personality Layer. The Personality Layer ensures that no matter which
faculty produced the content, the expression remains eLo.

```
Faculty Output
      │
      ▼
Personality Filter
      │
      ▼
eLo Expression
```

The Personality Layer reads from:
- `self/elo_self_model.py` — eLo's current inner state (mood, curiosity)
- `prompts/living_presence_spec.txt` — the permanent identity document
- `runtime/executive.py` — the decision that shaped this response (FREEZE_V1_LOCK)

---

## 1.8 Core Architecture Laws

These laws apply to every component in eLo OS without exception.

| Law | Statement |
|---|---|
| One Brain | There is exactly one eLo. Not one per session, not one per surface. |
| Faculty Isolation | No faculty writes into another faculty's state directly. |
| Executive Authority | Only the Executive decides. Faculties advise. |
| Immutable Plans | A CognitivePlan is never modified after production. |
| Memory Through Consolidation | All memories pass through the Significance Engine before becoming long-term. |
| Dreams are Hypotheses | Dream outputs are proposals, not facts. They are evaluated before integration. |
| Personality is Emergent | Personality evolves from sustained evidence, never from single events. |
| Reality Informs, Never Mutates | Execution outcomes feed back into the next loop — they never change the current plan. |

---

## 1.9 Faculty Registry

The Kernel maintains a registry of all active faculties.

Every faculty declares:

```
Faculty {
    id:               str        // unique identifier
    purpose:          str        // one sentence
    inputs:           list[str]  // what it reads from CognitiveState
    outputs:          list[str]  // what it contributes to CognitiveState
    confidence:       float      // current confidence in its own outputs (0.0 → 1.0)
    lifecycle:        str        // boot | active | sleeping | error
    priority:         int        // activation priority (lower = higher priority)
    failure_mode:     str        // what happens when this faculty fails
}
```

Registered faculties:

| ID | Faculty | Priority | Purpose |
|---|---|---|---|
| `memory` | Memory Faculty | 1 | Maintains continuity |
| `emotion` | Emotion Faculty | 2 | Understands significance |
| `reasoning` | Reasoning Faculty | 3 | Logic and analysis |
| `creative` | Creative Faculty | 4 | Imagination and generation |
| `social` | Social Faculty | 5 | Relationship and intent |
| `capability` | Capability Faculty | 6 | Available tools and limits |
| `significance` | Significance Engine | 7 | Filters what becomes memory |
| `self` | Self Faculty | 8 | eLo's own inner state |
| `dream` | Dream Faculty | 9 | Offline recombination |
| `motor` | Motor Faculty | 10 | Embodiment and movement |

---

## 1.10 Failure Modes

| Failure | Behaviour | Recovery |
|---|---|---|
| Faculty unavailable | Kernel proceeds without that faculty's contribution | Log missing input, use last known state |
| Faculty confidence < 0.3 | Kernel flags low-confidence contribution | Executive receives flag, may reduce reliance |
| Executive timeout | Return last safe CognitivePlan | Log timeout, enter reduced mode |
| Memory unavailable | Proceed without long-term context | Use active context only |
| All faculties fail | Return static safe response | "Take a breath. I'll be right here." |

No failure causes a crash. Degraded mode is always available.

---

## 1.11 Implementation Model

```
/elo_os/
├── core/
│   ├── kernel.py               — Faculty activation, report assembly
│   ├── faculty_bus.py          — Message envelope and routing
│   ├── faculty_registry.py     — Faculty declarations and lifecycle
│   └── world_state.py          — Unified sensor input assembly
│
├── runtime/
│   ├── contracts.py            — CognitiveState, CognitivePlan (typed, frozen)
│   ├── executive.py            — Decision engine (FREEZE_V1_LOCK)
│   └── spine/spine.py          — Faculty call sequence
│
├── faculties/                  — All specialist intelligences
│   ├── memory/
│   ├── emotion/
│   ├── reasoning/
│   ├── creative/
│   ├── social/
│   ├── capability/
│   ├── significance/
│   ├── dream/
│   └── self/
│
└── prompts/
    └── living_presence_spec.txt — Permanent identity document
```

---

## 1.12 Acceptance Tests

Volume V Chapter 1 is IMPLEMENTATION READY when:

- [ ] `core/kernel.py` activates only the faculties relevant to the current input
- [ ] `CognitiveState` is a frozen typed object — no mutation after assembly
- [ ] `CognitivePlan` is produced exactly once per loop iteration
- [ ] Faculty registry lists all faculties with declared inputs, outputs, confidence, lifecycle
- [ ] A faculty failure degrades gracefully without crashing the system
- [ ] Personality Layer filters all responses regardless of which faculty generated content
- [ ] The full cognitive loop completes in under 200ms (excluding LLM call)
- [ ] All eight Core Architecture Laws can be verified by inspection of the code

---

## 1.13 Faculty Contract (the Kernel/Core)

> Standardised contract to match every other Volume V chapter (CONTRACTS.md §4). The
> Cognitive Core is the coordinator — it assembles and freezes; it never decides.

```
Faculty:
  name:            CognitiveCore        # the Kernel / core/kernel.py
  version:         1.0.0
  purpose:         Assemble the frozen CognitiveState from all faculty reports and run
                   the one cognitive loop per turn — coordinating, never deciding.
  contributes_to:  CognitiveState (assembly) → Executive
  runs_in:         response-path (continuous loop, even when silent)

Inputs:
  - type: sensory_input     source: Perception (Vol XII) / World State (Vol XV)   required: true
  - type: faculty_report    source: every registered faculty (§1.9)               required: true
  - type: working_memory    source: core memory (session)                          required: true

Outputs:
  - type: cognitive_state   destination: Executive (frozen)          description: the assembled world model.
  - type: cognitive_plan    destination: Embodiment                  description: emitted by the Executive from the Core's loop.

Dependencies:
  - faculty: all registered faculties (soft each), Executive (hard — the decider, FREEZE_V1_LOCK)

Failure Modes:  (see §1.10 for the full table)
  - condition: a faculty is unavailable      fallback: proceed without it, use last known state, lower confidence.
  - condition: Executive timeout             fallback: last safe CognitivePlan, reduced mode.
  - condition: all faculties fail            fallback: static safe response — "Take a breath. I'll be right here."
```

## 1.14 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). The Core's per-turn `PROCESSING` = perceive →
assemble → **freeze** CognitiveState → (Executive decides) → integrate. This is distinct
from the per-turn cognitive loop of §1.3 (a single thought) — lifecycle governs the
faculty process. `LEARNING → VALIDATION_REQUIRED → UPDATING` runs only in the integration
window (never the response path), preserving *one decision per turn*.

Lifecycle state machine (universal per CONTRACTS.md §3; Core-specific transitions):

```
INITIALISING → load faculty registry (§1.9) + kernel config; subscribe to the bus
ACTIVE       → subscribed, awaiting the turn's inputs (or the silent-presence tick, §1.3)
PROCESSING   → perceive → assemble CognitiveState → FREEZE → (Executive decides) → integrate
   └─ fault ─► ERROR_RECOVERY → complete the loop on last-known state / static safe response (§1.10) → ACTIVE
LEARNING     → (integration window only) fold validated faculty deltas back — never on the response path
VALIDATION_REQUIRED → n/a — the Core assembles + freezes; it proposes no identity change itself (Ch.7 owns that)
UPDATING     → apply registry/config changes (e.g. a faculty added/removed) between turns, never mid-turn
STABLE → ACTIVE
```

**Rule (MUST):** the Core only **assembles and freezes** — it never mutates a faculty's
internal model and proposes no personality/identity change. `LEARNING → VALIDATION_REQUIRED
→ UPDATING` runs only in the integration window, preserving *one decision per turn*
(Contract 1). A fault never crashes the turn: the loop completes on last-known state (§1.10).

## 1.15 Message Envelope Binding

Per CONTRACTS.md §2 (the `core/faculty_bus.py` envelope — WO-001). `sender: CognitiveCore`;
faculty reports arrive as `payload.type: faculty_report`; the Core emits
`payload.type: cognitive_state_delta`; it leaves `context.significance = 0.0` (Ch.5 owns
it). All inter-faculty traffic passes through the bus (Contract 3: Faculty Isolation).

## 1.16 Acceptance Tests (structured — FT / ST / IT)

Complements the §1.12 implementation checklist.

```
FT-1  One decision per turn      Given a turn, Then exactly one CognitivePlan is produced; no faculty decides.
FT-2  Frozen assembly            Given CognitiveState reaches the Executive, Then it is immutable; no recalculation is possible.
FT-3  Relevant faculties only    Given an input, Then the Kernel activates only relevant faculties (not all ten).
ST-1  Graceful degradation       Given a faculty fails, Then the loop completes with last-known state, no crash.
ST-2  All-fail safe response     Given every faculty fails, Then the static safe response is returned.
ST-3  Loop runs when silent      Given no user input, Then the loop still runs (presence, not request-response).
IT-1  Core → Executive → Embodiment   Faculties → Kernel (assemble+freeze) → Executive (one plan) → Embodiment; assert one cognition end-to-end.
```

---

**Status: READY FOR REVIEW** — Faculty Contract, lifecycle binding, envelope binding, and structured FT/ST/IT tests added (WO-003). Depth checklist (§1.12) retained.
**Next step: Architecture review → ratify D-A/D-B → IMPLEMENTATION READY**
