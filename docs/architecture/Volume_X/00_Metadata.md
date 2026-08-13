---
volume: X
title: "Personality Engine — Unifying eLo's Self-Model & Trait Drift"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "Cognitive Plan Architecture (Personality) + self/elo_self_model.py + memory/personality_drift.py"
implementation: PARTIAL (two systems live but not unified)
audit_status: OPEN
canonical_path: docs/architecture/Volume_X/
dependencies:
  - Volume V Ch.7 (Personality Evolution — AUTHORITATIVE for trait vectors + evolution + validation)
  - Volume V Ch.4 (reads affect baseline), Ch.6 (feeds deltas)
  - Volume XXI (Narrative Identity — the across-time self that reads this volume's slices)
  - ADR-Exec-006 (The Moment / Executive Assembly — self is assembled each turn)
  - Volume V/CONTRACTS.md
priority: "Audit Critical Gap #6 (MEDIUM)"
last_review: 2026-08-10
next_review: TBD
---

# Volume X — Personality Engine

Addresses **Audit gap #6**: `self/elo_self_model.py` (mood, curiosity, satisfaction, inner
events) and `memory/personality_drift.py` (trait drift) are two separate systems that
don't know about each other. This volume **unifies them into one Personality Engine**.

## Scope boundary (no duplication with V Ch.7)

Volume V Ch.7 (Personality Evolution Engine) is **authoritative** for the trait-vector
model, the evolution rules, identity-continuity validation, and versioning. This volume
does NOT restate them. Volume X owns only what Ch.7 does not:

- the **unification plan** for the two live code systems into one faculty (Ch.1);
- eLo's **self-state** — the moment-to-moment inner life that sits *below* the slow trait
  vectors, schematised field-by-field from the live code (Ch.2);
- **drift management vs healthy growth** — turning the live self-applied drift system into a
  validated proposal stream and a read-only drift monitor (Ch.3);
- how personality **composes into The Moment** (ADR-Exec-006) and reconciles with traits
  (V Ch.7) and identity (Vol XXI) without forking (Ch.4).

Volume XXI (Narrative Identity) is authoritative for the across-time self/story; it *reads*
this volume's slices. Volume X is on the style/feeling side of "identity immutable, style
evolves" — never the identity side.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V10-CH01 | Chapter 1 | Self-State + Trait Unification | READY FOR REVIEW |
| ELO-V10-CH02 | Chapter 2 | The Self-State Model | READY FOR REVIEW |
| ELO-V10-CH03 | Chapter 3 | Drift Management vs Healthy Growth | READY FOR REVIEW |
| ELO-V10-CH04 | Chapter 4 | Personality in The Moment | READY FOR REVIEW |

## Definition of Done

- [x] The two live systems mapped and a single unified faculty defined (Ch.1)
- [x] Self-state model schematised field-by-field from live code (Ch.2)
- [x] Interface fast self-state ↔ slow trait vectors (defers to V Ch.7)
- [x] Drift vs growth defined; self-applied drift → validated proposal + monitor (Ch.3)
- [x] Personality composition into The Moment; three-volume seam stated (Ch.4)
- [x] Contract + lifecycle + envelope + tests per chapter
- [ ] Architecture Agent can implement without inventing (pending REVIEW)
- [ ] Chief Architect review of RESERVED decisions (Ch.2 §2.6; Ch.3 §3.6 D-X3-1/2/3)
- [ ] David L3 on the identity-level / values decisions flagged RESERVED
- [ ] Audit can mark COMPLETE (blocked on the above)
