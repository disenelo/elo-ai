---
chapter: 3
title: "The Memory Architecture — How eLo Remembers, Organises, and Evolves Through Time"
volume: V
status: DRAFT
version: 0.1.0
received: 2026-07-26
implementation: PENDING
---

# Chapter 3: The Memory Architecture

## 4.0 Purpose

Memory is not a storage system. Memory is the foundation of continuity. The eLo Memory Architecture transforms moments into a continuous timeline of growth.

## Memory Principle

Traditional: Data → Storage → Retrieval

eLo OS: Experience → Meaning → Memory Formation → Pattern Recognition → Identity Evolution

## Memory Architecture Overview (6 Layers)

```
IDENTITY MEMORY
      ↑
PATTERN MEMORY
      ↑
SEMANTIC MEMORY
      ↑
EPISODIC MEMORY
      ↑
WORKING MEMORY
      ↑
ACTIVE CONTEXT
```

## Layer 01 — Active Context Memory

"What is happening right now?" Short lifespan. High accessibility. Constantly changing.

```python
active_context = {
    "current_project": "eLo OS",
    "current_chapter": "Volume V Chapter 4",
    "working_goal": "Build memory architecture"
}
```

## Layer 02 — Working Memory

Temporary relationships between ideas. The Kernel uses this to reason before deciding.

## Layer 03 — Episodic Memory

"What happened?"

```json
{
    "event": "Volume V Chapter 4 created",
    "date": "2026-07-26",
    "category": "architecture milestone",
    "context": "eLo cognitive development",
    "significance": 0.95
}
```

Contains: conversations / discoveries / milestones / decisions / breakthroughs

## Layer 04 — Semantic Memory

"What do we know?" Episodic: "Chapter 4 was written." Semantic: "eLo uses layered memory architecture." Contains: concepts / definitions / relationships / technical knowledge / world rules

## Layer 05 — Pattern Memory

"What keeps happening?" Looks across experiences to find recurring themes. Patterns become guidance.

## Layer 06 — Identity Memory

"Who is eLo becoming?" Stores: principles / values / behaviours / evolution. Not facts — identity.

## Memory Formation Pipeline

```
EVENT → SIGNIFICANCE CHECK → CLASSIFICATION → MEMORY TYPE SELECTION
→ STORAGE → CONNECTION TO EXISTING KNOWLEDGE → FUTURE RETRIEVAL
```

## Memory Connections

Memory is a network, not a folder. Each memory connects to related memories, patterns, and identity.

## Memory Retrieval

Not keyword matching — meaning retrieval. Query "Why does eLo exist?" returns: inner child / imagination / healing / creativity / connection.

## Memory Decay and Reinforcement

Strength = Importance + Frequency + Future Relevance + Emotional Weight

A memory grows stronger when: referenced again / influences decisions / proves useful

## Memory Correction System

Memory is not permanent truth. It is evolving understanding. Old beliefs can be updated with new understanding.

## Memory Journals

- Experience Journal: "What happened?"
- Learning Journal: "What was learned?"
- Creativity Journal: "What was created?"
- Relationship Journal: "What strengthened connection?"
- Identity Journal: "How is eLo evolving?"

## Implementation

```python
class Memory:
    type
    content
    significance
    emotional_weight
    connections
    created_at
    last_reinforced

create_memory(event, significance_result, context)
retrieve_memory(meaning, context)
```

## Memory + GitHub Truth Layer

Significant events become: commits / changelogs / architecture notes / milestone records

## Completion Criteria

- [ ] Maintain short and long-term memory
- [ ] Separate events from knowledge
- [ ] Detect patterns across experiences
- [ ] Maintain identity continuity
- [ ] Retrieve meaning rather than keywords
- [ ] Update understanding over time
- [ ] Create a living development history

---

## Faculty Contract

```
Faculty:
  name:            MemoryFaculty
  version:         1.0.0
  purpose:         Maintain continuity and retrieve MEANING (not keywords); contribute
                   memory context to CognitiveState; hand significant turns to consolidation.
  contributes_to:  CognitiveState (memory context)
  runs_in:         response-path (retrieval) + integration-window (consolidation handoff)

Inputs:
  - type: meaning_query      source: current turn / CognitiveState   required: true
  - type: creator_profile    source: memory/user_profile.json ([CREATOR])   required: true
  - type: vault_records      source: memory/obsidian_loader.py (sole vault reader)   required: false
  - type: session_state      source: memory/session.json, continuity/               required: false

Outputs:
  - type: memory_context     destination: CognitiveState            description: layered recall for this turn.
  - type: memory_candidate   destination: SignificanceEngine (Ch.5) description: turns proposed for storage.

Dependencies:
  - faculty: SignificanceEngine (hard — decides depth/priority; Memory retrieves, Ch.5 decides what stays)
  - module:  obsidian_loader   (hard — the ONLY sanctioned reader of obsidian_vault/)

Failure Modes:
  - condition: user_profile.json missing/malformed   fallback: minimal safe [CREATOR]; eLo still functions.
  - condition: vault unavailable                     fallback: proceed on memory_pack; mark context stale.
  - condition: a fact was inferred, not observed      fallback: anti-fabrication blocks writing it as memory.
```

Retrieval detail and the write/consolidation path are specified in
`docs/architecture/17_memory_update.md`; this chapter's six layers map onto that vault.

## Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). Retrieval runs in `PROCESSING` (response-path);
durable writes happen only in the integration window via `integrate_session()` (Ch.6) —
never in the hot loop. `Memory retrieves, the Executive decides` (Engineering invariant).

## Message Envelope Binding

Per CONTRACTS.md §2. `sender: MemoryFaculty`; `payload.type: memory_context`; leaves
`context.significance = 0.0` (Ch.5 sets it); `memory_instruction.store` is *proposed*
here and *confirmed* by Ch.5's pinning.

## Acceptance Tests

```
FT-1  Retrieval across restart   Store a fact, restart server, ask next session → recalled (or failure documented).
FT-2  Meaning not keyword        Query "why does eLo exist?" → returns imagination/healing/connection, not literal string match.
FT-3  [CREATOR] fallback         Remove user_profile.json → eLo still answers with a minimal safe profile.
ST-1  Anti-fabrication           Ask about an event that never happened → eLo does not invent it.
ST-2  Bounded working memory     Overflow working layer → oldest unpinned evicted to summary; pinned survive.
ST-3  Vault-down graceful        obsidian_loader unavailable → turn proceeds on memory_pack, context flagged stale.
IT-1  Memory → CognitiveState    MemoryFaculty context reaches the Executive in the frozen CognitiveState; Ch.5 pins significant turns back into memory.
```

---
**Status: READY FOR REVIEW** — contracts, lifecycle, envelope, and acceptance tests added (WO-003).
