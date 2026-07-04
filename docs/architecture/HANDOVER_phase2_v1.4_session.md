# eLo OS Architecture Phase 2
# Session Handover — Start here for v1.4 Relationship Faculty

────────────────────────────────────────────
CONTEXT
────────────────────────────────────────────

We are continuing the architectural development of eLo OS, a unified
cognitive runtime built on the One Brain Principle.

The canonical architecture reference lives at:
    ~/elo-ai/docs/architecture/

Read 00_philosophy.md first. It contains the full pipeline and all rules.

────────────────────────────────────────────
WHAT IS ALREADY COMPLETE
────────────────────────────────────────────

✓ One Brain Principle — established and enforced
✓ Language Faculty — implemented in runtime/router/meaning_engine.py
✓ CCM v1.2 — full spec at docs/architecture/06_conversation_context_matrix.md
✓ HIM v1.3 — full spec at docs/architecture/07_human_interaction_matrix.md
✓ Emotional Light Engine v1.8 — full spec at docs/architecture/11_emotional_light_engine.md
✓ CognitivePlan object — partial, at runtime/spine/plan.py
✓ spine.py — partial alignment, at runtime/spine/spine.py
✓ Existing faculties in spine: Language, Capability, System, Executive, Conversation

────────────────────────────────────────────
WHAT DOES NOT EXIST YET (IN ARCHITECTURE FORM)
────────────────────────────────────────────

⚠ Memory Faculty — memory_engine.py exists but not a formal spine faculty
⚠ Attention Faculty — computed in server.py, passed as dict, not a faculty
⚠ Relationship Faculty — DOES NOT EXIST (see below)
⚠ Executive Faculty — partial (executive.py + spine.py fragment, no full spec)
⚠ Cognitive Plan — incomplete (plan.py exists but missing Emotional Vector)
⚠ Presence Plan — does not exist (output of Emotional Light Engine)
⚠ Emotional Light Engine — spec exists, implementation does not

IMPORTANT — the existing relationships/relationship_engine.py is a CONCEPT
GRAPH for eLo's world (book/game/OS/robot relationships). It is NOT the
Relationship Faculty. Do not confuse these. Do not touch relationship_engine.py.

────────────────────────────────────────────
THE PIPELINE (current vs target)
────────────────────────────────────────────

CURRENT spine.py run() order:
    Language → Capability → System → Executive → Conversation

TARGET order (after all Phase 2 docs are complete):
    Language → CCM → HIM → Memory → Attention → Relationship →
    Desktop → Capability → Executive →
    [COGNITIVE PLAN] →
    Emotional Light Engine →
    [PRESENCE PLAN] →
    Conversation / Voice / Avatar / Robot

────────────────────────────────────────────
THE TASK FOR THIS SESSION
────────────────────────────────────────────

Write eLo OS v1.4 — Relationship Faculty.

Complete Architecture Specification.

This document belongs at:
    docs/architecture/05_relationship_faculty.md

It should be written to the same quality and depth as CCM v1.2 and HIM v1.3.
Expect 4,000–6,000 words. Do not compress it.

────────────────────────────────────────────
WHAT THE RELATIONSHIP FACULTY MUST COVER
────────────────────────────────────────────

Purpose
Core principles
Responsibilities
Position in the pipeline (after Attention, before Desktop Context)

Relationship model:
    Who is communicating?
    Creator / friend / collaborator / mentor / community member / stranger
    Relationship affects expression warmth — never reasoning

Trust evolution:
    How trust builds across sessions
    What signals indicate trust increase or decrease
    Trust does not change the Executive's reasoning — only expression posture

Creative partnership:
    David is eLo's creator — this is the primary and founding relationship
    How a creative partnership differs from a user-assistant relationship
    Shared project evolution (eLo OS, game, book, robot, vinyl, etc.)

Session continuity:
    What persists between sessions
    How relationship context is retrieved from memory
    How it is passed to the Executive

Long-term memory interaction:
    How the Relationship Faculty reads from Memory Faculty
    What it adds to the cognitive context
    What it does not change

Familiarity scoring:
    0.0 = stranger, 1.0 = deeply established creative partner
    How scoring evolves
    How it influences expression, not reasoning

Boundary recognition:
    When the relationship faculty detects the person needs space
    When it detects over-reliance
    Neither triggers reasoning changes — only posture changes

Preferred communication:
    South London register, patois, hybrid — tracked by Relationship Faculty
    Language preferences persist as relationship context

Shared language growth:
    Vocabulary, phrases, and cultural expressions that belong to this relationship
    Stored as relationship context, not raw memory

Collaborative history:
    Projects worked on together
    Moments of creative breakthrough
    Obstacles overcome

Relationship confidence:
    How certain the engine is about its relationship model (0.0–1.0)
    Falls back gracefully when uncertain

Relationship graph:
    If other people ever interact with eLo, how relationships are tracked
    Primary relationship (David/creator) always has highest weight

Update rules:
    When and how relationship context is updated
    Never overwrites — always evolves

Retrieval rules:
    How relationship context is retrieved at start of each turn

Executive interface:
    What the Relationship Faculty hands to the Executive
    Exactly which fields the Executive receives
    What the Executive does with them (expression posture only)

Data structures:
    RelationshipContext object — define it
    RelationshipProfile — per-person model
    FamiliarityScore — continuous 0.0–1.0

────────────────────────────────────────────
RULES FOR THIS DOCUMENT
────────────────────────────────────────────

1. The Relationship Faculty never decides anything.
   It contributes relationship context. The Executive decides.

2. Relationship affects expression posture only.
   Never reasoning, never memory retrieval rules, never capability selection.

3. David is the creator relationship. This is the primary relationship.
   All other relationships are secondary. The system was built for this one.

4. Do not touch relationships/relationship_engine.py.
   That is a CONCEPT GRAPH for worldbuilding. This faculty is separate.

5. Write to the same quality as CCM v1.2 and HIM v1.3.
   Sections, rules, data structures, success criteria, future extensibility.

6. Use the architecture header style:
   # eLo OS v1.4
   # Relationship Faculty
   # Complete Architecture Specification

────────────────────────────────────────────
AFTER THIS DOCUMENT
────────────────────────────────────────────

v1.5 — Executive Faculty (full spec)
v1.6 — Cognitive Plan Object (add Emotional Vector + PresencePlan output)
v1.7 — spine.py Runtime Alignment (clean execution path for all faculties)
v1.8 — Emotional Light Engine (spec complete, implementation next)

Each of these is a separate session. Do not begin v1.5 in this session.

────────────────────────────────────────────
FILES TO READ BEFORE STARTING
────────────────────────────────────────────

    ~/elo-ai/docs/architecture/00_philosophy.md          ← full pipeline
    ~/elo-ai/docs/architecture/06_conversation_context_matrix.md  ← quality reference
    ~/elo-ai/docs/architecture/07_human_interaction_matrix.md     ← quality reference
    ~/elo-ai/runtime/spine/spine.py                      ← current implementation
    ~/elo-ai/runtime/spine/plan.py                       ← current CognitivePlan
    ~/elo-ai/runtime/executive.py                        ← current executive logic
    ~/elo-ai/relationships/relationship_engine.py        ← concept graph (DO NOT CHANGE)
    ~/elo-ai/memory/                                     ← memory system
