---
id: WO-003
title: "Finish Volume V — add contracts to the 6 legacy chapters"
status: READY
target_agent: Architecture
priority: P1
owner: ""
depends_on: [decision D-B]      # soft — can draft against CONTRACTS.md now
blocks: [Volume V IMPLEMENTATION READY]
spec_refs:
  - docs/architecture/Volume_V/00_Metadata.md
  - docs/architecture/Volume_V/CONTRACTS.md
  - docs/architecture/Volume_V/01_Cognitive_Core.md   # the depth template
audit_gap: ""
created: 2026-07-27
---

# WO-003 — Finish Volume V (6 legacy chapters)

## 1. Objective
Bring chapters 02, 03, 05, 08, 09, 10 up to the same engineering depth as 01/04/06/07 so
Volume V can clear REVIEW → IMPLEMENTATION READY.

## 2. Why now
This is the **easiest aligned** win: the chapters already exist as concepts; each just
needs the standardized contract block it lacks. It produces the **first
IMPLEMENTATION-READY volume** with no new architecture invention and no code risk.

## 3. Spec references (read first)
- `Volume_V/CONTRACTS.md` — the base faculty contract (§4), universal lifecycle (§3),
  and envelope (§2) each chapter must bind to. **This is fill-in-the-template work.**
- `Volume_V/01_Cognitive_Core.md`, `04`, `06`, `07` — the depth/format to match.
- `Volume_V/00_Metadata.md` — the "Remaining work" table lists exactly the 6 chapters.

## 4. Deliverable
For EACH of chapters 02, 03, 05, 08, 09, 10, append (do not rewrite the existing concept
text — additive):
- a typed **Faculty Contract** (name, version, purpose, contributes_to, inputs, outputs,
  dependencies, failure modes);
- a **Faculty Lifecycle** section binding CONTRACTS.md §3;
- a **Message Envelope** binding (CONTRACTS.md §2);
- **Acceptance tests** (≥ FT×3, ST×3, IT×1);
- update the chapter's status line to READY FOR REVIEW.

## 5. Files to TOUCH
- `docs/architecture/Volume_V/02_Faculty_System.md`
- `.../03_Memory_Architecture.md`
- `.../05_Significance_Engine.md`
- `.../08_Intent_Relationship_Engine.md`
- `.../09_Creative_Imagination_Engine.md`
- `.../10_Agency_Engine.md`
- Then update `00_Metadata.md` build-queue rows + DoD checkboxes.

## 6. Files/things you MUST NOT touch
- Existing concept prose in each chapter (append, don't replace — respect the other
  architect's authored content).
- Any code (this is a canon-only WO).

## 7. Acceptance tests (Definition of Done)
- [ ] All 6 chapters carry a Faculty Contract, lifecycle binding, envelope, and tests.
- [ ] Each chapter's Significance/Memory/Intent/Creative/Agency contract is consistent
      with its live-code counterpart (e.g. Ch.5 aligns with `memory/significance_engine.py`).
- [ ] `00_Metadata.md` shows 10/10 with full contracts; DoD "faculty contract / state
      machine / failure mode / tests" boxes all ticked.
- [ ] No contradiction with CONTRACTS.md or the four runtime contracts.

## 8. Risks / footguns
- Two architects edit `Volume_V/` — coordinate; append rather than overwrite.
- Ch.5's significance formula must match the live engine, not the conceptual draft.

## 9. Handback
Volume V status → REVIEW-clear (all chapters READY FOR REVIEW), ready for David + both
architects to promote to IMPLEMENTATION READY. Note any contract that revealed a
live-code mismatch (feeds a Builder WO).
