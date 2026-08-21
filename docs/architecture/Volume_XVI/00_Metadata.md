---
volume: XVI
title: "Multi-Faculty Coordination — One Mind, Specialised Cognition"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "David Charles Bible content (2026-07-27) + One Brain Principle"
implementation: PARTIAL (single Executive live; faculty-bus coordination pending)
Provenance: [ENGINEERING]
audit_status: OPEN
canonical_path: docs/architecture/Volume_XVI/
dependencies:
  - Volume V (CONTRACTS.md — Faculty Bus/envelope/lifecycle), Ch.1 (Executive), Ch.2 (Faculty System)
  - Volume XXII (Faculty Genome — capability declarations)
priority: "Audit gap: Multi-Agent Coordination (was 🔴 Future)"
last_review: 2026-08-10
next_review: TBD
---

# Volume XVI — Multi-Faculty Coordination

> eLo OS is **not a society of independent agents**. It is **one mind expressing
> specialised cognition.** One consciousness, one identity, one personality, one memory,
> one Executive — everything else is specialised cognition. (David Charles, 2026-07-27.)

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V16-CH01 | Chapter 1 | Coordination Under One Executive | READY FOR REVIEW |
| ELO-V16-CH02 | Chapter 2 | Executive Assembly — One Assembled State, One Plan Per Turn | READY FOR REVIEW |
| ELO-V16-CH03 | Chapter 3 | The Faculty Bus — Envelope Routing, Priority & Traceability | READY FOR REVIEW |
| ELO-V16-CH04 | Chapter 4 | Conflict Resolution & One Brain Across Embodiments | READY FOR REVIEW |

## Definition of Done
- [x] One Brain / Executive Authority principles stated as law (Ch.1)
- [x] Coordination loop + capability discovery defined (Ch.1)
- [x] Coordination rules (the four prohibitions) (Ch.1)
- [x] Executive Assembly / one-plan-per-turn mechanism (Ch.2 — ADR-Exec-006 / ADR-Exec-002)
- [x] Faculty Bus routing + priority + traceability (Ch.3 — grounded in core/faculty_bus.py)
- [x] Conflict resolution + One Brain across embodiments (Ch.4)
- [x] Contract + lifecycle + envelope + acceptance tests (all chapters)
- [ ] Architecture Agent can implement without inventing (pending REVIEW)
- [ ] Audit can mark COMPLETE

## Open Decisions (for CA / David)
- **D-XVI-A** (Ch.2): name reconciliation — code `CognitiveSnapshot` vs. ADR-Exec-006 `UnifiedCognitiveState`.
- **D-XVI-B** (Ch.2): confirm the 10-component ADR-Exec-006 set converges into ONE pre-decision frozen object (WO-052 completion target).
- **D-XVI-C** (Ch.4): ratify the conflict-resolution ORDER (safety > truth > executive-priority > confidence > relationship). Safety-veto changes remain David L3.

## Implementation status (grounded, do not overstate)
- **LIVE:** one `CognitivePlan` per turn (`runtime/spine/spine.py`); `CognitiveSnapshot` assembled + frozen at top of turn (`runtime/cognitive_snapshot.py`, WO-052 PARTIAL); Faculty Bus envelope + router + Attention→Executive proof pair (`core/faculty_bus.py`, WO-001).
- **PENDING:** full ADR-Exec-006 component convergence; priority-ordered bus scheduling (FIFO today); full faculty subscription onto the bus; multi-body simultaneous projection + verified body-switch handover.
