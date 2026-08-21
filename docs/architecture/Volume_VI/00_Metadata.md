---
volume: VI
title: "Working Memory & Attention"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "core/attention.py + runtime/working_memory.py (WO-008) + Volume V Ch.1 §4 + Cognitive Plan Architecture"
implementation: PARTIAL (typed WM object + attention competition built in runtime/working_memory.py; imported nowhere — wiring PENDING)
Provenance: [ENGINEERING]
audit_status: OPEN
canonical_path: docs/architecture/Volume_VI/
dependencies:
  - Volume V Ch.1 (working memory in-turn view — reconciled, D-G), Ch.5 (significance → pinning)
  - Volume V/CONTRACTS.md (envelope, lifecycle, base contract)
  - Volume VIII (Long-Term Memory — the boundary WM never crosses)
  - Volume XV (Unified World State — supplies attention candidates), Volume XII (Perception)
priority: "Audit Critical Gap #3 (HIGH)"
last_review: 2026-08-10
next_review: TBD
---

# Volume VI — Working Memory & Attention

The Brain tier's remaining gap. Defines the **typed working-memory object** (current task,
goals, interruptions, attention weights) and **attention as explicit competing weights**
(novelty vs importance vs urgency) — replacing today's untyped `_state` dict.

Addresses **Audit gap #3**: working memory lives in a mutable `_state` dict; attention
competition is implemented in `core/attention.py` but not as explicit competing weights.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V6-CH01 | Chapter 1 | Working Memory & Attention Competition (the typed object) | READY FOR REVIEW |
| ELO-V6-CH02 | Chapter 2 | The Working-Memory Lifecycle — Seed, Update, Evict, Carry | READY FOR REVIEW |
| ELO-V6-CH03 | Chapter 3 | Attention & Salience — One Competition, Not Two Drivers | READY FOR REVIEW |
| ELO-V6-CH04 | Chapter 4 | Wiring Working Memory Into the Turn — Executive · The Moment · Vol VIII / XV boundaries | READY FOR REVIEW |

**Open decisions raised by this volume (for CA / David):**
- **D-VI-1 (Ch.3)** — ratify the WM attention competition as the *single* attention driver and
  re-cast `core/attention.py` as the "Memory Relevance Filter" (supplier), ending the two-attention
  name collision. Blocks Ch.4 wiring.
- Plus per-chapter open questions Q2-a/b/c, Q3-a/b, Q4-a/b/c (INVENTED structure flagged inline).

## Canon reconciliation (REQUIRES DECISION — D-G)

Working memory is touched by Volume V Ch.1 §4 (the in-turn frame buffer). Ownership:
- **Volume VI (this)** = authoritative working-memory + attention volume (the typed object + competition model).
- **Volume V Ch.1 §4** = the cognitive-loop view (bounded frame buffer, pinning). Compatible sub-view.

**D-G RATIFIED (2026-07-27):** the **Executive owns Working Memory** (it is executive
state); the **Memory Faculty owns Long-Term Memory** (knowledge). So the typed
WorkingMemory object defined here is **Executive-owned per-turn state** — the attention
competition (§1.3) computes into it, but the Executive holds it. Long-term store is
Volume VIII. Volume VI remains the authoritative spec for the WM object + attention model;
V Ch.1 §4 is its in-turn view.

## Definition of Done

- [x] Typed WorkingMemory object (task/goals/interruptions/attention weights) — Ch.1
- [x] Attention competition as explicit weights (novelty/importance/urgency) — Ch.1, Ch.3
- [x] WM lifecycle: seed · update · evict · carry, bounded to Vol VIII at the LTM line — Ch.2
- [x] Two-attention reconciliation → one driver (D-VI-1) — Ch.3
- [x] Wiring contract: turn placement · CognitiveState slot · Executive (D-G) · The Moment · Vol VIII/XV boundaries — Ch.4
- [x] Faculty contract + lifecycle + envelope + acceptance tests (per chapter)
- [ ] Architecture Agent can implement without inventing (pending REVIEW + D-VI-1)
- [ ] Audit can mark COMPLETE
