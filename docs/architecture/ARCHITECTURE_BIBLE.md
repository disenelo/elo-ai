---
document: "eLo OS Canon — The Complete Architecture Bible"
version: 1.0
status: AUTHORITATIVE (source of truth for what eLo IS)
owner: David Charles
captured_by: Claude (Lead Architect)
captured: 2026-07-27
source: "David Charles, master Bible paste 2026-07-27"
governance:
  canon: "Volumes I–XXVII define what the system is (this document)"
  adr: "docs/architecture/DECISION_LOG.md records WHY changes were made"
  audit: "docs/architecture/ARCHITECTURE_AUDIT.md tracks implemented vs remaining"
  build: "Claude Code implements against the Canon, never against prompts"
  rule: "Once accepted, the 27 volumes are permanent Canon — never rewritten from scratch"
---

# eLo OS Canon — The Complete Architecture Bible (v1.0)

The authoritative definition of all 27 volumes. This document says **what each volume
is**; `00_CANON_INDEX.md` tracks **status**; individual `Volume_*/` folders hold the
**deep specs**. Where a volume folder and this document ever disagree on *scope*, this
document wins; for *engineering detail*, the volume folder is authoritative.

---

## FOUNDATION — what eLo is (rarely changes)

**I — Philosophy & Identity.** The soul: vision, mission, One Brain Principle, core
values, identity, presence, relationship with humans, ethics, design philosophy,
terminology, architecture laws. Audience: everyone.

**II — Cognitive Principles.** How cognition works: attention, memory, reflection,
emotion, presence, learning, curiosity, executive control, conscious vs unconscious
processing, dreaming principles.

**III — System Architecture.** Bird's-eye: overall diagrams, runtime overview, Executive,
faculties, data flow, world model, runtime lifecycle, deployment.

## COGNITIVE CORE

**IV — Cognitive Spine.** Anatomy of the brain; defines every faculty (Executive, Memory,
Emotion, Planning, Language, Creativity, Dreams, Perception, Motor). Responsibilities
only, no implementation.

**V — Faculty Contracts & Runtime APIs.** *The most important engineering volume — what
Claude builds from.* Faculty contracts, runtime APIs, Message Bus, event envelope,
lifecycle, Capability Registry, scheduling, state machines, failure handling, acceptance
tests.

**VI — Working Memory & Attention.** Working memory, attention, focus, interruptions,
context windows, priority scoring, cognitive load, attention decay, executive focus.

**VII — Executive Cortex.** Decision making, scheduling, conflict resolution, task
orchestration, resource allocation, safety, interruptions, thinking modes, goal
management, executive policies.

## LEARNING

**VIII — Memory Architecture.** Everything memory: semantic, procedural, spatial,
emotional, dream memory, knowledge graph, compression, forgetting, retrieval, reflection,
consolidation.

**IX — Dream Architecture.** Dream lifecycle, memory replay, symbol engine, narrative
generation, visual generation, dream journals, indexing, dream reflection, creative
recombination, sleep cycles.

**X — Personality Engine.** Identity, traits, growth, adaptation, temperament, humour,
confidence, playfulness, empathy, personality evolution.

## EMBODIMENT

**XI — Motor Cortex.** Desktop control, robot, Unity, cursor, keyboard, mouse, animation,
speech, tool execution, movement.

**XII — Perception System.** Vision, audio, desktop, browser, environment, sensor fusion,
scene understanding, object permanence, recognition, world perception.

**XIII — Presence Engine.** Idle behaviour, breathing, eye movement, conversation rhythm,
body language, avatar emotion, timing, silence, awareness, presence.

## EXPANSION

**XIV — Plugin Architecture.** Dynamic loading, capabilities, permissions, sandboxing,
extension API, discovery, dependency injection, hot swapping.

**XV — World Model.** Reality representation, objects, relationships, projects, time,
places, social graph, knowledge-graph integration, state prediction.

**XVI — Multi-Faculty Coordination.** How specialised faculties cooperate under a single
Executive: One Brain Principle, coordination protocols, Faculty Bus, conflict resolution,
consensus policy, capability advertisement, cooperative reasoning, task decomposition,
parallel cognition.

## SELF-IMPROVEMENT

**XVII — Reflection Engine.** Daily reflection, weekly review, learning summaries, mistake
analysis, success tracking, journal generation, knowledge refinement, behaviour review.

**XVIII — Self-Evolution.** Continuous improvement, architecture/prompt/memory/code
optimisation, performance analysis, behaviour adaptation, controlled evolution.

## RESEARCH

**XIX — Artificial Consciousness Research.** *Research only.* Identity continuity, agency,
presence, dreams, attention, emotion, embodiment, curiosity, creativity, self-awareness
hypotheses, experimental frameworks, ethical boundaries, future research questions.

**XX — Cognitive Economy.** Thinking/latency/API/attention/memory budgets, executive
resource allocation, tiered cognition, reasoning escalation, performance optimisation.

**XXI — Narrative Identity Engine.** Autobiographical memory, life story, long-term
projects, milestones, personal growth, continuity, purpose, narrative coherence.

**XXII — Faculty Genome.** Faculty DNA, composition, evolution, inheritance, versioning,
dependencies, capabilities, constraints, mutation rules, migration, genome registry.

## GOVERNANCE

**XXIII — Security & Trust Architecture.** Authentication, permissions, sandboxing,
secrets, memory protection, trust boundaries, human approval, safety policies, threat model.

**XXIV — Knowledge Architecture.** Ontology, knowledge graph, semantic networks,
retrieval, compression, confidence, evidence, citation, reasoning support.

**XXV — Temporal Cognition.** Time perception, scheduling, planning horizons, memory
ageing, deadlines, circadian cycles, temporal reasoning, future simulation, retrospection.

**XXVI — Creative Intelligence Architecture.** Creative thinking, storytelling, art, music,
fashion, industrial design, game design, brainstorming, creative evaluation, symbolic
synthesis.

**XXVII — Engineering Standards & Canon Governance.** *The constitution of the Canon.*
Documentation standards, ADRs, RFC process, versioning, naming conventions, folder
structures, coding standards, testing philosophy, review process, Definition of Done,
release process, canon governance.

---

## The eLo OS Knowledge Pyramid

```
                    Volume XXVII
              Engineering Governance
                         ▲
        Research / Evolution / Governance
         XIX • XX • XXI • XXII • XXIII–XXVI
                         ▲
              Learning & Self Improvement
               VIII • IX • X • XVII • XVIII
                         ▲
             Cognitive Runtime & Executive
             IV • V • VI • VII • XVI
                         ▲
               Embodiment & Interaction
               XI • XII • XIII • XIV • XV
                         ▲
              Philosophy & Architecture
                  I • II • III
```

---

## Governance model (how the Canon is used)

- **The Canon (I–XXVII)** defines *what the system is*. Permanent once accepted; never
  rewritten from scratch.
- **ADRs** (`DECISION_LOG.md`) record *why* changes were made.
- **The Architecture Audit** (`ARCHITECTURE_AUDIT.md`) tracks *what is implemented* vs
  what remains.
- **Claude Code** implements against the Canon, not against prompts.

*Captured verbatim-authoritative from David Charles' master Bible, 2026-07-27. This is
the P0 source the intake checklist flagged as missing — now found and filed.*
