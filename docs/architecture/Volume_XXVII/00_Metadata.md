---
volume: XXVII
title: "Engineering Standards & Canon Governance"
status: REVIEW · Canon (ADR-0003) — 3 chapters READY FOR REVIEW; consolidates engineering/ governance
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles)"
audit_status: OPEN
canonical_path: docs/architecture/Volume_XXVII/
tier: GOVERNANCE (the constitution of the Canon)
last_review: 2026-08-10
---

# Volume XXVII — Engineering Standards & Canon Governance

The constitution of the Canon. Much of this **already exists live** in `engineering/`
and the docs I built this program — this volume formalises and points to them.

## Scope amendment — governance for one person (2026-08-10)

**eLo is David Charles's personal companion; the product / sharing track is PARKED.** This
volume was written in the product era and encoded an organisation that does not exist. Amended
across all three chapters on 2026-08-10 (**not ratified — READY FOR REVIEW**):

**Corrected:**
- **The seats that actually exist** (Ch.3 §3.1): **Builder (eLo OS Python) · Designer (Unity) ·
  Game · Lead Architect (Claude) · Chief Architect (ChatGPT) · Gemini R&D**, with **David as
  sole L3**. The eight-seat table, "Planning Assistants", the Debug seat and the CEO Agent are
  retired (recorded in place, not deleted).
- **David is the single gate.** Software RESERVED collapsed to David as both **L3 and LG-2** on
  2026-08-10. **CA first-pass is advisory, not a gate**, and the CA legislates nothing.
- **`LG-2` is now expressible in this volume at all** — Ch.1 §1.3.1 is new. The audit found
  **zero occurrences of `LG-2`** here, meaning the constitution structurally could not state
  David's own ruling. Software collapses to David; **robot hardware keeps a real second
  review**, which must not be the part's designer, with the force-limiter scope DONE before
  anything is powered near David.
- **The stranger-onboarding bar is retired** (Ch.2 §2.1) and replaced by the bar that describes
  the real failure mode: **survive a compaction** — a seat that lost its context, or David back
  after two weeks, resumes in one session without re-explaining anything.
- **Product-era release framing re-scoped** (Ch.3 §3.8): there is no release audience;
  "release" means David starts living with it, and the trigger is *"David feels it's coherent."*

**Kept, deliberately — this is good discipline and it survives intact:**
Canon vs ADR vs Audit · the Definition of Done (incl. *"the Builder can implement without
inventing anything"*) · the Append Rule and ID immutability · evidence gates ("no DONE until
acceptance tests pass") · FREEZE discipline · Verify-before-claim and the honesty markers ·
the Architect never ratifying its own draft.

**Governance here serves David** — so he can trust the record without re-reading the repo. It
does not exist to demonstrate process to an outside reader.

## Scope (authoritative, from the Bible)
Documentation standards · ADRs · RFC process · versioning · naming conventions · folder
structures · coding standards · testing philosophy · review process · Definition of Done ·
release process · canon governance.

## Already live (this volume formalises, doesn't recreate)
- **Engineering programme & lifecycle:** `engineering/README.md`, `engineering/Volume_1_Framework/`, `engineering/standards/`.
- **ADRs / Decision Log:** `docs/architecture/DECISION_LOG.md` (D-A…G, FC-1/2).
- **Work-order dispatch + roles:** `engineering/work_orders/` (README, board, template).
- **Canon structure & index:** `ARCHITECTURE_BIBLE.md`, `00_CANON_INDEX.md`.
- **Contracts/lifecycle/envelope standard:** `Volume_V/CONTRACTS.md`.
- **Co-working guide:** `CO_WORKING_GUIDE.md`.
- **Freeze discipline:** `FREEZE_V1_LOCK.md`, `VERSIONING.md`.

## Chapter plan (mostly consolidation)
- 01 Canon governance: Canon vs ADR vs Audit; the RFC process; Definition of Done
- 02 Standards: documentation, naming, folder structure, coding, testing
- 03 Release & review process

## Chapter Build Queue

| Ch | Title | Status | Version | Consolidates (points to, does not recreate) |
|----|-------|--------|---------|-----------------------------------------------|
| 01 | Canon Governance — Canon vs ADR vs Audit, the Change Process, the Definition of Done | READY FOR REVIEW | 0.1.0 | `00_CANON_INDEX.md` (DoD + map) · `DECISION_LOG.md` (ADR ledger) · `ARCHITECTURE_AUDIT.md` · `CHANGE_CONTROL.md` (RFC path) · freeze standards |
| 02 | Engineering Standards — Documentation, Naming, Structure, Coding, Testing | READY FOR REVIEW | 0.1.0 | `engineering/standards/{documentation,coding,testing,architecture}.md` · `Volume_V/CONTRACTS.md` · `engineering/README.md` |
| 03 | Release & Review Process — Dispatch, Review Gates, Freeze & Versioning | READY FOR REVIEW | 0.1.0 | `work_orders/{README,CHANGE_CONTROL,COMPLETION_LOG,DISPATCH_BOARD}` · `Volume_1_Framework/{03_review,04_freeze}_standards` · `FREEZE_V1_LOCK.md` · `VERSIONING.md` |

**Status: REVIEW** — three chapters authored to READY FOR REVIEW (2026-08-10), then amended for
personal scope the same day. This volume formalises and points to existing `engineering/` +
canon governance; it does not recreate it. Lowest invention risk of the five. **Advances to
IMPLEMENTATION READY only on David's L3** — *amended 2026-08-10: was "Chief Architect
first-pass → David L3"; the CA gate is retired for software (Ch.1 §1.3.1).* Open questions for
David are collected at the foot of each chapter (§x.8/§x.9); the ones flagged 🔴 are his call,
not the Architect's.
