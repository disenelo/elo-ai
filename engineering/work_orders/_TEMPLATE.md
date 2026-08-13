---
id: WO-NNN
title: ""
status: DRAFT            # DRAFT | READY | BLOCKED | IN_PROGRESS | IN_REVIEW | DONE
target_agent: ""         # Builder | UI/Avatar | Architecture
priority: P2             # P0 (drop-everything) | P1 (this cycle) | P2 (next) | P3 (backlog)
owner: ""                # set when claimed
depends_on: []           # [WO-xxx, decision D-x, WP_x]
blocks: []               # [WO-xxx]
spec_refs: []            # canon files this implements
audit_gap: ""            # e.g. "Critical Gap #2" or ""
created: 2026-07-27
---

# WO-NNN — <Title>

## 1. Objective (one sentence)
What this WO delivers, in plain terms.

## 2. Why now
The gap it closes / why it's this priority. Link to Audit or WP.

## 3. Spec references (read these first)
- `docs/architecture/...` — the canon that defines this.
- Contract / envelope / lifecycle sections that apply.

## 4. Deliverable
Exactly what to produce (file(s), function signatures, object).

## 5. Files to TOUCH
- `path/to/file.py` — what changes.

## 6. Files/things you MUST NOT touch
- `runtime/executive.py`, `prompts/` (FREEZE_V1_LOCK)
- **The DISENELO apps in `~/Desktop/Output/` (D-I)** — Builder write-scope is `~/elo-ai/` only.
- <anything else this WO must leave alone>

## 7. Acceptance tests (Definition of Done)
The WO is DONE only when these pass. Copy from the spec chapter's tests where possible.
- [ ] ...
- [ ] Regression: no prior-phase behaviour broken.

## 8. Risks / footguns
From `CO_WORKING_GUIDE.md` where relevant.

## 9. Handback  (follow `COMPLETION_LOG.md` protocol)
On completion: set this WO → `IN_REVIEW` on the board · append a Completion Record to
`COMPLETION_LOG.md` · update the living record (Audit row / deliverable location / propose
an ADR) · attach evidence (diff, test output, screenshot). David reviews → DONE or loop.
