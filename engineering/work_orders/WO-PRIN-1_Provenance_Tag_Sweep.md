---
id: WO-PRIN-1
title: "Provenance-tag sweep across Architecture Bible volumes + faculties"
owner_seat: SEAT-EXE-004 (Lead Architect) / Canon Manager
occupant: Architecture (Claude)
priority: P2
reason: "Operationalise 01_PRINCIPLES.md §7 Validation Philosophy — every canon component labelled by origin so evidence is never confused with intention."
roadmap_tag: canon hygiene
depends_on: []
review_required: L1 → L3
canonical_docs: [docs/architecture/01_PRINCIPLES.md, 00_MANIFESTO.md, 00_CANON_INDEX.md]
risk: none
status: READY
created: 2026-07-29
---

# WO-PRIN-1 — Provenance-tag sweep

## 1. Objective
Tag every Volume (and later, faculty) header in the Architecture Bible with its **origin** per
`01_PRINCIPLES.md §7`: `[SCIENCE]` · `[ENGINEERING]` · `[CREATIVE]` (a component may carry more than one,
listed in order of dominance). So a future editor never mistakes a *chosen value* for an *empirical claim*.

## 2. Exactly what to do
- Add a `Provenance:` line to each Volume's metadata header (and `00_MANIFESTO.md` / `01_PRINCIPLES.md`).
- Guide:
  - `[SCIENCE]` — memory systems, predictive processing, attention, perception, learning, embodiment,
    decision-making (biologically-inspired).
  - `[ENGINEERING]` — cognitive spine, memory hierarchy, contracts/envelope, attention routing, identity
    persistence, capability/faculty structure (system-design decisions).
  - `[CREATIVE]` — eLo's chosen values/personality: curiosity-before-certainty, preservation-before-
    replacement, ethics, the glow/character rules, bounded emergence (`DEC-EMERGENCE`).
- Record the mapping in `00_CANON_INDEX.md` (a Provenance column).
- Pairs with the **Decision Taxonomy** (EA-0 CA-006 Rec 8) — decisions get typed at the same time.

## 3. Acceptance
- [ ] Every Volume header + the two philosophical roots carry a `Provenance:` tag.
- [ ] `00_CANON_INDEX.md` shows the provenance per volume.
- [ ] No content changed — labels only (additive).

## 4. Handback
Diff → `COMPLETION_LOG.md`. Architect self-review (L1) → David L3. Low-risk, additive canon hygiene.
