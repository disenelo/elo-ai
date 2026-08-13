---
volume: XXII
title: "Faculty Genome — The Architectural DNA of eLo"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "David Charles Bible content 2026-07-27 + ARCHITECTURE_BIBLE.md"
implementation: PENDING
audit_status: OPEN
canonical_path: docs/architecture/Volume_XXII/
dependencies:
  - Volume_V/CONTRACTS.md (base contract, envelope, lifecycle)
  - Volume_V/02_Faculty_System.md (the faculty network the genome describes)
  - Volume_XVI/01_Coordination_Under_One_Executive.md (capability advertisement / Executive market)
  - Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md (ADR-Exec-005 constitutional boundary)
  - runtime/capabilities/registry.py + capability.py, runtime/faculty_health.py (live precedent)
priority: "Bible RESEARCH/GOVERNANCE tier"
last_review: 2026-08-10
next_review: TBD
---

# Volume XXII — Faculty Genome

The architectural DNA of eLo: how every faculty is **described** (the genome schema), **versioned**,
and **allowed to evolve safely** — under One Brain → One Identity and the constitutional ceiling of
ADR-Exec-005 (evolution never alters identity, values, truth, the Constitution, or the Executive).

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V22-CH01 | Chapter 1 | Genome Schema, Evolution & Laws (compressed anchor — David's Bible content) | READY FOR REVIEW |
| ELO-V22-CH02 | Chapter 2 | The Genome Schema — the descriptor every faculty carries | READY FOR REVIEW |
| ELO-V22-CH03 | Chapter 3 | Faculty Evolution & the Six Laws | READY FOR REVIEW |
| ELO-V22-CH04 | Chapter 4 | Genome Governance — Registry, Executive & the Constitutional Boundary | READY FOR REVIEW |

Ch.1 remains the at-a-glance anchor (canonicalised from David's Bible content). Ch.2–4 expand its
three pillars to full spec depth: the descriptor (Ch.2), evolution + the six laws (Ch.3), and
governance/registry/Vol XXVIII boundary (Ch.4).

## Definition of Done
- [x] Canonical genome schema (Ch.2, full MUST/SHOULD/MAY field set)
- [x] Evolution/versioning rules + composition + deprecation/succession (Ch.3)
- [x] Six Genome Laws formalised, derivations beyond the bare list flagged (Ch.3 §3.4)
- [x] Genome × Executive (Vol XVI) and × Adaptive Learning (Vol XXVIII / ADR-Exec-005) (Ch.4)
- [x] Live grounding cited (registry.py / capability.py / faculty_health.py); gaps marked PENDING
- [ ] CA/David review of flagged derivations (Ch.3 §3.4) — pending
- [ ] Architecture Agent can implement without inventing (pending REVIEW)
- [ ] Audit can mark COMPLETE
